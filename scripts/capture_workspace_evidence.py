"""Exercise a deployed demo using public HTTPS, two cookie jars and real QR decoding."""
import http.cookiejar
import io
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import zxingcpp
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from emporio.sovereign import verify_opening


def main():
    origin = os.environ.get("KONAET_CAPTURE_URL", "http://127.0.0.1:8034").rstrip("/")
    parsed=urllib.parse.urlsplit(origin)
    if parsed.scheme!="https" and parsed.hostname not in {"127.0.0.1","localhost"}:
        raise SystemExit("Use a trusted HTTPS demo origin or loopback")
    output=ROOT/"artifacts";output.mkdir(exist_ok=True)
    owner=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    visitor=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(opener,path,body=None,method=None,expected=200):
        headers={"User-Agent":"KonaetMusic-Verification/2.1","Accept":"application/json"}
        if body is not None:headers.update({"Content-Type":"application/json","Origin":origin})
        req=urllib.request.Request(origin+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
        try:
            with opener.open(req,timeout=45) as response:status,raw=response.status,response.read()
        except urllib.error.HTTPError as error:status,raw=error.code,error.read()
        assert status==expected, f"{path.split('/')[2:3]} expected {expected}; received {status}"
        return raw
    def api(opener,path,body=None,method=None,expected=200):
        return json.loads(call(opener,path,body,method,expected))
    health=api(owner,"/api/health");caps=api(owner,"/api/capabilities?probe_model=true")
    api(owner,"/api/session");api(visitor,"/api/session")
    wallet=api(owner,"/api/sandbox/wallet")
    products=api(owner,"/api/shop?available_only=true&sort=price_asc")["products"]
    product=next(p for p in products if p["stock"]>=2)
    api(owner,"/api/cart",{"product_id":product["id"],"quantity":2},"PUT")
    key="verified_"+secrets.token_hex(12)
    quote=api(owner,"/api/checkout",{"request_key":key,"method":"pix"})
    assert quote["checkout_url"].startswith(origin+"/checkout/") and quote["pricing_policy"]=="unit_round_v1"
    assert api(owner,"/api/checkout",{"request_key":key,"method":"pix"})==quote
    assert api(visitor,"/api/checkout/"+quote["id"])==quote
    assert b"checkout-content" in call(visitor,"/checkout/"+quote["id"])
    api(visitor,"/api/sandbox/intents",{"checkout_id":quote["id"],"request_key":"foreign_"+secrets.token_hex(10)},expected=409)
    decoded=0
    for theme in ("signature","orbit","studio"):
        svg=call(owner,"/api/checkout/"+quote["id"]+"/code.svg?theme="+theme)
        with pymupdf.open(stream=svg,filetype="svg") as doc:
            page=doc[0];png=page.get_pixmap(matrix=pymupdf.Matrix(520/page.rect.width,520/page.rect.width),alpha=False).tobytes("png")
        result=zxingcpp.read_barcode(Image.open(io.BytesIO(png)))
        assert result and result.text==quote["checkout_url"]
        with visitor.open(result.text,timeout=15) as page:assert page.status==200
        decoded+=1
        (output/("public-checkout-"+theme+".png")).write_bytes(png)
    intent=api(owner,"/api/sandbox/intents",{"checkout_id":quote["id"],"request_key":"intent_"+secrets.token_hex(12)})
    route="/api/sandbox/intents/"+intent["id"]+"/confirm"
    final=api(owner,route,{"decision":"approve"})
    assert final==api(owner,route,{"decision":"approve"})
    assert final["seal_verified"] and final["funds_moved"] is False and verify_opening(final["sovereign_opening"])
    after=api(owner,"/api/sandbox/wallet")
    assert wallet["balance_cents"]-after["balance_cents"]==quote["subtotal_cents"]
    research=api(owner,"/api/research",{"query":"quantum computing","scope":"knowledge","synthesize":False})
    assert research["sources"] and any(p["status"]=="ok" for p in research["providers"])
    hardware=api(owner,"/api/hardware/simulate",{"cycles":96,"capacity":8,"burst":40,"refill_every":5})
    assert len(hardware["trace"])==96 and not hardware["physical_device_connected"]
    api(owner,"/api/session",method="DELETE")
    api(owner,"/api/sandbox/intents/"+intent["id"],expected=404)
    report={"schema":"konaet.music.public-verification.v1","checked_at":datetime.now(timezone.utc).isoformat(),"origin":origin,"status":"PASS",
            "version":health["version"],"model_connection":caps["agent"]["state"],"two_client_quote_open":True,"qr_themes_decoded_and_opened":decoded,
            "foreign_test_spend_rejected":True,"duplicate_confirmation_single_debit":True,"server_seal_verified":True,"sovereign_opening_verified":True,
            "funds_moved":False,"real_bank_payment":False,"research_sources":len(research["sources"]),"hardware_logical_cycles":96,
            "hardware_validation":hardware["validation"],"physical_hardware_connected":False,"session_reset_revokes_wallet":True,
            "browser_layout_verified":False,"microphone_verified":False,"availability":"Local Python/model host and temporary tunnel must remain running"}
    (output/"public-workspace-verification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report))


if __name__=="__main__":main()
