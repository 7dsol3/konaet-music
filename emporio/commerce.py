"""Session-scoped carts and immutable, expiring checkout quotes.

The model never chooses a total or marks a payment paid. Demo quotes do not
reserve inventory. A real provider adapter must recheck stock before payment.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlsplit

from .config import Settings
from .storage import Store, canonical
from .tools import Tools

CATEGORIES = {1: "Electric guitars", 2: "Bass guitars", 3: "Drums & percussion", 4: "Keys & pianos",
              5: "Acoustic guitars", 6: "Woodwinds", 7: "Brass", 8: "Orchestral strings", 9: "Ukuleles"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS music_cart (
 session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 20),
 PRIMARY KEY(session_id,product_id));
CREATE TABLE IF NOT EXISTS music_checkout (
 id TEXT PRIMARY KEY, session_sha256 TEXT NOT NULL, request_key TEXT NOT NULL,
 cart_hash TEXT NOT NULL, created TEXT NOT NULL, expires TEXT NOT NULL, snapshot TEXT NOT NULL,
 UNIQUE(session_sha256,request_key));
"""


def display_product(product: dict) -> dict:
    p = dict(product)
    p["category"] = CATEGORIES[p["category_id"]]
    p["name"] = re.sub(r"^(?:Violão|Guitarra|Baixo|Bateria|Teclado|Piano|Ukulele|Violino|Flauta|Saxofone|Trompete)\s+", "", p["name"], flags=re.I)
    return p


class Commerce:
    def __init__(self, store: Store, tools: Tools, settings: Settings):
        self.store, self.tools, self.settings = store, tools, settings
        parsed = urlsplit(settings.public_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.path not in {"", "/"}
                or parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}):
            raise ValueError("KONAET_PUBLIC_URL must be an HTTPS origin, or HTTP loopback")
        self.origin = settings.public_url.rstrip("/")
        with store.connect() as db:
            db.executescript(SCHEMA)

    def catalog(self, query="", category_id=None, max_price_brl=None, available_only=False, sort="featured") -> dict:
        # The same query/discount implementation as the agent. Public browsing
        # can show all 65 fixtures; model tool output remains capped at eight.
        result = self.tools.search_products(query=query, category_id=category_id,
                                            max_price_brl=max_price_brl, available_only=available_only, limit=200)
        products = [display_product(p) for p in result["products"]]
        if sort == "price_desc":
            products.sort(key=lambda p: (-p["sale_cents"], p["id"]))
        elif sort == "name":
            products.sort(key=lambda p: p["name"].casefold())
        elif sort == "featured":
            products.sort(key=lambda p: (not p["available"], -p["discount_percent"], p["sale_cents"], p["id"]))
        elif sort != "price_asc":
            raise ValueError("Invalid catalog sort")
        return {"products": products, "total_matches": len(products), "currency": "BRL", "snapshot": result["snapshot"]}

    def product(self, product_id: int) -> dict:
        result = self.tools.get_product(product_id)
        if not result["products"]:
            raise ValueError("Product not found")
        return display_product(result["products"][0])

    def compare(self, ids: list[int]) -> dict:
        if not 2 <= len(ids) <= 3 or len(set(ids)) != len(ids):
            raise ValueError("Choose two or three different instruments")
        products = [self.product(i) for i in ids]
        return {"products": products, "spec_keys": sorted(set().union(*(p["specs"] for p in products))),
                "notice": "Recorded catalog specifications. Missing specifications are not inferred."}

    def cart(self, session_id: str) -> dict:
        with self.store.connect() as db:
            rows = db.execute("SELECT product_id,quantity FROM music_cart WHERE session_id=? ORDER BY product_id", (session_id,)).fetchall()
        items = []
        for row in rows:
            p = self.product(row["product_id"])
            total = p["sale_cents"] * row["quantity"]
            items.append({"product": p, "quantity": row["quantity"], "line_total_cents": total,
                          "available": p["available"] and p["stock"] >= row["quantity"]})
        return {"items": items, "quantity": sum(i["quantity"] for i in items),
                "subtotal_cents": sum(i["line_total_cents"] for i in items), "currency": "BRL",
                "checkout_available": bool(items) and all(i["available"] for i in items),
                "notice": "Prices are rechecked. Adding an item does not reserve stock."}

    def set_item(self, session_id: str, product_id: int, quantity: int) -> dict:
        if type(product_id) is not int or type(quantity) is not int or not 0 <= quantity <= 20:
            raise ValueError("Choose a quantity between zero and twenty")
        p = self.product(product_id)
        if quantity and (not p["available"] or quantity > p["stock"]):
            raise ValueError("This quantity is not available in the recorded catalog")
        with self.store.connect() as db:
            if quantity:
                count = db.execute("SELECT COUNT(*) FROM music_cart WHERE session_id=?", (session_id,)).fetchone()[0]
                existing = db.execute("SELECT 1 FROM music_cart WHERE session_id=? AND product_id=?", (session_id, product_id)).fetchone()
                if count >= 12 and not existing:
                    raise ValueError("A cart can hold up to twelve different instruments")
                db.execute("INSERT INTO music_cart VALUES(?,?,?) ON CONFLICT(session_id,product_id) DO UPDATE SET quantity=excluded.quantity",
                           (session_id, product_id, quantity))
            else:
                db.execute("DELETE FROM music_cart WHERE session_id=? AND product_id=?", (session_id, product_id))
        return self.cart(session_id)

    def checkout(self, session_id: str, request_key: str, method: str) -> dict:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{16,80}", request_key) or method not in {"pix", "card"}:
            raise ValueError("Invalid checkout request")
        cart = self.cart(session_id)
        if not cart["checkout_available"]:
            raise ValueError("Your cart is empty or contains unavailable quantities")
        session_hash = hashlib.sha256(session_id.encode()).hexdigest()
        items = []
        for i in cart["items"]:
            p, qty = i["product"], i["quantity"]
            discount = p["discount_percent"] or (5 if method == "pix" else 0)
            unit = int((Decimal(p["price_cents"]) * (100 - discount) / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
            total = unit * qty
            items.append({"product_id": p["id"], "name": p["name"], "quantity": qty,
                          "list_total_cents": p["price_cents"] * qty, "discount_percent": discount,
                          "unit_total_cents": unit, "line_total_cents": total, "promotion_applied": bool(p["discount_percent"])})
        cart_hash = hashlib.sha256(canonical({"items": items, "method": method}).encode()).hexdigest()
        current = datetime.now(timezone.utc)
        with self.store.connect() as db:
            db.execute("DELETE FROM music_checkout WHERE expires < ?", ((current-timedelta(days=1)).isoformat(),))
            existing = db.execute("SELECT * FROM music_checkout WHERE session_sha256=? AND request_key=?", (session_hash, request_key)).fetchone()
            if existing:
                if existing["cart_hash"] != cart_hash:
                    raise ValueError("The cart changed. Start a new checkout")
                return self.get_checkout(existing["id"])
            checkout_id = secrets.token_urlsafe(24)
            snapshot = {"id": checkout_id, "items": items, "method": method, "currency": "BRL",
                        "schema": "konaet.quote.v2", "pricing_policy": "unit_round_v1",
                        "subtotal_cents": sum(i["line_total_cents"] for i in items),
                        "created_at": current.isoformat(), "expires_at": (current+timedelta(minutes=15)).isoformat(),
                        "status": "quote", "payment_status": "not_started", "demo": True,
                        "shipping": "Not included. Confirm fulfillment with the store before payment.",
                        "checkout_url": self.origin + "/checkout/" + checkout_id}
            db.execute("INSERT INTO music_checkout VALUES(?,?,?,?,?,?,?)", (checkout_id, session_hash, request_key, cart_hash,
                       snapshot["created_at"], snapshot["expires_at"], canonical(snapshot)))
        self.store.audit(session_id, "prepare_checkout", ["product:"+str(i["product_id"]) for i in items], "quote_only")
        return snapshot

    def get_checkout(self, checkout_id: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{32}", checkout_id):
            raise ValueError("Checkout not found")
        with self.store.connect() as db:
            row = db.execute("SELECT snapshot,expires FROM music_checkout WHERE id=?", (checkout_id,)).fetchone()
        if not row:
            raise ValueError("Checkout not found")
        if datetime.fromisoformat(row["expires"]) <= datetime.now(timezone.utc):
            raise ValueError("This checkout has expired. Create a new quote")
        return json.loads(row["snapshot"])
