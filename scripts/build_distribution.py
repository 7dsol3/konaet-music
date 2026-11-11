"""Build from fresh source staging and reject missing or stale runtime files."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent


def runtime_sources():
    sources = {}
    for path in (ROOT / "emporio").rglob("*"):
        if path.is_file() and (
            path.suffix == ".py"
            or path.parent == ROOT / "emporio/web"
            or path.name in {"KONAET_LICENSE", "SOVEREIGN_LICENSE"}
            or path.parent == ROOT / "emporio/gateware" and path.suffix in {".sv", ".json"}
        ):
            sources[path.relative_to(ROOT).as_posix()] = path
    for path in (ROOT / "data").iterdir():
        if path.is_file() and (path.suffix in {".csv", ".pdf"} or path.name == "__init__.py"):
            sources["konaet_music_data/" + path.name] = path
    return sources


def verify_wheel_contents(wheel):
    sources = runtime_sources()
    with ZipFile(wheel) as archive:
        packaged = [name for name in archive.namelist() if name.startswith(("emporio/", "konaet_music_data/"))]
        assert len(packaged) == len(set(packaged)), "Duplicate runtime archive entries"
        extra = sorted(set(packaged) - sources.keys())
        missing = sorted(sources.keys() - set(packaged))
        assert not extra and not missing, f"Runtime inventory mismatch: extra={extra}, missing={missing}"
        for name, path in sources.items():
            assert archive.read(name) == path.read_bytes(), f"Runtime content mismatch: {name}"
    return len(sources)


def build_wheel(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="konaet-music-build-") as folder:
        staging = Path(folder) / "source"
        staging.mkdir()
        for name in ("pyproject.toml", "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(ROOT / name, staging / name)
        for name, source in runtime_sources().items():
            target = staging / ("data/" + name.removeprefix("konaet_music_data/") if name.startswith("konaet_music_data/") else name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        wheels = Path(folder) / "wheels"
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", "--disable-pip-version-check", "--no-deps",
             "--no-build-isolation", "--wheel-dir", str(wheels), str(staging)],
            check=True, timeout=180, env=os.environ.copy(),
        )
        produced = list(wheels.glob("konaet_music-*.whl"))
        assert len(produced) == 1, "Expected one KONAET Music distribution"
        verify_wheel_contents(produced[0])
        destination = output / produced[0].name
        shutil.copy2(produced[0], destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(build_wheel(args.out_dir))
