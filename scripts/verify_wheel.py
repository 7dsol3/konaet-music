"""Build and exercise the installed distribution away from the checkout."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile
from build_distribution import build_wheel, verify_wheel_contents

ROOT = Path(__file__).resolve().parent.parent

def run(*args, **kwargs):
    subprocess.run([sys.executable, *args], check=True, timeout=180, **kwargs)

def main():
    with tempfile.TemporaryDirectory(prefix="konaet-music-package-") as folder:
        temporary = Path(folder); wheels = temporary / "wheels"; target = temporary / "installed"
        wheel = build_wheel(wheels)
        runtime_files = verify_wheel_contents(wheel)
        with ZipFile(wheel) as archive:
            names = archive.namelist()
            assert len([n for n in names if n.startswith("konaet_music_data/") and n.endswith(".csv")]) == 6
            assert len([n for n in names if n.startswith("konaet_music_data/") and n.endswith(".pdf")]) == 1
            assert "emporio/web/glass.css" in names and "emporio/web/service-worker.js" in names
        # Regression: an old build cache must never silently add retired assets.
        polluted = temporary / "stale-runtime.whl"
        with ZipFile(wheel) as original, ZipFile(polluted, "w") as probe:
            for info in original.infolist():
                probe.writestr(info, original.read(info.filename))
            probe.writestr("emporio/web/stale-build-probe.js", b"retired asset")
        try:
            verify_wheel_contents(polluted)
        except AssertionError as error:
            assert "stale-build-probe.js" in str(error)
        else:
            raise AssertionError("Stale runtime asset was accepted")
        run("-m", "pip", "install", "--disable-pip-version-check", "--no-deps", "--target", str(target), str(wheel))
        code = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from emporio.config import Settings
from emporio.service import AgentService
s=Settings(state_dir=Path(sys.argv[2]))
assert s.data_dir.is_dir()
a=AgentService(s)
assert a.data_report['counts']['products']==65
assert a.turn('How much is the Takamine GD20?')['results'][0]['products']
print(json.dumps({'installed_smoke':'PASS','products':65,'data_packaged':True}))
'''
        env = {k:v for k,v in os.environ.items() if not k.startswith(("EMPORIO_", "KONAET_", "PYTHONPATH"))}
        run("-c", code, str(target), str(temporary / "state"), cwd=temporary, env=env)
    output=ROOT/"artifacts";output.mkdir(exist_ok=True)
    (output/"package-smoke.json").write_text(json.dumps({"status":"PASS","isolated_install":True,"products":65,"runtime_source_files_verified":runtime_files,"stale_runtime_rejected":True})+"\n",encoding="utf-8")

if __name__ == "__main__": main()
