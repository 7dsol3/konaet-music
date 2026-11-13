"""Build the standalone GitHub Pages demo. No Python API is needed at runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "deploy/browser"
WEB = ROOT / "emporio/web"


def export_catalog():
    from emporio.config import Settings
    from emporio.policies import CARDS
    from emporio.service import AgentService
    with tempfile.TemporaryDirectory() as folder:
        agent = AgentService(Settings(state_dir=Path(folder)))
        products = agent.commerce.catalog(sort="price_asc")["products"]
        public = {"products": products, "policies": [
            {"topic": topic, "title": title, "summary": summary, "pages": pages}
            for topic, (title, pages, summary) in CARDS.items()]}
        fingerprint = hashlib.sha256(json.dumps(public, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        public.update(schema="konaet.browser-catalog.v1", fingerprint=fingerprint)
        return public


def build(out: Path, base="/konaet-music/"):
    if not re.fullmatch(r"/(?:[a-zA-Z0-9_-]+/)*", base):
        raise ValueError("Base must be a rooted directory path such as /konaet-music/")
    out = out.resolve()
    if not out.is_relative_to((ROOT / "dist").resolve()) or out == (ROOT / "dist").resolve():
        raise ValueError("Build output must be a subdirectory of this repository's dist/")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    static = out / "static"
    static.mkdir(exist_ok=True)
    def paths(text):
        return text.replace('"/static/', '"' + base + 'static/').replace("'/static/", "'" + base + "static/")
    for source in WEB.iterdir():
        if source.suffix in {".webp", ".png", ".woff2"} or source.name == "FONT-LICENSE.txt":
            shutil.copyfile(source, static / source.name)
            continue
        if source.name!='service-worker.js' and source.suffix in {".css", ".js", ".mjs", ".svg"}:
            (static / source.name).write_text(paths(source.read_text(encoding="utf-8")), encoding="utf-8")
    for name in ("bootstrap.js", "browser-runtime.mjs"):
        shutil.copyfile(SOURCE / name, static / name)
    shutil.copytree(SOURCE / "vendor", static / "vendor", dirs_exist_ok=True)
    shutil.copyfile(SOURCE / "catalog.json", out / "catalog.json")
    shutil.copyfile(ROOT / "data/políticas_da_loja.pdf", out / "manual.pdf")
    bootstrap = f'<script src="{base}static/vendor/qrcode.js" defer></script><script src="{base}static/bootstrap.js" defer></script>'
    for name, destination in (("index.html", "index.html"), ("sound-lab.html", "sound-lab/index.html"), ("api.html", "docs/index.html")):
        text = paths((WEB / name).read_text(encoding="utf-8"))
        text = text.replace('href="/sound-lab"', f'href="{base}sound-lab/"').replace('href="/docs"', f'href="{base}docs/"').replace('href="/"', f'href="{base}"')
        text = text.replace('href="/manual"',f'href="{base}manual.pdf"').replace('PYTHON × SYSTEMVERILOG','BROWSER REFERENCE × SYSTEMVERILOG')
        text = text.replace(f'<script src="{base}static/app.js"', bootstrap + f'<script src="{base}static/app.js"') if name == "index.html" else text.replace('<script src=', bootstrap + '<script src=', 1) if name == "sound-lab.html" else text
        text = text.replace('class="demo-pill"', 'class="demo-pill" data-browser-notice')
        text = text.replace('Every amount comes from the catalog.', 'Every amount is recalculated from the bundled catalog. This is an unsigned browser quote.')
        text = text.replace('A Python reference is available.', 'A browser reference is available.')
        text = text.replace('Coaching sends only the note or chord estimate you choose.','Music coaching uses local rules; audio and estimates stay in this browser.')
        text = text.replace('BROWSER DSP · OPTIONAL MODEL COACH', 'BROWSER DSP · LOCAL MUSIC RULES')
        text = text.replace('<button id="verify-button">Verify an order</button>','<button id="verify-button" disabled title="Available in the downloadable Python application">Orders: local app only</button>')
        text = text.replace('<b>Receipt export</b>','<b>Local app only</b>')
        if name == "api.html":
            text = text.replace('The Python API serves', 'The downloadable Python application serves').replace('href="/openapi.json"', 'href="https://github.com/7dsol3/konaet-music/blob/main/emporio/api.py"')
            text = text.replace('Read the complete OpenAPI schema', 'Read the Python API source')
        target=out / destination; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    # JS source helpers remain unchanged in the Python app. Only the standalone
    # build rewrites physical paths and presents its different trust boundary.
    app=static / "app.js"
    text=app.read_text(encoding="utf-8").replace('"/manual#page=', '"' + base + 'manual.pdf#page=')
    text=text.replace('"/service-worker.js"', '"' + base + 'service-worker.js"')
    app.write_text(text, encoding="utf-8")
    workspace=static / "workspace.js"
    text=workspace.read_text(encoding="utf-8")
    text=text.replace('"Session wallet, server-calculated quotes and sealed test receipts. No real money moves."','"Local browser credits, recomputed unsigned quotes and editable demo receipts. No money moves."')
    text=text.replace('"An opening compatible with SocialReceiptRegistry.ko. Not submitted or finalized on a validator network."','"Sovereign openings and server seals require the downloadable Python application."')
    text=text.replace('"Request limits active"','"Static hosting"').replace('c.protection.max_inflight_per_process+" concurrent requests per process; bounded bodies and read time. Internet DDoS edge: not provisioned."','"GitHub Pages serves this demo. There is no Python API or inference server behind this page."')
    text=text.replace('"The server seal is not an independent bank certificate. Keep the Sovereign opening private; no network finalization has occurred."','"This editable browser receipt is a demonstration, without a server seal, bank certificate or network finalization."')
    workspace.write_text(text, encoding="utf-8")
    manifest=json.loads((WEB / "app.webmanifest").read_text(encoding="utf-8"))
    manifest.update(id=base,scope=base,start_url=base)
    for icon in manifest["icons"]:icon["src"]=base+"static/"+Path(icon["src"]).name
    (static / "app.webmanifest").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/'.nojekyll').touch()
    assets=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and not p.name.startswith('.') and p.name not in {'service-worker.js','pages-build.json'})
    hashes={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in assets}
    revision=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
    worker='''"use strict";
const PREFIX=%s,CACHE=PREFIX+%s,ASSETS=%s;
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==self.location.origin)return;let key=u.pathname;if(key===%s)key+= 'index.html';if(key.endsWith('/sound-lab/'))key+='index.html';if(key.endsWith('/docs/'))key+='index.html';if(!ASSETS.includes(key))return;e.respondWith(fetch(e.request).then(r=>r.ok?r:caches.match(key).then(c=>c||r)).catch(()=>caches.match(key).then(r=>r||Response.error())));});
'''%(json.dumps('konaet-browser:'+base+':'),json.dumps(revision),json.dumps([base+n for n in assets]),json.dumps(base))
    (out/"service-worker.js").write_text(worker,encoding="utf-8")
    report={"schema":"konaet.pages-build.v1","mode":"standalone_browser_demo","base":base,"files":hashes,"revision":revision,"customer_records_included":False,"api_server_required":False}
    (out/"pages-build.json").write_text(json.dumps(report,indent=2)+'\n',encoding="utf-8")
    print(f"Built browser demo: {out}, {len(hashes)} files; no Python backend at runtime")
    return out


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,default=ROOT/'dist/pages')
    parser.add_argument('--base',default='/konaet-music/')
    parser.add_argument('--refresh-catalog',action='store_true')
    args=parser.parse_args()
    if args.refresh_catalog:
        (SOURCE/'catalog.json').write_text(json.dumps(export_catalog(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    build(args.out_dir,args.base)
