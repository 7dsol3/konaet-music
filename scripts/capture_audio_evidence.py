"""Verify public Sound Lab delivery and API/reference contracts, without a browser."""
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    origin = os.environ.get("KONAET_CAPTURE_URL", "http://127.0.0.1:8034").rstrip("/")
    parsed = urllib.parse.urlsplit(origin)
    if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or (
            parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}):
        raise SystemExit("Use a trusted HTTPS workspace or loopback")

    def call(path, body=None, expected=200):
        request = urllib.request.Request(origin + path, data=json.dumps(body).encode() if body is not None else None,
                                         headers={"Content-Type": "application/json", "Origin": origin,
                                                  "User-Agent": "KonaetAudioVerification/2.2"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status, data, headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as error:
            status, data, headers = error.code, error.read(), error.headers
        assert status == expected, f"Unexpected HTTP status {status} on {path}"
        return data, headers

    page, headers = call("/sound-lab")
    assert b'lang="en"' in page and b'sound-lab.mjs' in page
    assert "media-src 'self' blob:" in headers["Content-Security-Policy"]
    sources = {}
    for name in ("sound-lab.mjs", "sound-dsp.mjs", "sound-lab.css", "audio-core.svg"):
        data, headers = call("/static/" + name)
        if name.endswith(".mjs"):
            assert headers["Content-Type"].startswith(("text/javascript", "application/javascript"))
        normal = data.replace(b"\r\n", b"\n")
        assert normal == (ROOT / "emporio/web" / name).read_bytes().replace(b"\r\n", b"\n"), name
        sources[name] = hashlib.sha256(normal).hexdigest()
    p = json.loads(call("/api/audio/program", {"root": 9, "quality": "minor", "octave": 3})[0])
    assert p["notes"] == ["A3", "C4", "E4"] and p["phase_steps"] == [19685267, 23409859, 29494575]
    assert not p["physical_device_connected"]
    assert p["validation"]["status"] == "source_matched_record"
    for i, block in enumerate(p["meter_blocks"]):
        samples = p["preview_pcm16"][i * 64:(i + 1) * 64]
        assert block["peak"] == max(map(abs, samples)) and block["energy"] == sum(x * x for x in samples)
    rules = json.loads(call("/api/music/explain", {"midi": 69, "hz": 440.0})[0])
    assert rules["mode"] == "checked_music_rules" and rules["audio_uploaded"] is False
    assert "A4" in rules["facts"][0]
    call("/api/music/explain", {"midi": 69, "hz": 100.0}, 422)
    model = json.loads(call("/api/music/explain", {"root": 0, "quality": "major", "neural": True})[0])
    assert model["facts"] and model["audio_uploaded"] is False
    report = {"status": "PASS", "scope": "HTTP delivery and typed contracts, not browser/device audio QA",
              "checked_at": datetime.now(timezone.utc).isoformat(), "origin": origin,
              "source_hashes": sources, "program_samples": len(p["preview_pcm16"]), "meter_blocks": len(p["meter_blocks"]),
              "audio_core_validation": p["validation"], "model_state": model.get("model_state", "not_requested"),
              "model": model.get("model"), "raw_audio_uploaded": False, "physical_device_tested": False,
              "browser_visual_verified": False}
    output = ROOT / "artifacts"; output.mkdir(exist_ok=True)
    (output / "public-audio-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # Runtime program contains no identities, private quote tokens or credentials.
    (output / "public-audio-program.json").write_text(json.dumps(p) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
