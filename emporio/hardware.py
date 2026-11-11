"""Reference model for the included RTL, with explicit simulation provenance."""
import hashlib
import json
from pathlib import Path

GATEWARE = Path(__file__).parent / "gateware"


def trace_model(vectors, capacity):
    if type(capacity) is not int or not 1 <= capacity <= 32 or not 1 <= len(vectors) <= 512:
        raise ValueError("Use 1–32 credits and at most 512 logical cycles")
    credits, trace = capacity, []
    for cycle, pair in enumerate(vectors):
        request, refill = pair
        if type(request) is not bool or type(refill) is not bool:
            raise ValueError("Hardware inputs must be booleans")
        available = min(capacity, credits + int(refill))
        admitted = request and available > 0
        rejected = request and not admitted
        credits = available - int(admitted)
        trace.append({"cycle": cycle, "request": request, "refill": refill, "admitted": admitted, "rejected": rejected, "credits": credits})
    return trace


def simulate(cycles=96, capacity=8, refill_every=5, burst=40):
    if any(type(v) is not int for v in (cycles, capacity, refill_every, burst)) or not 16 <= cycles <= 192 or not 1 <= refill_every <= 32 or not 1 <= burst <= cycles:
        raise ValueError("Invalid bounded simulation inputs")
    trace = trace_model([(n < burst or n % 7 == 0, n % refill_every == 0) for n in range(cycles)], capacity)
    return {"mode": "logical_simulation", "physical_device_connected": False, "cycles": cycles, "capacity": capacity,
            "admitted": sum(r["admitted"] for r in trace), "rejected": sum(r["rejected"] for r in trace), "trace": trace,
            "notice": "Logical credit-gate cycles, not real packet throughput or a measured FPGA clock.", "validation": validation()}


def source_hashes():
    # Git/Windows line-ending conversion does not change the source contract.
    digest = lambda p: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return {"python_reference": digest(Path(__file__)), "systemverilog": digest(GATEWARE / "ingress_guard.sv"),
            "testbench": digest(GATEWARE / "ingress_guard_tb.sv")}


def validation():
    path = GATEWARE / "validation.json"
    if path.is_file():
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("sources") == source_hashes() and report.get("status") == "PASS":
            return {"status": "source_matched_record", "vectors": report["vectors"], "simulator": report["simulator"],
                    "notice": "Recorded RTL/reference agreement; no physical device tested"}
    return {"status": "record_unavailable", "vectors": 0, "notice": "Run scripts/verify_gateware.py with Icarus Verilog"}
