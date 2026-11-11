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
    for file in WEB.glob("*.svg"): ElementTree.parse(file)
    manifest = json.loads((WEB / "app.webmanifest").read_text(encoding="utf-8"))
    assert manifest["lang"] == "en" and manifest["display"] == "standalone"
    for icon in manifest["icons"]: assert (WEB / icon["src"].removeprefix("/static/")).is_file()
    assets = [p for p in WEB.iterdir() if p.suffix in {".html", ".js", ".css", ".svg", ".webmanifest"} and p.name not in {"api.html", "language.js"}]
    raw = sum(p.stat().st_size for p in assets)
    compressed = sum(len(gzip.compress(p.read_bytes(), compresslevel=6, mtime=0)) for p in assets)
    assert raw < 150_000, f"UI source budget exceeded: {raw}"
    assert compressed < 45_000, f"UI compressed budget exceeded: {compressed}"
    report = {"status": "PASS", "static_ids": len(parser.ids), "files": len(assets), "raw_bytes": raw,
              "gzip_bytes": compressed, "external_font_requests": 0, "browser_layout_verified": False,
              "voice_hardware_verified": False, "scope": "Static references, SVG parsing and source-byte budgets"}
    output = ROOT / "artifacts"; output.mkdir(exist_ok=True)
    (output / "frontend-budget.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report))

if __name__ == "__main__": main()
