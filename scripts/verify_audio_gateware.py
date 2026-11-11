"""Execute real RTL/reference parity, I2S decoding/loopback and generic synthesis."""
import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from emporio.audio import GATEWARE, dds_trace, meter_trace, source_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--synthesis", action="store_true")
    args = parser.parse_args()
    compiler, runner = shutil.which("iverilog"), shutil.which("vvp")
    if not compiler or not runner:
        raise SystemExit("Icarus Verilog is required; unavailable is never reported as PASS")
    rng = random.Random(20261111)
    rows = [(True, False, True, 0, [0, 0, 0], False, 0)]
    # Exact max-energy, sign, clip-threshold, reset and all voice-mask cases.
    for value in (-32768, 32767, 0, 32699, -32700):
        rows += [(False, True, False, 7, [0x7FFFFFFF, 0x80000000, 0xFFFFFFFF], True, value)] * 64
    for n in range(3775):
        rows.append((n % 733 == 732, rng.random() < .8, rng.random() < .12, n % 8,
                     [rng.randrange(2**32) for _ in range(3)], rng.random() < .83, rng.randrange(-32768, 32768)))
    synth = dds_trace([row[:5] for row in rows])
    meter = meter_trace([(row[0], row[5], row[6]) for row in rows])
    modules = ["audio_dds", "audio_meter", "audio_i2s_tx", "audio_i2s_rx", "konaet_audio_core"]
    with tempfile.TemporaryDirectory(prefix="konaet-audio-") as temporary:
        folder = Path(temporary)
        inputs = folder / "vectors.txt"
        inputs.write_text("".join(" ".join(map(str, [int(r), int(e), int(m), mask, *steps, int(v), pcm])) + "\n"
                                  for r, e, m, mask, steps, v, pcm in rows), encoding="ascii")
        binary = folder / "audio.vvp"
        sources = [str(GATEWARE / (m + ".sv")) for m in modules]
        subprocess.run([compiler, "-g2012", "-s", "audio_core_tb", "-o", str(binary), *sources,
                        str(GATEWARE / "audio_core_tb.sv")], check=True, timeout=30)
        output = subprocess.check_output([runner, str(binary), "+vectors=" + str(inputs)], text=True, timeout=60)
        observed = [tuple(map(int, match)) for match in re.findall(r"TRACE (\d+) (\d+) (-?\d+) (\d+) (\d+) (\d+) (\d+)", output)]
        expected = [(i, int(a["valid"]), a["sample"], int(b["valid"]), b["peak"], b["energy"], b["clipped"])
                    for i, (a, b) in enumerate(zip(synth, meter))]
        assert len(observed) == len(expected), "Incomplete RTL output"
        for actual, wanted in zip(observed, expected):
            assert actual == wanted, f"Audio integer mismatch: actual={actual}, expected={wanted}"
        patterns = [-32768, 32767, 0, 0x1234, -1, 0x5555, -21846, -12345]
        frames = [tuple(map(int, m)) for m in re.findall(r"I2S (\d+) (-?\d+) (-?\d+)", output)]
        assert frames == [(i, patterns[i % 8], patterns[i % 8]) for i in range(256)], "I2S frame mismatch"
        rx = [tuple(map(int, m)) for m in re.findall(r"RX (\d+) (-?\d+)", output)]
        expected_rx = [(channel, patterns[i % 8]) for i in range(256) for channel in (0, 1)][1:]
        assert rx == expected_rx, "I2S receive/loopback mismatch"
        assert "DONE " in output
        synthesis = "not_run"
        if args.synthesis:
            yosys = shutil.which("yosys")
            if not yosys:
                raise SystemExit("Yosys required for requested synthesis")
            # Paths are generated in a temporary script, not a shell command.
            script = folder / "synth.ys"
            script.write_text("read_verilog -sv " + " ".join('"' + s.replace('\\', '/') + '"' for s in sources) +
                              "\nhierarchy -check -top konaet_audio_core\nsynth -top konaet_audio_core\ncheck -assert\nstat\n", encoding="utf-8")
            run = subprocess.run([yosys, "-s", str(script)], text=True, capture_output=True, timeout=120, check=True)
            (ROOT / "artifacts").mkdir(exist_ok=True)
            (ROOT / "artifacts/audio-synthesis.log").write_text(run.stdout, encoding="utf-8")
            synthesis = "generic_yosys_pass_no_place_and_route"
    report = {"status": "PASS", "clock_vectors": len(rows), "meter_blocks": sum(r["valid"] for r in meter),
              "i2s_frames": len(frames), "i2s_received_words": len(rx), "seed": 20261111,
              "simulator": subprocess.check_output([compiler, "-V"], text=True, stderr=subprocess.STDOUT).splitlines()[0],
              "synthesis": synthesis, "sources": source_hashes(), "physical_device_tested": False}
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/audio-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.record:
        (GATEWARE / "audio-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
