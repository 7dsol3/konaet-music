"""Check source references, language, SVG structure and transfer-size budgets.

This is source-level validation, not browser layout, accessibility certification,
voice hardware verification or a measured frame-rate claim.
"""
import gzip
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "emporio" / "web"
SOUND = {"sound-lab.html", "sound-lab.css", "sound-glass.css", "sound-lab.mjs", "sound-dsp.mjs", "audio-core.svg"}

class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.assets = []; self.lang = None; self.inline_scripts = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.append(a["id"])
        if tag == "html": self.lang = a.get("lang")
        if tag == "script" and not a.get("src"): self.inline_scripts += 1
        for key in ("src", "href"):
            target = a.get(key, "")
            if target.startswith("/static/"): self.assets.append(target.removeprefix("/static/"))

def main():
    parser = SourceParser(); parser.feed((WEB / "index.html").read_text(encoding="utf-8"))
    assert parser.lang == "en" and parser.inline_scripts == 0
    assert not [i for i,n in Counter(parser.ids).items() if n > 1], "Duplicate static DOM IDs"
    for target in parser.assets: assert (WEB / target).is_file(), target
    script = (WEB / "app.js").read_text(encoding="utf-8")
    for target in re.findall(r'\$\("#([a-z][a-z0-9-]*)"\)', script): assert target in parser.ids, target
    assert "innerHTML" not in script and "eval(" not in script
    workspace = (WEB / "workspace.js").read_text(encoding="utf-8")
    for target in re.findall(r'q\("#([a-z][a-z0-9-]*)"\)',workspace):
        assert target in parser.ids,target
    assert "innerHTML" not in workspace and "eval(" not in workspace
    shell = (WEB / "studio-shell.js").read_text(encoding="utf-8")
    for target in re.findall(r'q\("#([a-z][a-z0-9-]*)"\)', shell):
        assert target in parser.ids, target
    assert "innerHTML" not in shell and "eval(" not in shell
    for file in WEB.glob("*.svg"): ElementTree.parse(file)
    for file in WEB.glob("*.css"):
        for ref in re.findall(r'url\([\'"]?([^\'"\)]+)[\'"]?\)', file.read_text(encoding="utf-8")):
            if ref.startswith(("data:", "https:", "#")): continue
            target = ref.split("#")[0].split("?")[0]
            assert (WEB / target.removeprefix("/static/")).is_file(), (file.name, target)
    sound_parser = SourceParser(); sound_parser.feed((WEB / "sound-lab.html").read_text(encoding="utf-8"))
    assert sound_parser.lang == "en" and sound_parser.inline_scripts == 0
    assert not [i for i,n in Counter(sound_parser.ids).items() if n > 1]
    for target in sound_parser.assets: assert (WEB / target).is_file(), target
    sound_script = (WEB / "sound-lab.mjs").read_text(encoding="utf-8")
    for target in re.findall(r"q\('([a-z][a-z0-9-]*)'\)", sound_script): assert target in sound_parser.ids, target
    assert "innerHTML" not in sound_script and "eval(" not in sound_script
    assert not any(name in parser.assets for name in SOUND), "Sound Lab must stay lazy, on its own page"
    manifest = json.loads((WEB / "app.webmanifest").read_text(encoding="utf-8"))
    assert manifest["lang"] == "en" and manifest["display"] == "standalone"
    for icon in manifest["icons"]: assert (WEB / icon["src"].removeprefix("/static/")).is_file()
    assets = [p for p in WEB.iterdir() if p.suffix in {".html", ".js", ".mjs", ".css", ".svg", ".webmanifest"} and p.name not in {"api.html", "language.js"} | SOUND]
    raw = sum(p.stat().st_size for p in assets)
    compressed = sum(len(gzip.compress(p.read_bytes(), compresslevel=6, mtime=0)) for p in assets)
    # The glass studio adds explicit view navigation and a small room image.
    # Track the bitmap separately instead of hiding it in the text transfer budget.
    raster = sum(p.stat().st_size for p in WEB.iterdir() if p.suffix in {".webp", ".png"})
    fonts = list(WEB.glob("*.woff2"))
    font_bytes = sum(p.stat().st_size for p in fonts)
    assert font_bytes < 30_000, f"Local font budget exceeded: {font_bytes}"
    assert all(p.read_bytes()[:4] == b"wOF2" for p in fonts), "Invalid WOFF2 font"
    assert not fonts or "SIL OPEN FONT LICENSE" in (WEB / "FONT-LICENSE.txt").read_text(encoding="utf-8")
    assert raw < 170_000, f"UI source budget exceeded: {raw}"
    assert compressed < 50_000, f"UI compressed budget exceeded: {compressed}"
    assert raster < 30_000, f"UI raster budget exceeded: {raster}"
    lazy_raw = sum((WEB / name).stat().st_size for name in SOUND)
    lazy_gzip = sum(len(gzip.compress((WEB / name).read_bytes(), compresslevel=6, mtime=0)) for name in SOUND)
    assert lazy_raw < 70_000 and lazy_gzip < 22_000, "Sound Lab lazy budget exceeded"
    report = {"status": "PASS", "static_ids": len(parser.ids), "files": len(assets), "raw_bytes": raw,
              "gzip_bytes": compressed, "raster_bytes": raster, "font_bytes": font_bytes, "external_font_requests": 0, "browser_layout_verified": False,
              "voice_hardware_verified": False, "sound_lab_lazy": {"files": len(SOUND), "raw_bytes": lazy_raw, "gzip_bytes": lazy_gzip},
              "scope": "Static references, SVG parsing and separate home / lazy Sound Lab source-byte budgets"}
    output = ROOT / "artifacts"; output.mkdir(exist_ok=True)
    (output / "frontend-budget.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report))

if __name__ == "__main__": main()
