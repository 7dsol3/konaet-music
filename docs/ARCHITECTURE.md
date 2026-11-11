# KONAET Music architecture

Python remains the application language. FastAPI serves a buildless English
HTML/CSS/JavaScript interface and a SQLite-backed API from one origin. There is
no frontend framework, vector database, client payment secret or browser LLM.

## Customer flows

1. Public discovery reads the current imported case snapshot and exposes the
   existing discount/availability rules, translated category labels and filters.
2. Comparison retrieves two or three explicit distinct IDs. Absent specs remain
   unrecorded, rather than being supplied by the model.
3. A cryptographically random HttpOnly session owns its bag. SQL binds every cart
   query to that server session; request bodies cannot choose another session.
4. Quote creation rechecks quantities and prices. Per-line totals use integer
   cents and Decimal rounding. Active promotions take precedence over 5% PIX;
   no stacking is performed. Shipping is excluded and inventory is not reserved.
5. The server stores an immutable quote, its request key, a cart/method hash and
   a fifteen-minute expiry. Same request plus same cart returns the same quote;
   changed inputs are rejected. A new key creates a new random reference.
6. The code endpoint creates the original branded SVG from the trusted configured
   origin and opaque quote reference. The quote contains no private identity.
   A capability URL can be viewed by its holder until expiry.

All quote states are preview/not-started. There is no payment state machine,
refund executor, reservation API or model-authorized financial action in 2.0.
Payment integration requires separate merchant work described in PAYMENTS.md.

## Agent boundary

The local bilingual router inherited from the case is the fallback and default.
The customer UI always requests English. An optional native function-calling
model can choose bounded read-only functions. Only allowlisted schemas pass;
no generated SQL or arbitrary source is executed.

Catalog category, budget, availability and explicit brand/model constraints
cannot be broadened by a provider plan. Explicit transaction arguments are
similarly checked. The deterministic renderer uses tool facts for prices,
installments, availability and preliminary policy outcomes.

Order requests bypass the external planner. Server-side session ownership
filters SQL, and number/email fixture verification does not become a claimed
production account. Only `category` and `last_products` enter provider context.
Order identifiers in recent user messages are redacted, as are recognizable
email/phone patterns. This is deliberate minimization, not general PII detection.

Private return facts remain local. Missing packaging or materials trigger
human review. The small model can still choose an ineffective query; model mode,
fallback, tools, latency and source receipts remain visible.

## Voice and PWA

Speech recognition populates an editable draft, with no auto-submit. Speech
synthesis is separately opt-in. Browser permissions and services are outside
the Python process; these features are not a proprietary speech model.

The worker caches only the public app shell. No API, checkout, code or private
content is cached or queued offline. Unavailable API calls must fail visibly.
The standalone manifest provides installation metadata where supported.

## State, freshness and deployment

The six original CSVs import transactionally. New source fingerprints invalidate
sessions so recycled customer IDs cannot preserve old verification. Deleting a
session cascades its bag; existing product-only quotes expire independently.
Historical audit receipts remain minimal hash-linked records without a public
anchor. Policy summaries and decision rules remain tied to the original PDF hash.

The original prototype's process-wide turn lock deliberately serializes agent
and cart mutations. One application process is supported. This prioritizes local
correctness over throughput and has not been measured as a multi-tenant system.

The public origin must be configured, rather than inferred from incoming Host.
Cookies receive Secure on HTTPS configurations; same-origin write checks, Host
checks, rate limits and typed bodies continue to apply. Compression reduces
transfer size. Real upstream authentication, encrypted managed storage,
distributed limits, observability and incident response remain production work.

The optional Render blueprint deploys a **demo** process with ephemeral state.
No cloud service has been provisioned by this repository alone. GitHub Pages
and the Sites Worker runtime cannot execute the current Python/SQLite service
unchanged; publishing only its static files would leave critical controls broken.
