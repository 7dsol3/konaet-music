"""Pinned, optional Windows CPU inference backend. No credentials or GPU needed."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(os.getenv("KONAET_MODEL_CACHE", str(ROOT / "var" / "model")))
MODEL_REV = "23749fefcc72300e3a2ad315e1317431b06b590a"
MODEL_NAME = "Qwen3-0.6B-Q8_0.gguf"
MODEL_SHA = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
MODEL_URL = f"https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/{MODEL_REV}/{MODEL_NAME}"
ENGINE_TAG = "b12024"
ENGINE_URL = f"https://github.com/ggml-org/llama.cpp/releases/download/{ENGINE_TAG}/llama-{ENGINE_TAG}-bin-win-cpu-x64.zip"
ENGINE_SHA = "a8a1bc0167c594c377255e54aab617b288a38e09efb50f39ac5bd087e4398f72"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path, expected: str) -> None:
    if target.exists() and sha(target) == expected:
        print(f"Verified cached {target.name}", flush=True)
        return
    partial = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "EmporioTechnicalCase/1.0"})
    print(f"Downloading {target.name} from its official publisher...", flush=True)
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
        total = 0
        checkpoint = 0
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            total += len(chunk)
            if total - checkpoint >= 128 * 1024 * 1024:
                print(f"  {total // (1024*1024)} MiB received", flush=True)
                checkpoint = total
            if total > 900 * 1024 * 1024:
                raise RuntimeError("Download exceeded its expected size budget")
    if sha(partial) != expected:
        raise RuntimeError("Checksum mismatch; the downloaded file will not be executed")
    partial.replace(target)


def setup() -> None:
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("This helper is for Windows x64. On other platforms, run a compatible llama-server and use the environment settings in README.md.")
    CACHE.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(CACHE).free < 2 * 1024**3:
        raise SystemExit("At least 2 GiB of free disk space is required")
    archive = CACHE / "llama-cpu.zip"
    download(ENGINE_URL, archive, ENGINE_SHA)
    destination = CACHE / "engine"
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for member in package.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise RuntimeError("Unsafe path in engine archive")
        package.extractall(destination)
    download(MODEL_URL, CACHE / MODEL_NAME, MODEL_SHA)
    manifest = {"model": "Qwen/Qwen3-0.6B-GGUF", "revision": MODEL_REV, "file": MODEL_NAME,
                "model_sha256": MODEL_SHA, "model_license": "Apache-2.0", "model_url": MODEL_URL,
                "engine": "ggml-org/llama.cpp", "engine_tag": ENGINE_TAG, "engine_sha256": ENGINE_SHA,
                "engine_license": "MIT", "engine_url": ENGINE_URL,
                "scope": "External inference provider only; not a Konaet-trained model."}
    (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Local model and engine verified. Run: python scripts/local_model.py app", flush=True)


def start_backend() -> subprocess.Popen:
    manifest = CACHE / "manifest.json"
    model = CACHE / MODEL_NAME
    binaries = list((CACHE / "engine").rglob("llama-server.exe"))
    if not manifest.exists() or not model.exists() or len(binaries) != 1:
        raise SystemExit("Run python scripts/local_model.py setup first")
    if sha(model) != MODEL_SHA:
        raise SystemExit("Model checksum changed. Refusing to load it.")
    # The archive is pinned too. Recheck extracted executable and every DLL
    # before launch; checking only the model does not authenticate the engine.
    archive = CACHE / "llama-cpu.zip"
    if not archive.exists() or sha(archive) != ENGINE_SHA:
        raise SystemExit("Engine archive checksum changed. Run setup again.")
    with zipfile.ZipFile(archive) as package:
        expected = {m.filename for m in package.infolist() if not m.is_dir()}
        actual = {p.relative_to(CACHE / "engine").as_posix() for p in (CACHE / "engine").rglob("*") if p.is_file()}
        if actual != expected:
            raise SystemExit("Engine inventory changed. Run setup again in a clean cache.")
        for name in expected:
            if sha(CACHE / "engine" / name) != hashlib.sha256(package.read(name)).hexdigest():
                raise SystemExit("Engine binary checksum changed. Refusing to execute it.")
    log = (CACHE / "server.log").open("ab")
    command = [str(binaries[0]), "-m", str(model), "--host", "127.0.0.1", "--port", "8081",
               "--ctx-size", "8192", "--parallel", "1", "--threads", str(min(os.cpu_count() or 4, 8)),
               "--jinja", "--alias", "emporio-qwen3-0.6b", "--reasoning", "off", "--no-webui"]
    child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.close()
    for _ in range(120):
        if child.poll() is not None:
            raise SystemExit("Model backend stopped. See var/model/server.log")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8081/health", timeout=1) as response:
                if response.status == 200:
                    return child
        except Exception:
            time.sleep(0.5)
    child.terminate()
    raise SystemExit("Model backend did not become ready within 60 seconds")


def configure() -> None:
    os.environ["EMPORIO_PROVIDER"] = "openai_compatible"
    os.environ["EMPORIO_MODEL_URL"] = "http://127.0.0.1:8081/v1/chat/completions"
    os.environ["EMPORIO_MODEL"] = "emporio-qwen3-0.6b"
    os.environ["EMPORIO_MODEL_TIMEOUT"] = "45"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "backend", "app"])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "setup":
        setup()
        return
    child = start_backend()
    try:
        if args.command == "backend":
            print("Model backend ready at http://127.0.0.1:8081 (Ctrl+C to stop)", flush=True)
            child.wait()
        else:
            configure()
            os.environ.setdefault("KONAET_PUBLIC_URL", f"http://127.0.0.1:{args.port}")
            from emporio.api import create_app
            import uvicorn
            print(f"Assistant ready at http://127.0.0.1:{args.port}", flush=True)
            uvicorn.run(create_app(), host="127.0.0.1", port=args.port, access_log=False)
    except KeyboardInterrupt:
        pass
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    main()
