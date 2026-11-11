"""KONAET checkout state machine. Test transactions only; no banking connection."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timezone

from .storage import canonical
from .sovereign import opening, verify_opening

SCHEMA = """
CREATE TABLE IF NOT EXISTS konaet_test_intents(
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 checkout_id TEXT NOT NULL UNIQUE, request_key TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents>=0),
 status TEXT NOT NULL CHECK(status IN ('pending_test','paid_test','declined_test')),
 created TEXT NOT NULL, receipt TEXT, mac TEXT, opening TEXT, UNIQUE(session_id,request_key));
CREATE TABLE IF NOT EXISTS konaet_test_wallets(
 session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
 address TEXT NOT NULL UNIQUE, balance_cents INTEGER NOT NULL CHECK(balance_cents>=0));
"""


class TestPayments:
    def __init__(self, store, commerce, state_dir):
        self.store, self.commerce = store, commerce
        key_path = state_dir / "test-receipt-seal.key"
        try:
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(secrets.token_bytes(32))
        self.key = key_path.read_bytes()
        if len(self.key) != 32:
            raise ValueError("The local test receipt seal is invalid; do not replace existing keys silently")
        self.key_id = hashlib.sha256(self.key).hexdigest()[:16]
        with store.connect() as db:
            db.executescript(SCHEMA)
            if "opening" not in {r[1] for r in db.execute("PRAGMA table_info(konaet_test_intents)")}:
                db.execute("ALTER TABLE konaet_test_intents ADD COLUMN opening TEXT")

    def _ensure_session(self, db, session_id):
        if not db.execute("SELECT id FROM sessions WHERE id=? AND expires>?", (session_id, datetime.now(timezone.utc).isoformat())).fetchone():
            raise ValueError("This test workspace session has expired")

    def _owned_quote(self, db, session_id, checkout_id, *, require_active=True):
        if not re.fullmatch(r"[A-Za-z0-9_-]{32}", checkout_id):
            raise ValueError("Test checkout not found for this session")
        row = db.execute("SELECT * FROM music_checkout WHERE id=? AND session_sha256=?",
                         (checkout_id, hashlib.sha256(session_id.encode()).hexdigest())).fetchone()
        if not row:
            raise ValueError("Test checkout not found for this session")
        if require_active and datetime.fromisoformat(row["expires"]) <= datetime.now(timezone.utc):
            raise ValueError("The quote expired. Prepare a new checkout")
        quote = json.loads(row["snapshot"])
        if quote.get("demo") is not True or quote.get("currency") != "BRL":
            raise ValueError("Only BRL demonstration quotes are supported")
        if quote.get("pricing_policy") != "unit_round_v1":
            raise ValueError("This quote uses an older pricing rule. Prepare a new checkout")
        return quote

    def _wallet(self, db, session_id):
        row = db.execute("SELECT * FROM konaet_test_wallets WHERE session_id=?", (session_id,)).fetchone()
        if not row:
            db.execute("INSERT INTO konaet_test_wallets VALUES(?,?,1000000)", (session_id, "KNT_TEST_" + secrets.token_hex(10)))
            row = db.execute("SELECT * FROM konaet_test_wallets WHERE session_id=?", (session_id,)).fetchone()
        return row

    def wallet(self, session_id, topup=False):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._ensure_session(db, session_id)
            wallet = self._wallet(db, session_id)
            if topup:
                if wallet["balance_cents"] > 99_000_000:
                    raise ValueError("The test wallet balance limit was reached")
                db.execute("UPDATE konaet_test_wallets SET balance_cents=balance_cents+1000000 WHERE session_id=?", (session_id,))
                wallet = self._wallet(db, session_id)
            recent = db.execute("SELECT id,status,amount_cents,created FROM konaet_test_intents WHERE session_id=? ORDER BY created DESC LIMIT 8", (session_id,)).fetchall()
            return {"address": wallet["address"], "balance_cents": wallet["balance_cents"], "unit": "test BRL",
                    "demo": True, "funds_moved": False, "transactions": [dict(r) for r in recent],
                    "notice": "Sandbox credits only. No cash value, bank account, crypto assets or real deposits."}

    def create(self, session_id, checkout_id, request_key):
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", request_key):
            raise ValueError("Use a valid test request key")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._ensure_session(db, session_id)
            quote = self._owned_quote(db, session_id, checkout_id)
            previous = db.execute("SELECT * FROM konaet_test_intents WHERE session_id=? AND request_key=?", (session_id, request_key)).fetchone()
            if previous and previous["checkout_id"] != checkout_id:
                raise ValueError("This request key belongs to another checkout")
            previous = previous or db.execute("SELECT * FROM konaet_test_intents WHERE checkout_id=?", (checkout_id,)).fetchone()
            if previous:
                if previous["session_id"] != session_id:
                    raise ValueError("Test checkout not found for this session")
                return self._view(previous)
            intent_id = secrets.token_urlsafe(24)
            db.execute("INSERT INTO konaet_test_intents(id,session_id,checkout_id,request_key,amount_cents,status,created) VALUES(?,?,?,?,?,'pending_test',?)",
                       (intent_id, session_id, checkout_id, request_key, quote["subtotal_cents"], datetime.now(timezone.utc).isoformat()))
            return self._view(db.execute("SELECT * FROM konaet_test_intents WHERE id=?", (intent_id,)).fetchone())

    def confirm(self, session_id, intent_id, decision):
        if decision not in {"approve", "decline"} or not re.fullmatch(r"[A-Za-z0-9_-]{32}", intent_id):
            raise ValueError("Invalid test transaction")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._ensure_session(db, session_id)
            row = db.execute("SELECT * FROM konaet_test_intents WHERE id=? AND session_id=?", (intent_id, session_id)).fetchone()
            if not row:
                raise ValueError("Test transaction not found for this session")
            target = "paid_test" if decision == "approve" else "declined_test"
            if row["status"] != "pending_test":
                if row["status"] != target:
                    raise ValueError("The completed test transaction cannot change outcome")
                return self._view(row)
            quote = self._owned_quote(db, session_id, row["checkout_id"])
            if quote["subtotal_cents"] != row["amount_cents"]:
                raise ValueError("The test transaction amount does not match its quote")
            wallet = self._wallet(db, session_id)
            if decision == "approve":
                if wallet["balance_cents"] < row["amount_cents"]:
                    raise ValueError("Not enough sandbox credits. Add test credits in your test wallet.")
                db.execute("UPDATE konaet_test_wallets SET balance_cents=balance_cents-? WHERE session_id=?", (row["amount_cents"], session_id))
            wallet = self._wallet(db, session_id)
            receipt = {"schema": "konaet.test-receipt.v1", "id": row["id"], "checkout_id": row["checkout_id"],
                       "amount_cents": row["amount_cents"], "currency": "BRL", "status": target,
                       "created_at": datetime.now(timezone.utc).isoformat(), "demo": True, "funds_moved": False,
                       "provider": "KONAET Sandbox", "seal_key_id": self.key_id,
                       "test_wallet": wallet["address"], "test_balance_after_cents": wallet["balance_cents"],
                       "notice": "TEST RECEIPT. No money moved, no bank settlement and no stock reservation."}
            serialized = canonical(receipt)
            mac = hmac.new(self.key, serialized.encode(), hashlib.sha256).hexdigest()
            bridge = canonical(opening(receipt, mac))
            db.execute("UPDATE konaet_test_intents SET status=?,receipt=?,mac=?,opening=? WHERE id=?", (target, serialized, mac, bridge, intent_id))
            return self._view(db.execute("SELECT * FROM konaet_test_intents WHERE id=?", (intent_id,)).fetchone())

    def get(self, session_id, intent_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{32}", intent_id):
            raise ValueError("Test transaction not found for this session")
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM konaet_test_intents WHERE id=? AND session_id=?", (intent_id, session_id)).fetchone()
        if not row:
            raise ValueError("Test transaction not found for this session")
        return self._view(row)

    def _view(self, row):
        if row["status"] != "pending_test" and not all(row[k] for k in ("receipt","mac","opening")):
            raise ValueError("The completed test receipt is incomplete")
        receipt = json.loads(row["receipt"]) if row["receipt"] else None
        verified = bool(receipt and hmac.compare_digest(hmac.new(self.key, row["receipt"].encode(), hashlib.sha256).hexdigest(), row["mac"] or ""))
        if receipt:
            verified = verified and all(receipt.get(k) == v for k, v in {
                "id": row["id"], "checkout_id": row["checkout_id"], "amount_cents": row["amount_cents"],
                "status": row["status"], "currency": "BRL", "demo": True, "funds_moved": False,
                "seal_key_id": self.key_id}.items())
        if receipt and not verified:
            raise ValueError("The stored test receipt failed seal verification")
        bridge = json.loads(row["opening"]) if row["opening"] else None
        if bridge and (not verify_opening(bridge) or bytes.fromhex(bridge["document_hex"]) != canonical({"receipt":receipt,"server_seal":row["mac"]}).encode()):
            raise ValueError("The stored Sovereign opening is invalid")
        return {"id": row["id"], "checkout_id": row["checkout_id"], "amount_cents": row["amount_cents"],
                "currency": "BRL", "status": row["status"], "provider": "KONAET Sandbox", "demo": True,
                "funds_moved": False, "receipt": receipt, "server_seal": row["mac"], "seal_verified": verified, "sovereign_opening": bridge,
                "notice": "Test transaction only. The server seal is not bank confirmation or an independently signed certificate."}
