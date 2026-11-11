# Sound Lab 2.2 validation

The Sound Lab and H-01 are added to the existing 2.1 workspace. This record
separates new source/CI evidence from physical-device and production gates.

## Reproduce

```sh
python -m pytest --junitxml=artifacts/pytest.xml
node --test tests/ui/interface.test.mjs tests/ui/sound-lab.test.mjs tests/sound-dsp.test.mjs tests/gateway.test.mjs
python scripts/verify_frontend.py
python scripts/verify_wheel.py
python scripts/verify_gateware.py
python scripts/verify_audio_gateware.py --synthesis
```

Node 24.22.2 is used by CI. Install the pinned development dependencies as
documented in the repository; Icarus Verilog and Yosys are required for the last
two checks. No unavailable RTL tool produces a passing substitute.

## Recorded results

- New local audio checks: 11 Python tests and 16 JavaScript DSP/DOM tests passed.
- Existing plus new JavaScript contracts: 32 passed.
- Full Python suite before the Windows MIME regression was added: 189 passed
  locally; the final CI matrix includes that extra regression test.
- Home assets: 142,870 raw / 43,780 gzip bytes. Sound Lab's separate lazy assets:
  45,794 raw / 16,910 gzip bytes. Byte budgets are not browser speed measurements.
- Isolated wheel smoke: 65 catalog products and complete runtime inventory;
  stale build-cache entries rejected. The source-matched audio record adds one
  packaged JSON file after the initial smoke run.
- H-01: 4,096 exact integer clock vectors, 51 complete meter blocks, 256 decoded
  stereo I²S frames, 511 received loopback words and connected top-level activity.
  Generic Yosys synthesis and `check -assert` passed; generic cell count 5,982
  (not target LUT utilization). Icarus 12.0 / Yosys 0.33.
- [H-01 validation run](https://github.com/7dsol3/konaet-music/actions/runs/43113977896)
  at source `5216be8489325bfc68743d059757717215ab1f61` passed the RTL and interface
  jobs. The Windows Python jobs found a `.mjs` MIME association problem; the
  subsequent fix serves ES modules with an explicit JavaScript MIME and tests an
  incorrect OS association. That initial run is not represented as fully green.
- [Packaged audio record](../emporio/gateware/audio-validation.json) binds normalized
  reference/RTL/testbench hashes. The API reports `source_matched_record` only
  when every hash matches; record availability does not assert a physical board.

See [PR 8](https://github.com/7dsol3/konaet-music/pull/8) for final required-check
results and the merged source revision. Release assets provide the finished
package and evidence for the release revision rather than a mutable preview.

## Limits

Browser-control infrastructure was unavailable during this implementation.
DOM tests exercised actual event handlers with audio API doubles; no real
microphone permission, speaker output, phone rendering, PWA installation or
accessibility certification was performed. The GIF was rendered from exact
reference PCM samples and visually inspected as an exported chart.

Physical FPGA testing, constrained board implementation, general music-recognition
accuracy, production identity/payments/scale/rights and a paired Kimi runtime
benchmark remain open. The new software does not turn these gates into PASS.
