from __future__ import annotations

import csv
import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def cents(value: str | int | float) -> int:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary value") from exc
    if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000"):
        raise ValueError("Money must be finite and between zero and one billion BRL")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def now() -> datetime:
    return datetime.now(timezone.utc)


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS products(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, category_id INTEGER REFERENCES categories(id),
 price_cents INTEGER NOT NULL CHECK(price_cents>=0), description TEXT NOT NULL,
 stock INTEGER NOT NULL CHECK(stock>=0), status TEXT NOT NULL,
 specs TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY, email TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders(
 id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id),
 order_date TEXT NOT NULL, status TEXT NOT NULL, total_cents INTEGER NOT NULL,
 payment_method TEXT NOT NULL, tracking_code TEXT, estimated_delivery TEXT);
CREATE TABLE IF NOT EXISTS order_items(
 order_id INTEGER REFERENCES orders(id), product_id INTEGER REFERENCES products(id),
 quantity INTEGER NOT NULL CHECK(quantity>0), PRIMARY KEY(order_id,product_id));
CREATE TABLE IF NOT EXISTS promotions(
 id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id),
 discount_percent INTEGER CHECK(discount_percent BETWEEN 1 AND 100),
 description TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)));
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(
 id TEXT PRIMARY KEY, expires TEXT NOT NULL, customer_id INTEGER,
 history TEXT NOT NULL DEFAULT '[]', context TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS audit(
 seq INTEGER PRIMARY KEY, previous TEXT NOT NULL, payload TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS orders_owner ON orders(customer_id);
"""


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def import_data(self, directory: Path) -> dict:
        paths = sorted(Path(directory).glob("*.csv"))
        expected = {"categories", "customers", "products", "orders", "order_items", "promotions"}
        source = {p.stem.split(" - ")[-1]: p for p in paths}
        if set(source) != expected:
            raise ValueError("Expected the six original case CSV tables")
        manifest = {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in source.items()}
        fingerprint = hashlib.sha256(canonical(manifest).encode()).hexdigest()
        with self.connect() as db:
            row = db.execute("SELECT value FROM metadata WHERE key='data_hash'").fetchone()
            if row and row[0] == fingerprint:
                return json.loads(db.execute("SELECT value FROM metadata WHERE key='report'").fetchone()[0])
        tables = {}
        for name, path in source.items():
            with path.open(encoding="utf-8-sig", newline="") as stream:
                tables[name] = list(csv.DictReader(stream))
        warnings = []
        with self.connect() as db:
            # Replacement is transactional; a malformed fixture never leaves a partial catalog.
            # A changed dataset cannot inherit verification from reused customer IDs.
            db.execute("DELETE FROM sessions")
            for table in ("order_items", "promotions", "orders", "products", "customers", "categories"):
                db.execute(f"DELETE FROM {table}")  # Internal fixed identifiers, never user input.
            db.executemany("INSERT INTO categories VALUES(?,?)",
                           [(int(r["category_id"]), r["name"]) for r in tables["categories"]])
            db.executemany("INSERT INTO customers VALUES(?,?)",
                           [(int(r["customer_id"]), r["email"].strip().casefold()) for r in tables["customers"]])
            for r in tables["products"]:
                if r["status"] not in {"active", "discontinued", "coming_soon"}:
                    raise ValueError("Unknown product status")
                specs = json.loads(r["specs"])
                if not isinstance(specs, dict):
                    raise ValueError("Product specs must be an object")
                db.execute("INSERT INTO products VALUES(?,?,?,?,?,?,?,?,?)", (
                    int(r["product_id"]), r["name"], int(r["category_id"]), cents(r["price_brl"]),
                    r["description"], int(r["stock_quantity"]), r["status"], canonical(specs), r["created_at"]))
            for r in tables["orders"]:
                if r["status"] not in {"pending", "confirmed", "shipped", "delivered", "cancelled"}:
                    raise ValueError("Unknown order status")
                db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?)", (
                    int(r["order_id"]), int(r["customer_id"]), r["order_date"], r["status"],
                    cents(r["total_brl"]), r["payment_method"], r["tracking_code"] or None,
                    r["estimated_delivery"] or None))
            db.executemany("INSERT INTO order_items VALUES(?,?,?)", [
                (int(r["order_id"]), int(r["product_id"]), int(r["quantity"])) for r in tables["order_items"]])
            db.executemany("INSERT INTO promotions VALUES(?,?,?,?,?)", [
                (int(r["promotion_id"]), int(r["product_id"]), int(r["discount_percent"]),
                 r["description"], int(r["is_active"])) for r in tables["promotions"]])
            mismatches = db.execute("""SELECT o.id FROM orders o JOIN order_items i ON i.order_id=o.id
                JOIN products p ON p.id=i.product_id GROUP BY o.id
                HAVING o.total_cents != SUM(p.price_cents*i.quantity)""").fetchall()
            if mismatches:
                warnings.append({"code": "historical_total_differs", "orders": [r[0] for r in mismatches],
                                 "action": "Keep recorded order totals; current catalog prices are not historical prices."})
            report = {"counts": {k: len(v) for k, v in tables.items()}, "source_sha256": manifest,
                      "warnings": warnings, "fingerprint": fingerprint}
            for key, value in (("data_hash", fingerprint), ("report", canonical(report))):
                db.execute("INSERT OR REPLACE INTO metadata VALUES(?,?)", (key, value))
        return report

    def session(self, session_id: str | None = None) -> dict:
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE expires < ?", (now().isoformat(),))
            row = db.execute("SELECT * FROM sessions WHERE id=?", (session_id or "",)).fetchone()
            if row:
                value = dict(row)
                value["history"] = json.loads(value["history"])
                value["context"] = json.loads(value["context"])
                return value
            session_id = secrets.token_urlsafe(32)
            expires = (now() + timedelta(hours=24)).isoformat()
            db.execute("INSERT INTO sessions(id,expires) VALUES(?,?)", (session_id, expires))
        return {"id": session_id, "expires": expires, "customer_id": None, "history": [], "context": {}}

    def save_session(self, session: dict) -> None:
        with self.connect() as db:
            db.execute("UPDATE sessions SET customer_id=?,history=?,context=? WHERE id=?",
                       (session["customer_id"], canonical_list(session["history"][-24:]),
                        canonical(session["context"]), session["id"]))

    def forget_session(self, session_id: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE id=?", (session_id,))

    def verify_order(self, session: dict, order_id: int, email: str) -> bool:
        with self.connect() as db:
            row = db.execute("SELECT c.id,c.email FROM customers c JOIN orders o ON o.customer_id=c.id WHERE o.id=?",
                             (order_id,)).fetchone()
        # Same public result for unknown order and mismatched identity.
        valid = bool(row and secrets.compare_digest(row["email"].encode(), email.strip().casefold().encode()))
        session["customer_id"] = row["id"] if valid else None
        self.save_session(session)
        return valid

    def audit(self, session_id: str, action: str, sources: list[str], outcome: str) -> str:
        payload = canonical({"time": now().isoformat(), "session_sha256": hashlib.sha256(session_id.encode()).hexdigest(),
                             "action": action, "sources": sources, "outcome": outcome})
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            last = db.execute("SELECT seq,hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            seq, previous = (last[0] + 1, last[1]) if last else (1, "0" * 64)
            digest = hashlib.sha256(f"{seq}\n{previous}\n{payload}".encode()).hexdigest()
            db.execute("INSERT INTO audit VALUES(?,?,?,?)", (seq, previous, payload, digest))
        return digest

    def verify_audit(self) -> dict:
        previous = "0" * 64
        with self.connect() as db:
            rows = db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
        for expected, row in enumerate(rows, 1):
            digest = hashlib.sha256(f"{expected}\n{previous}\n{row['payload']}".encode()).hexdigest()
            if row["seq"] != expected or row["previous"] != previous or row["hash"] != digest:
                return {"valid": False, "records": len(rows), "first_error": expected}
            previous = digest
        return {"valid": True, "records": len(rows), "head": previous}


def canonical_list(value: list) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
