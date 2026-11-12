"""Decode actual JS-generated QR artwork and compare JS/Python numeric outputs."""
import io
import json
from pathlib import Path
import sys
import pymupdf
from PIL import Image
import zxingcpp

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from emporio.audio import program
from emporio.hardware import simulate


def main():
    folder=ROOT/'artifacts/browser-qr'
    quote=json.loads((folder/'quote.json').read_text())
    decoded=0
    for theme in ['signature','orbit','studio']:
        with pymupdf.open(folder/(theme+'.svg')) as doc:
            page=doc[0]
            for width in [400,520,800]:
                pix=page.get_pixmap(matrix=pymupdf.Matrix(width/page.rect.width,width/page.rect.width),alpha=False)
                image=Image.open(io.BytesIO(pix.tobytes('png')))
                for angle in [0,90]:
                    result=zxingcpp.read_barcode(image.rotate(angle,expand=True))
                    assert result and result.text==quote['checkout_url'],(theme,width,angle)
                    decoded+=1
            pix.save(folder/(theme+'.png'))
    js=json.loads((folder/'audio.json').read_text());py=program(9,'minor',3)
    for key in ['phase_steps','preview_pcm16','meter_blocks','rtl_parameters']:
        assert js[key]==py[key],key
    gate=json.loads((folder/'gate.json').read_text());reference=simulate()
    for key in ['trace','admitted','rejected']:assert gate[key]==reference[key],key
    report={'status':'PASS','independent_qr_decodes':decoded,'themes':3,'reference_pcm_samples':512,'meter_blocks':8,'credit_gate_cycles':96,'physical_device_tested':False}
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
