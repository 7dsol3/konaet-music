"""Build and exercise the installed distribution away from the checkout."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent

def run(*args, **kwargs):
    subprocess.run([sys.executable, *args], check=True, timeout=180, **kwargs)

def main():
    with tempfile.TemporaryDirectory(prefix="konaet-music-package-") as folder:
        temporary = Path(folder); wheels = temporary / "wheels"; target = temporary / "installed"
        run("-m", "pip", "wheel", "--disable-pip-version-check", "--no-deps", "--no-build-isolation", "--wheel-dir", str(wheels), str(ROOT))
        wheel = next(wheels.glob("konaet_music-*.whl"))
        with ZipFile(wheel) as archive:
            names = archive.namelist()
            assert len([n for n in names if n.startswith("konaet_music_data/") and n.endswith(".csv")]) == 6
            assert len([n for n in names if n.startswith("konaet_music_data/") and n.endswith(".pdf")]) == 1
            assert "emporio/web/glass.css" in names and "emporio/web/service-worker.js" in names
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
    (output/"package-smoke.json").write_text(json.dumps({"status":"PASS","isolated_install":True,"products":65})+"\n",encoding="utf-8")

if __name__ == "__main__": main()
