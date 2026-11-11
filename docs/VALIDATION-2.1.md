# Connected workspace validation — 11 November 2026

The 2.1 validation extends the historical [2.0 record](VALIDATION.md). It does
not relabel old screenshots or original case evidence as proof of this redesign.

## Observed application results

| Check | Result | Scope |
| --- | --- | --- |
| Full Python suite | 158 passed; one upstream TestClient deprecation warning | Grounded agent, commerce, research, sandbox, request shield and hardware model |
| Interface event contracts | 11 passed | Real handlers with controlled browser/API doubles |
| Optional gateway contracts | 5 passed | Credential/cookie isolation, routes, bounded bodies and failure states |
| Installed wheel | PASS | Clean source staging, full inventory/byte comparison, retired-asset rejection, isolated install and 65-product query |
| QR styles | 36 independent decode cases | Three frames × two URLs × two widths × three rotations; no logo covers the symbol |
| Active UI source size | 142,782 bytes raw / 43,750 gzip | 18 files; not load-time, FPS, battery or mobile performance |
| Public HTTPS flow | PASS | Two cookie jars, exact quote URL, three QR decodes and actual decoded-link opens |
| Sovereign SDK compatibility | PASS in local original Node SDK | Same commitment and exact two decimal `u128` arguments; no validator submission |

The complete Python suite covers every available catalog product with both card
and eligible Pix quote math, fractional-cent promotional rounding, concurrent
duplicate confirmation, foreign-session denial, expired and legacy pricing
rejection, receipt/binding tampering and session revocation.

The fractional-cent regression initially exposed a distinction between a displayed
discounted unit price and line-total rounding. Both bag and quote now round the
unit price consistently before multiplication. A stale interface assertion also
expected the default SVG after selecting Studio; it was corrected to check the
selected server URL. Failed checks were resolved, not excluded.

## Actual public preview exercise

[public-workspace-verification.json](evidence/public-workspace-verification.json)
records the sanitized run. It contains no active quote capability URL, cookies,
wallet address, local seal key or private opening.

The exercise created a quote through HTTPS, opened it with another cookie jar,
decoded all three actual SVG styles with ZXing-C++, and fetched each decoded
URL. The visitor could view the product quote but could not create its owner's
sandbox intent. Approval replay returned the same receipt and debited only once.
The seal and private Sovereign opening verified; resetting the session revoked
the test wallet/intent. Wikipedia source retrieval and 96 logical hardware cycles
also completed. The configured Qwen endpoint responded to model discovery.

This public exercise used **sandbox credits only**. It did not issue a bank Pix,
reserve inventory, move fiat or crypto assets, create a production account or
send a commitment to a validator network. It is not proof of real settlement.

## Hardware evidence

The independent RTL job runs Icarus Verilog against the included Python reference
for 1,536 logical cycles and capacities 1, 8 and 32. Its actual report is linked
by source hashes in `emporio/gateware/validation.json` when a completed run is
recorded. The UI shows `record_unavailable` rather than claiming approval when
the record is missing or mismatched. No physical FPGA board or packet throughput
measurement is part of this validation.

## Limits still visible

The browser/native control host was unavailable. DOM contract tests do not prove
rendered layout, accessibility conformance, real microphone output, iOS/Android
installation or frame rate. No general assistant, learning or Alexa/Siri benchmark
was performed. Provider configuration does not prove unrestricted internet coverage;
Brave's general Web scope requires a backend key and is not configured in this preview.

The HTTPS preview depends on the local host and temporary tunnel remaining online.
GitHub Pages hosts an entrance; it does not execute the Python service. Source-level
request limits are not a volumetric DDoS certification or a production availability SLA.

## Reproduce

```text
python -m pytest --junitxml=artifacts/pytest.xml
node --test tests/ui/interface.test.mjs tests/gateway.test.mjs
python scripts/verify_frontend.py
python scripts/verify_wheel.py
python scripts/verify_gateware.py
```

The last command requires real `iverilog` and `vvp`. To repeat the public flow,
set `KONAET_CAPTURE_URL` to the trusted demo HTTPS origin and run
`python scripts/capture_workspace_evidence.py`. It exercises only demonstration
transactions. Remote Actions runs bind their outcome to the exact checked source.
