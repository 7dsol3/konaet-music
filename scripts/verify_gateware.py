"""Compare real Icarus RTL output against the Python reference over seeded vectors."""
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
from emporio.hardware import GATEWARE, source_hashes, trace_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="Update the packaged record after a real passing run")
    args = parser.parse_args()
    compiler, runner = shutil.which("iverilog"), shutil.which("vvp")
    if not compiler or not runner:
        raise SystemExit("Install Icarus Verilog (iverilog and vvp); no simulated pass is substituted")
    version = subprocess.check_output([compiler, "-V"], text=True, stderr=subprocess.STDOUT).splitlines()[0]
    rng = random.Random(20261111)
    vectors = [(True, False)]*40 + [(False, True)]*40 + [(True, True)]*40
    vectors += [(rng.random()<0.8, rng.random()<0.3) for _ in range(392)]
    checked = 0
    with tempfile.TemporaryDirectory(prefix="konaet-gateware-") as temporary:
        folder = Path(temporary)
        inputs = folder / "vectors.txt"
        inputs.write_text("".join(f"{int(a)} {int(b)}\n" for a,b in vectors), encoding="ascii")
        for capacity in (1, 8, 32):
            binary = folder / f"guard-{capacity}.vvp"
            subprocess.run([compiler, "-g2012", "-s", "ingress_guard_tb", f"-Pingress_guard_tb.CAPACITY={capacity}", "-o", str(binary), str(GATEWARE/"ingress_guard.sv"), str(GATEWARE/"ingress_guard_tb.sv")], check=True, timeout=30)
            output = subprocess.check_output([runner, str(binary), "+vectors="+str(inputs)], text=True, timeout=30)
            observed = [tuple(map(int, m)) for m in re.findall(r"TRACE (\d+) (\d+) (\d+) (\d+)", output)]
            expected = [(r["cycle"],int(r["admitted"]),int(r["rejected"]),r["credits"]) for r in trace_model(vectors, capacity)]
            assert observed == expected, f"RTL/reference disagreement at capacity {capacity}"
            checked += len(observed)
    report = {"status":"PASS", "vectors":checked, "capacities":[1,8,32], "seed":20261111,
              "simulator":version, "sources":source_hashes(), "physical_device_tested":False}
    artifacts = ROOT/"artifacts"; artifacts.mkdir(exist_ok=True)
    (artifacts/"gateware-validation.json").write_text(json.dumps(report,indent=2)+"\n", encoding="utf-8")
    if args.record:
        (GATEWARE/"validation.json").write_text(json.dumps(report,indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
