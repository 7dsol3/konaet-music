from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

import pytest
from fastapi.testclient import TestClient

from emporio.api import create_app


def test_public_shop_filters_and_comparison(agent):
    shop = agent.commerce.catalog(category_id=5, max_price_brl="1000", available_only=True, sort="price_asc")
    assert shop["products"]
    assert all(p["category_id"] == 5 and p["available"] and p["sale_cents"] <= 100000 for p in shop["products"])
    assert [p["sale_cents"] for p in shop["products"]] == sorted(p["sale_cents"] for p in shop["products"])
    ids = [p["id"] for p in shop["products"][:2]]
    result = agent.commerce.compare(ids)
    assert [p["id"] for p in result["products"]] == ids
    assert "Missing specifications are not inferred" in result["notice"]
    with pytest.raises(ValueError):
        agent.commerce.compare([ids[0], ids[0]])


def test_cart_is_session_scoped_and_clears_on_forget(agent):
    one, two = agent.store.session(), agent.store.session()
    p = agent.commerce.catalog(available_only=True)["products"][0]
    agent.commerce.set_item(one["id"], p["id"], 1)
    assert agent.commerce.cart(one["id"])["quantity"] == 1
    assert agent.commerce.cart(two["id"])["quantity"] == 0
    agent.store.forget_session(one["id"])
    assert agent.commerce.cart(one["id"])["quantity"] == 0


def test_cart_rejects_unavailable_and_out_of_stock_quantities(agent):
    session = agent.store.session()
    all_products = agent.commerce.catalog()["products"]
    unavailable = next(p for p in all_products if not p["available"])
    with pytest.raises(ValueError):
        agent.commerce.set_item(session["id"], unavailable["id"], 1)
    p = next(p for p in all_products if p["available"])
    with pytest.raises(ValueError):
        agent.commerce.set_item(session["id"], p["id"], max(p["stock"] + 1, 21))
    with pytest.raises(ValueError):
        agent.commerce.set_item(session["id"], p["id"], True)


def test_quote_is_unique_idempotent_and_bound_to_cart(agent):
    session = agent.store.session()
    p = agent.commerce.catalog(available_only=True)["products"][0]
    agent.commerce.set_item(session["id"], p["id"], 1)
    first = agent.commerce.checkout(session["id"], "request_key_000001", "pix")
    again = agent.commerce.checkout(session["id"], "request_key_000001", "pix")
    second = agent.commerce.checkout(session["id"], "request_key_000002", "pix")
    assert first == again and first["id"] != second["id"]
    assert first["demo"] and first["payment_status"] == "not_started"
    assert len(first["id"]) == 32
    assert (datetime.fromisoformat(first["expires_at"]) - datetime.fromisoformat(first["created_at"])).total_seconds() == 900
    agent.commerce.set_item(session["id"], p["id"], 0)
    with pytest.raises(ValueError):
        agent.commerce.checkout(session["id"], "request_key_000001", "pix")


def test_quote_totals_use_catalog_and_pix_never_stacks(agent):
    products = agent.commerce.catalog(available_only=True)["products"]
    for p in (next(p for p in products if p["discount_percent"]), next(p for p in products if not p["discount_percent"])):
        session = agent.store.session()
        agent.commerce.set_item(session["id"], p["id"], 1)
        q = agent.commerce.checkout(session["id"], "stable_request_key_1", "pix")
        discount = p["discount_percent"] or 5
        expected = int((Decimal(p["price_cents"]) * (100-discount) / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        assert q["subtotal_cents"] == expected
        assert q["items"][0]["discount_percent"] == discount


def test_quote_expires_and_contains_no_session_or_customer_identity(agent):
    session = agent.store.session()
    p = agent.commerce.catalog(available_only=True)["products"][0]
    agent.commerce.set_item(session["id"], p["id"], 1)
    q = agent.commerce.checkout(session["id"], "quote_expiry_000001", "card")
    assert "session_id" not in q and "customer_id" not in q and "email" not in q
    with agent.store.connect() as db:
        db.execute("UPDATE music_checkout SET expires=? WHERE id=?", ((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(), q["id"]))
    with pytest.raises(ValueError, match="expired"):
        agent.commerce.get_checkout(q["id"])


def test_full_http_shop_cart_quote_svg_reset(settings):
    with TestClient(create_app(settings)) as c:
        products = c.get("/api/shop?category_id=5&max_price_brl=1000&available_only=true").json()["products"]
        assert products
        assert c.put("/api/cart", json={"product_id": products[0]["id"], "quantity": 1}).json()["quantity"] == 1
        response = c.post("/api/checkout", json={"request_key": "http_checkout_test_0001", "method": "pix"})
        assert response.status_code == 200
        q = response.json()
        assert c.get("/api/checkout/"+q["id"]).json() == q
        code = c.get("/api/checkout/"+q["id"]+"/code.svg")
        assert code.status_code == 200 and "image/svg+xml" in code.headers["content-type"]
        assert "KONAET" in code.text and "not a payment confirmation" in code.text
        assert c.get("/checkout/"+q["id"]).status_code == 200
        assert c.post("/api/checkout", json={"request_key": "forged_total_0000001", "method": "pix", "total_cents": 1}).status_code == 422
        assert c.put("/api/cart", json={"product_id": products[0]["id"], "quantity": 1, "session_id": "other"}).status_code == 422
        assert c.put("/api/cart", headers={"Origin": "https://evil.example"}, json={"product_id": products[0]["id"], "quantity": 1}).status_code == 403
        assert c.delete("/api/session").status_code == 200
        assert c.get("/api/cart").json()["quantity"] == 0


@pytest.mark.parametrize("bad", ["x", "../../private", "a"*33, "a"*31])
def test_arbitrary_checkout_references_are_rejected(agent, bad):
    with pytest.raises(ValueError):
        agent.commerce.get_checkout(bad)
