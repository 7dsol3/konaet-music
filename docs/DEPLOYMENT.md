# Deployment and admission boundaries

The standalone browser demo is hosted directly on GitHub Pages at
`https://7dsol3.github.io/konaet-music/`, including `/sound-lab/`. It has no Python
origin or tunnel dependency. The build and its different checkout trust boundary
are documented in [GITHUB-PAGES.md](GITHUB-PAGES.md).

The full server application needs a Python host. GitHub Pages does not execute
the Python API, private session store or optional neural inference engine.
The included Render blueprint is an optional demo deployment recipe, not an
active production deployment. Its ephemeral storage is unsuitable for real orders.

The ASGI shield bounds request bodies (including chunked input) to 16 KiB,
headers to 32 KiB, URL length to 4 KiB, body-read time to five seconds and
in-flight requests to 24 per process. Endpoint limits and a 4,096-key rate-tracker
cap bound additional work; a full tracker rejects new keys instead of growing.
Public providers also have an eight-attempt-per-minute budget each. Neural
research synthesis has two slots and otherwise falls back to the source brief.

These controls mitigate specific application resource-exhaustion paths. They do
not absorb internet traffic, protect the network uplink, measure volumetric
DDoS resistance or guarantee availability. The RTL credit-gate simulation is a
separate verified design demonstration; it does not offload these HTTP requests.

Before an internet deployment, put the origin behind a configured TLS reverse
proxy and DDoS protection edge. Restrict direct origin access, buffer/limit bodies
and connections at the proxy, and establish capacity and recovery objectives.
Only trust forwarded client-IP headers from explicitly configured proxy addresses.
The local launchers disable generic proxy-header trust. If the backend sees only
one proxy IP, its per-IP limits are shared; perform per-client limiting at the
trusted edge instead of trusting arbitrary incoming X-Forwarded-For values.

Use one application worker for this SQLite demo, a persistent private state
directory and tested backups. Process-memory caches and limits are not shared
across replicas. A production distributed service requires appropriate shared
coordination, storage and infrastructure verification. No DNS, WAF, TLS, cloud
account or edge configuration was created by the source-only tests.

## Historical temporary preview used for 2.1 and 2.2

The former preview used an accountless `trycloudflare.com` tunnel to a
Python process bound to loopback. Its public origin is set as `KONAET_PUBLIC_URL`
before launch, so QR codes point to HTTPS rather than localhost. The tunnel,
Python runtime and neural engine must remain running. The address is temporary;
a restarted quick tunnel gets another address and requires updating the origin
and entrance link. Old quote links do not become valid on a new origin.

`scripts/launch_public.py` takes runtime configuration through hidden stdin,
validates a direct tunnel's hostname, and supports a detached preview process.
No system startup task or Windows service is installed. The process-memory
origin secret used in the optional gateway is not saved to Git or CLI arguments.

The previously provisioned Sites gateway could not be updated in the later
session: mutation calls returned `project_not_found` even though its captured
public metadata could be read. Its URL is not the active preview linked here.
The tested optional Worker gateway source remains in `deploy/gateway/index.mjs`;
it is not represented as the active path or a verified production DDoS edge.

The direct tunnel presents one local peer to Python, so the application's IP
budgets are shared by preview visitors. Arbitrary forwarded-IP headers are not
trusted to bypass those budgets. This is a bounded demonstration, not a 24/7 SLA.

The host/origin boundary, Strict HttpOnly cookies, HTTPS Secure cookies, same-origin
scripts, CSP, text-only rendering and no-store API responses remain in place.
No real payment provider or private inference key belongs in the frontend.
Exercise abuse tests only against your own isolated environment with bounded load.

[Cloudflare's description of actual network/HTTP DDoS protection](https://developers.cloudflare.com/ddos-protection/)
explains why application limits and an upstream edge cover different layers.
