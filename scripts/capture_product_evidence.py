"""Capture actual loopback API commerce evidence, not a rendered UI screenshot."""
import io
import json
from pathlib import Path

import pymupdf
import zxingcpp
from PIL import Image
from fastapi.testclient import TestClient

from emporio.api import create_app
from emporio.config import Settings, ROOT
from emporio.konaet_code import render_checkout_svg

def main():
    output=ROOT/"artifacts"; output.mkdir(exist_ok=True)
    settings=Settings(state_dir=output/"evidence-state")
    with TestClient(create_app(settings)) as c:
        products=c.get('/api/shop?category_id=5&max_price_brl=1000&available_only=true').json()['products']
        c.put('/api/cart',json={'product_id':products[0]['id'],'quantity':1})
        quote=c.post('/api/checkout',json={'request_key':'evidence_quote_'+__import__('secrets').token_hex(8),'method':'pix'}).json()
        svg=c.get('/api/checkout/'+quote['id']+'/code.svg').text
        api_evidence={'status':'PASS','catalog_ids':[p['id'] for p in products],'checkout':quote,'money_collected':False}
    # A documentation code points to the public source page, not a private
    # transient quote or a nonexistent hosted checkout. Its heading is explicit.
    sample=render_checkout_svg('https://github.com/7dsol3/konaet-music','SOURCE-DEMO-0001','SOURCE / NO PAYMENT')
    docs=ROOT/'docs'/'graphics';docs.mkdir(parents=True,exist_ok=True)
    (docs/'konaet-code.svg').write_text(sample,encoding='utf-8')
    with pymupdf.open(stream=sample.encode(),filetype='svg') as doc:
        pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
        png=pix.tobytes('png')
        decoded=zxingcpp.read_barcode(Image.open(io.BytesIO(png)))
        assert decoded and decoded.text=='https://github.com/7dsol3/konaet-music'
        (docs/'konaet-code.png').write_bytes(png)
    (output/'commerce-evidence.json').write_text(json.dumps(api_evidence,indent=2)+'\n',encoding='utf-8')
    (output/'actual-checkout-code.svg').write_text(svg,encoding='utf-8')
    print('Actual API quote captured. Documentation QR independently decoded; no payment was created.')

if __name__=='__main__':main()
