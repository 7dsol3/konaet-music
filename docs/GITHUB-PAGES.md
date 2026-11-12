# Standalone GitHub Pages edition

Open **https://7dsol3.github.io/konaet-music/**. The store and
**https://7dsol3.github.io/konaet-music/sound-lab/** run as static browser apps.
No tunnel or computer belonging to the author is needed to serve them.

## Use a downloaded copy

Extract the source ZIP, install Python 3.11 or newer, and double-click
`Run Browser Demo.cmd` on Windows. On macOS/Linux use:

```sh
python3 scripts/serve_browser.py
```

The launcher builds into `dist/browser-local`, serves only that public directory
on `127.0.0.1:8040`, and opens the browser. No pip install, model download, payment
credential or API key is required. Keep the terminal open; Ctrl+C stops it.
If that port is busy, pass `--port 8041`. Opening the HTML with `file://` is not
supported: modules, fetch, microphone permissions and storage need a local server.
Localhost QR links work on the same PC. Use the public Pages edition to scan
from another device; localhost on a phone refers to that phone.

The existing `Run Offline.cmd` installs and runs the full Python edition.
`Run Demo.cmd` also prepares the optional external Qwen/llama.cpp model.

## What runs in the browser

- Bundled public catalog, filters, comparison, bag and per-unit integer pricing.
- Browser-rule music assistant and source-linked store guide.
- Fifteen-minute quote URLs, three original frames around standard QR matrices.
- Local test wallet with serialized, idempotent demo confirmations.
- Chords, tuning, WAV export, explicit microphone opt-in, local-file analysis,
  music rules and the integer audio/credit-gate references.
- Optional direct requests to Wikipedia, GitHub and Crossref for public research.

The browser edition saves its bag, conversation and test credits in this
browser's localStorage. Other browsers and devices have separate state. If storage
is blocked, the current tab remains usable without persistence. Clear the
conversation to reset the local demo. Browser storage is editable by its owner.

QR links contain only catalog fingerprint, item IDs/quantities, pricing method,
creation time and a random reference. The receiving browser checks bounds,
stock, catalog fingerprint and expiry and **recalculates** each price. No balance,
email, order identity or secret is included. The link has **no authentication**:
editing a selection creates a different demonstration, never a valid payment.
Browser receipts have no server seal, bank settlement, inventory reservation or
Sovereign finalization. Private fixture order verification, server-sealed receipts,
Sovereign openings and neural inference require the full Python application.

Network/CORS/rate limits can prevent public research. The UI reports unavailable
providers rather than presenting invented results. Speech recognition depends
on the browser and may use its speech service. Offline use after the first load
caches public assets; private records and live search results are not cached.

## Build, publication and checks

```sh
python scripts/build_pages.py
```

Produces `dist/pages` for `/konaet-music/`. The Pages workflow publishes this
directory on main changes to frontend/build inputs. It no longer publishes the
legacy entrance in `deploy/pages`. To refresh public catalog data after changes
to the Python case rules, install runtime dependencies and run
`python scripts/build_pages.py --refresh-catalog`, review `deploy/browser/catalog.json`,
and commit it. CI rejects a snapshot that differs from the authoritative source.
Customer, order and order-item records never enter the browser build.

The JavaScript suite exercises real DOM handlers with the actual browser
runtime and checks cross-device quote parsing, expiry, stock, duplicate confirms,
storage failure and research failure. An independent ZXing decoder reads all
three generated SVGs at 400/520/800 px and 0/90° rotation. The browser's PCM,
meters and logical trace are compared exactly with the Python reference.
These are behavior/source/HTTP checks; they do not certify visual layout,
microphone hardware, acoustic fidelity or production payment processing.

The QR matrix encoder is `qrcode-generator` 2.0.4 (MIT, Kazuhiko Arase), vendored
with npm package integrity and source SHA-256. KONAET supplies the surrounding
artwork, quote encoding and integration. No external QR service receives a URL.
