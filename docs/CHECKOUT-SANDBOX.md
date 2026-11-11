# KONAET Checkout sandbox

This is a local test ledger and checkout state machine. It does not replace Pix,
operate a bank or move fiat/crypto assets. A real merchant account, authorized
inventory, provider integration and reconciliation are not provisioned here.

1. The server checks catalog lifecycle and quantity, calculates discounts and
   rounds the advertised discounted **unit** price to cents with ROUND_HALF_UP.
   It multiplies that price by quantity in both the bag and quote. Eligible Pix
   pricing does not stack with a promotion. The rule is `unit_round_v1`.
2. The quote has a random 192-bit reference, an immutable snapshot and a fifteen-
   minute expiry. Reusing a request key with changed contents is rejected.
3. Only the session that prepared the quote can create its sandbox intent.
   A browser-supplied total, session identity or outcome outside the typed
   contract is rejected. Legacy pricing snapshots require a fresh quote.
4. A test wallet begins with 10,000 test BRL, with no cash value. Top-ups add
   fixed test credits, subject to request and balance caps. Its `KNT_TEST_`
   address is not a real crypto address or deposit destination.
5. Approval atomically checks expiry, ownership, quote amount and credit balance
   in a SQLite immediate transaction. Duplicate and concurrent confirmation
   returns the same final result without a second debit. A decline keeps the
   balance. Neither final outcome can change into the other.
6. The receipt is labeled `paid_test` or `declined_test`, with `demo: true` and
   `funds_moved: false`. The original quote remains a quote, not bank confirmation.
   Stock is never reserved or decremented by these test actions.

The backend creates a random 32-byte local test-seal key in the private state
directory; it is not committed or sent to the browser. HMAC-SHA256 binds the
stored receipt bytes, and reads also check their amount, intent, quote and status
bindings. The opening commits the same receipt/seal using Sovereign's domain.
Do not silently replace that key: existing receipts would stop verifying.

The seal is symmetric server authentication, not an independent digital signature,
bank certificate, legal proof of settlement or external ledger anchor. An operator
who controls the database and secret can replace them. The test wallet is not
an anti-fraud model or a production accounting system.

The private Sovereign opening export is compatible with:

```text
node polyglot/node/export-frame.cjs konaet-private-test-opening.json
```

It discloses its document and salt. Keep it private; submit only the appropriate
commitment through a separately authorized Sovereign operator workflow if that
is desired. No operator key, validators, quorum certificate or chain submission
is part of this application.

Clearing or expiring the session removes its sandbox wallet and intents through
foreign-key cascades. The minimal existing audit chain has its documented local
retention behavior. Public product quotes may remain accessible by capability
link until their expiry and carry no customer identity.
