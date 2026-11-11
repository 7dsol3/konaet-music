# Connected workspace 2.1

The English interface adds a research desk, a private sandbox wallet, explicit
connection states and a logical hardware lab. The submitted Empório repository
is not the destination of these product changes.

## Research and the agent

The music desk uses the existing checked catalog, store policies and scoped
order tools. Open research separately queries Wikipedia and Crossref; Knowledge,
Science and Code select narrower indexes. Code queries use public GitHub repository
metadata. No GitHub user credential or GCM token is forwarded to these services.

The general Web scope uses Brave's documented API only when
`KONAET_BRAVE_SEARCH_KEY` is configured on the backend. It is not active merely
because an account can use this coding assistant's web tools. No search plan or
paid provider account is purchased by this application.

Sources show their provider, available source date and retrieval time. Wikipedia
lead extracts and search excerpts, Crossref bibliographic metadata, GitHub
descriptions and Brave snippets do not constitute reading full linked pages.
The service does not index the whole internet or guarantee the newest result.
Outbound API destinations are fixed; returned links are never fetched by the backend.
Redirects, oversized responses and common credential/private-order queries are rejected.

An optional model explanation receives the public question and at most four
source excerpts. It receives no session history, wallet, customer verification
or private order data. Unknown citation IDs or invalid output cause an explicit
source-brief fallback. Valid citation IDs do not prove that every generated
claim is correct. Qwen remains an external model; no KONAET neural training is claimed.

The source record hash excludes the cache flag and serving latency. Search results
may be kept in bounded process memory for two minutes; the retrieval timestamp is
preserved on cache hits. No-source failures are not cached as successful research.
The recent-research list lasts only in the current tab and can be cleared. A new
conversation clears that list. No private research history is sent to a model to
train weights. Ambient mode is a visual toggle, not a learned preference model.

The GitHub Pages entrance links to the public HTTPS preview. Its Python/model
host and temporary tunnel must stay running. [Availability and deployment
details](DEPLOYMENT.md#public-preview-used-for-21) distinguish that preview from
an independently hosted production application.

## Checkout and the Sovereign bridge

See [the sandbox contract](CHECKOUT-SANDBOX.md). The unique QR opens a versioned,
fifteen-minute quote. Its content is the exact trusted checkout URL; it is not a
bank-issued Pix request. The current session can approve or decline a test
transaction and inspect a sealed test receipt.

The private opening export has the exact three-field
`konaet.social-receipt-opening.v1` shape accepted by the original Sovereign SDK.
It binds the test receipt and server seal to a random-salt SHA-256 commitment.
The two `u128` arguments remain decimal strings, preserving all 256 bits.
This implementation was checked against the original Node SDK in the local
Sovereign checkout. Exporting does not submit to validators, finalize a network
transaction or import assets from another KONAET installation.

## Software and gateware

The logic lab runs a bounded Python model of `ingress_guard.sv`. The testbench
executes actual Icarus Verilog, comparing 1,536 logical cycles across credit
capacities 1, 8 and 32. It covers sustained bursts, refill, simultaneous
request/refill and seeded mixed input. The report records source hashes and the
simulator version. A packaged report is displayed as source-matched only when
the current LF-normalized Python/RTL/testbench hashes agree with it.

No physical board is connected, no network packets are processed by FPGA, and
logical cycles are not measured throughput or a clock-frequency claim. This
demonstrates a software/hardware design contract, not deployed DDoS hardware.

## Interface verification boundary

The interface uses source SVGs, system fonts and CSS. New voice routes still
require a click, an editable transcript and explicit submission. No audio is
captured on load. The service worker caches only an allowlisted public shell;
API data, wallets, quotes, receipts and research results remain outside it.

DOM event contracts exercise the real handlers with browser/network doubles.
They are not rendered-browser, microphone, mobile-installation, frame-rate or
battery tests. Those checks remain necessary on real devices.

## Official API references

- [MediaWiki search](https://www.mediawiki.org/wiki/API:REST_API/Reference)
- [MediaWiki lead extracts](https://www.mediawiki.org/wiki/Extension:TextExtracts#API)
- [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- [GitHub repository search and rate limits](https://docs.github.com/en/rest/search/search#search-repositories)
- [Brave authentication and key handling](https://api-dashboard.search.brave.com/documentation/guides/authentication)
- [Sovereign Receipt Kit](https://github.com/7dsol3/konaet-sovereign-spec/tree/3ccf7a96b701b3b17e58694ef227af4e83cb7d22/polyglot)
