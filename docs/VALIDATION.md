# KONAET Music 2.0 validation

Observed on Windows x64, Python 3.12.10 and Node 24.22.2, 11 November 2026.
The original submission's evidence remains in Git history. The files identified
below distinguish new tests from historical screenshots and UI captures.

## Automated application and interface checks

| Check | Observed result | Scope |
| --- | --- | --- |
| Python suite | 87 passed, one upstream TestClient deprecation warning | Existing agent rules plus new commerce, hardening and QR cases |
| DOM event contracts | 6 passed | Real interface handlers with controlled API/browser doubles |
| Installed distribution | PASS | Wheel built and installed outside source tree; 65 products imported and a grounded query answered |
| Static interface checks | PASS | English root, unique IDs, referenced assets, SVG parsing and source byte budgets |
| Compilation | PASS | Python compileall and Node syntax checks |
| Actions source lint | PASS | actionlint 1.7.12 |

The source budget report measured approximately **97 KB raw / 30 KB gzip** for
14 active UI asset files, with no font/CDN calls. This is an asset-size measure,
not a real mobile load-time, battery-use or frame-rate result.

QR verification rasterizes the actual branded SVG and decodes it with ZXing-C++
at 260/520 pixels and 0/90/180 degrees. It tests two URL lengths, error correction H,
unsafe-target rejection and escaping. It does not guarantee every banking app
or camera will scan the code under every condition. The code opens a product
quote; no Pix payment was created.

Commerce tests cover session isolation, reset, unavailable quantities, exact
pricing, promotion/PIX nonstacking, immutable quote retry, expiry, untrusted
request fields, cross-origin rejection and the full HTTP quote/SVG path.

Hardening cases reject missing original packaging in English/Portuguese,
missing accessories/manuals, widened model budgets/categories/availability,
private order context sent to the provider and model planning for private orders.
A number-leading SKU such as `110e` stays selected for a subsequent payment query.

## Fresh actual local model evaluation

Official Qwen3-0.6B GGUF Q8_0 was served by checksum-pinned llama.cpp `b12024`
on the local CPU. No paid API or remote inference was used. The model and engine
were verified against their recorded SHA-256 identities before execution.

The five English conversations in `examples/` were recaptured through the running
2.0 API. [live-evaluation.json](live-evaluation.json) records observed tools and
latencies; scripted outcome assertions all passed.

| Observation | Result |
| --- | ---: |
| Scenarios | 5 |
| Customer turns | 13 |
| Accepted model-selected plans | 4 |
| Explicit local fallbacks after model planning | 4 |
| Local scope/private-order turns | 5 |
| Median model-attempt end-to-end latency | 6,510.55 ms |
| Model-attempt range | 6,181.2–6,785.4 ms |

The three private-order turns intentionally bypass model inference. A fallback
is not counted as successful neural planning. These thirteen scripted turns
are not a general accuracy estimate or a comparison with Siri/Alexa.

The first 2.0 live capture failed a PIX follow-up because the local model-code
extractor ignored the digit-leading `110e` SKU. A focused regression and code fix
preceded the successful full recapture. The failed attempt was not presented as
the final evidence. Earlier 1.0 failure captures remain labeled as historical.

## Verification not completed

The native app pipe and browser access host were unavailable. No new browser
screenshot, pixel-layout check, microphone recording, spoken-output listening
test or iOS/Android install test was performed. `docs/ui-check.json` and
`docs/screenshots/` are original 1.0 artifacts, not proof of the new glass UI.
The DOM contracts do not replace those checks.

No public Python backend has been provisioned by these source tests. The optional
Render blueprint still requires an account and configured HTTPS origin. No
merchant account, provider sandbox, bank payment, inventory reservation or
refund integration was tested. Do not use the case fixtures with real customers.

## Reproduce

```text
python -m pip install -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest --junitxml=artifacts/pytest.xml
python scripts/verify_frontend.py
python scripts/verify_wheel.py
python scripts/capture_product_evidence.py
cd tests/ui
npm ci --ignore-scripts
cd ../..
node --test tests/ui/interface.test.mjs
```

Run the neural helper first, then `python scripts/capture_examples.py` to repeat
the five actual conversations. Set `KONAET_CAPTURE_URL` when using another port.
Model outputs and CPU latency vary; failed assertions must be investigated,
not removed or silently turned into successful examples.

The GitHub workflow defines Python 3.11/3.12 on Ubuntu/Windows and a separate
Node interface job. Its actual remote outcome is recorded by GitHub, separately
from the local results above. Review that run for the exact published commit.

## Distribution inventory

The final release gate found a retired `language.js` file left in a local build
cache. That package was not published. `scripts/build_distribution.py` now builds
from fresh source staging, compares every packaged runtime file with current
source bytes, and rejects extra or missing entries. `verify_wheel.py` also checks
that an injected stale asset is rejected before exercising the isolated install.

Build a distributable with the checked path:

```text
python scripts/build_distribution.py --out-dir artifacts/distribution
```
