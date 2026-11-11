import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from emporio.api import create_app
from emporio.payments import TestPayments as SandboxPayments
from emporio.sovereign import verify_opening


def prepared(agent):
    session=agent.store.session()["id"]
    product=agent.commerce.catalog(available_only=True)["products"][0]
    agent.commerce.set_item(session,product["id"],1)
    quote=agent.commerce.checkout(session,"sandbox_quote_request_01","pix")
    p=SandboxPayments(agent.store,agent.commerce,agent.settings.state_dir)
    return p,session,quote


def test_test_wallet_is_isolated_and_confirming_twice_debits_once(agent):
    pay,sid,quote=prepared(agent)
    before=pay.wallet(sid)
    other=agent.store.session()["id"]
    assert pay.wallet(other)["address"]!=before["address"]
    intent=pay.create(sid,quote["id"],"sandbox_intent_key_01")
    assert pay.create(sid,quote["id"],"sandbox_intent_key_01")==intent
    assert pay.create(sid,quote["id"],"sandbox_intent_key_02")["id"]==intent["id"]
    receipt=pay.confirm(sid,intent["id"],"approve")
    assert pay.confirm(sid,intent["id"],"approve")==receipt
    assert pay.wallet(sid)["balance_cents"]==before["balance_cents"]-quote["subtotal_cents"]
    assert receipt["seal_verified"] and receipt["funds_moved"] is False
    assert receipt["status"]=="paid_test" and verify_opening(receipt["sovereign_opening"])
    assert receipt["sovereign_opening"]["network_finalized"] is False
    assert all(isinstance(a,str) for a in receipt["sovereign_opening"]["args"])
    with pytest.raises(ValueError):pay.confirm(sid,intent["id"],"decline")


def test_decline_keeps_balance_and_is_terminal(agent):
    pay,sid,quote=prepared(agent)
    before=pay.wallet(sid)["balance_cents"]
    intent=pay.create(sid,quote["id"],"sandbox_decline_key01")
    assert pay.confirm(sid,intent["id"],"decline")["status"]=="declined_test"
    assert pay.wallet(sid)["balance_cents"]==before
    with pytest.raises(ValueError):pay.confirm(sid,intent["id"],"approve")


def test_concurrent_confirmations_debit_once_and_a_key_cannot_switch_quotes(agent):
    from concurrent.futures import ThreadPoolExecutor
    pay,sid,quote=prepared(agent)
    before=pay.wallet(sid)["balance_cents"]
    intent=pay.create(sid,quote["id"],"concurrent_intent_01")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:pay.confirm(sid,intent["id"],"approve"),range(2)))
    assert results[0]==results[1]
    assert pay.wallet(sid)["balance_cents"]==before-quote["subtotal_cents"]
    second=agent.commerce.checkout(sid,"second_checkout_key1","pix")
    with pytest.raises(ValueError,match="another checkout"):
        pay.create(sid,second["id"],"concurrent_intent_01")


def test_cannot_spend_from_another_session_or_an_expired_quote(agent):
    pay,sid,quote=prepared(agent)
    other=agent.store.session()["id"]
    with pytest.raises(ValueError):pay.create(other,quote["id"],"sandbox_foreign_key1")
    intent=pay.create(sid,quote["id"],"sandbox_expiry_key01")
    with pytest.raises(ValueError):pay.confirm(other,intent["id"],"approve")
    with agent.store.connect() as db:
        db.execute("UPDATE music_checkout SET expires=? WHERE id=?",((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),quote["id"]))
    with pytest.raises(ValueError,match="expired"):pay.confirm(sid,intent["id"],"approve")


def test_sandbox_refuses_legacy_pricing_snapshots(agent):
    pay,sid,quote=prepared(agent)
    quote.pop("pricing_policy")
    with agent.store.connect() as db:db.execute("UPDATE music_checkout SET snapshot=? WHERE id=?",(json.dumps(quote),quote["id"]))
    with pytest.raises(ValueError,match="older pricing"):
        pay.create(sid,quote["id"],"old_policy_intent_01")


@pytest.mark.parametrize("tamper",["receipt","amount","opening","missing_receipt"])
def test_tampered_receipt_bindings_are_rejected(agent,tamper):
    pay,sid,quote=prepared(agent)
    intent=pay.create(sid,quote["id"],"tamper_sandbox_key01")
    receipt=pay.confirm(sid,intent["id"],"approve")
    with agent.store.connect() as db:
        if tamper=="receipt":db.execute("UPDATE konaet_test_intents SET receipt='{}' WHERE id=?",(intent["id"],))
        elif tamper=="amount":db.execute("UPDATE konaet_test_intents SET amount_cents=1 WHERE id=?",(intent["id"],))
        elif tamper=="missing_receipt":db.execute("UPDATE konaet_test_intents SET receipt=NULL WHERE id=?",(intent["id"],))
        else:
            changed=receipt["sovereign_opening"];changed["args"][0]="1"
            db.execute("UPDATE konaet_test_intents SET opening=? WHERE id=?",(json.dumps(changed),intent["id"]))
    with pytest.raises(ValueError):pay.get(sid,intent["id"])


def test_insufficient_credits_and_session_reset(agent):
    pay,sid,quote=prepared(agent)
    intent=pay.create(sid,quote["id"],"balance_sandbox_key1")
    with agent.store.connect() as db:db.execute("INSERT INTO konaet_test_wallets VALUES(?,?,0)",(sid,"KNT_TEST_zero"))
    with pytest.raises(ValueError,match="Not enough"):pay.confirm(sid,intent["id"],"approve")
    pay.wallet(sid,topup=True)
    assert pay.confirm(sid,intent["id"],"approve")["seal_verified"]
    agent.store.forget_session(sid)
    with pytest.raises(ValueError):pay.get(sid,intent["id"])
    with pytest.raises(ValueError):pay.wallet(sid)


def test_http_flow_never_accepts_a_forged_total_or_uses_a_foreign_quote(settings):
    app=create_app(settings)
    with TestClient(app) as c:
        assert c.get("/api/sandbox/wallet").status_code==401
        c.get("/api/session")
        product=c.get("/api/shop?available_only=true").json()["products"][0]
        c.put("/api/cart",json={"product_id":product["id"],"quantity":1})
        quote=c.post("/api/checkout",json={"request_key":"api_quote_sandbox_01","method":"pix"}).json()
        assert c.post("/api/sandbox/intents",json={"checkout_id":quote["id"],"request_key":"api_intent_sandbox_01","amount_cents":1}).status_code==422
        intent=c.post("/api/sandbox/intents",json={"checkout_id":quote["id"],"request_key":"api_intent_sandbox_01"}).json()
        r=c.post("/api/sandbox/intents/"+intent["id"]+"/confirm",json={"decision":"approve"})
        assert r.status_code==200 and r.json()["funds_moved"] is False
        assert c.get("/api/sandbox/intents/"+intent["id"]).json()["seal_verified"]
        assert c.delete("/api/session").status_code==200
        assert c.get("/api/sandbox/intents/"+intent["id"]).status_code==404
