# Demonstration and production gates

The application is an integrated demonstration. Passing its automated suites
does not approve a bank integration, certify security or establish commercial
deployment capacity. The submitted technical case remains unchanged; this is a
separate evolution. The November 11 review identifies the following real gates.

| Gate | Implemented evidence | Still required for production |
| --- | --- | --- |
| Identity | Strict session-owned state, cookie controls, order-data scope checks, no private fields to model planning | A configured account provider, secure recovery, actual customer ownership and authorization tests; fixture order/email verification is demonstration only |
| Scaling / operations | Bounded application requests, single-process SQLite transactions and idempotent sandbox updates | Durable hosted service, shared limits/state, tested backups/restoration, capacity and SLO/load/failover measurements; the current tunnel depends on a local host |
| Payments | Exact server quotes, test credits, atomic test outcomes, sealed receipts and replay/foreign-session checks | Contracted payment provider, credential provisioning, signed-event validation, reconciliation, refunds, fraud and inventory-reservation integration; no bank account or Pix settlement is supplied |
| Interface / devices | DOM event tests, strict schemas, local-audio lifecycle, independent QR decode, source budgets | Actual supported browsers and phones, microphone/speaker checks, assistive-technology audit, installation and field performance measurements |
| Rights | Original code MIT; frozen third-party modules and external weights remain attributed under their own licenses | Written authorization for redistribution/use of supplied challenge CSV/PDF data, and commercial permission or replacement for the RCL-licensed policy component; MIT does not grant those rights |
| Digital hardware | Portable H-01 RTL, integer parity, serial framing tests, generic synthesis gate | Target-specific resource/timing closure, physical board, power/analog/EMC work and bench validation |
| Model capability | Local checked tools, explicit external-model identity, bounded failures and optional coaching | Comparable real-task benchmarks with fixed model/weights/data, raw results and independent replication; no universal-superiority or 100% real-world accuracy claim |

These gates are not resolved by changing a badge or assigning a higher version.
The public API exposes `commerce_mode=demo`, `can_charge_real_money=false` and
physical-device flags. The interface calls balances test credits and receipts
sandbox results. It never treats a QR as proof of payment.

Deployment recipes in this repository remain demonstration recipes. The active
preview is useful for inspecting functionality; it is not a hosted commercial
service with an uptime promise. No paid provider, identity tenant, bank credential,
physical prototype or redistribution permission is fabricated by a code change.
