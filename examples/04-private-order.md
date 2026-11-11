# Verification and cross-customer access control

Captured from the running application. These are observed responses, not manually scripted assistant answers.
Data fingerprint: `4270a5860500ef3d463a1d95a77dbd44dea5948fe4165586df0f8cae501e2976`

Language: English. Store-local capture date: 2026-11-11. The return scenario explicitly supplies a simulated receipt four days earlier.

**Customer:** What is the status of order 8?

**Assistant:** Before I share order information, please use Verify order with your order number and purchase email. Verification stays in this local application and is not sent to a language model.

Sources: No store facts required.

Planner: `local`. Tool receipts:

```json
[
  {
    "tool": "get_order",
    "status": "verification_required",
    "arguments": {
      "order_id": 8
    }
  }
]
```

*The customer verified the fictional purchase identity through the separate verification form. The email is not placed in the chat or model prompt.*

**Customer:** What is the status of order 8?

**Assistant:** Order #8 is shipped. Recorded total: BRL 349.90.

• 1 × Kala KA-C Concert Mogno

Tracking code: BRJL5544332BR. The recorded delivery estimate is 2026-02-28; this is not confirmation of actual receipt or a refreshed carrier estimate.

This is the supplied order snapshot, not a live carrier lookup.

Sources: Verified order #8

Planner: `local`. Tool receipts:

```json
[
  {
    "tool": "get_order",
    "status": "found",
    "arguments": {
      "order_id": 8
    }
  }
]
```

**Customer:** What is the status of order 1?

**Assistant:** I cannot access that order for the currently verified customer. Please check the number or verify the correct purchase email.

Sources: No store facts required.

Planner: `local`. Tool receipts:

```json
[
  {
    "tool": "get_order",
    "status": "unavailable",
    "arguments": {
      "order_id": 1
    }
  }
]
```
