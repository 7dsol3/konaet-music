import io
import xml.etree.ElementTree as ET

import pymupdf
import pytest
import zxingcpp
from PIL import Image

from emporio.konaet_code import render_checkout_svg, checkout_matrix


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8000/checkout/abcdefghijklmnopqrstuvwxyzABCDEF",
    "https://music.konaet.example/checkout/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
    "https://emily-catalyst-joint-james.trycloudflare.com/checkout/abcdefghijklmnopqrstuvwxyzABCDEF",
])
@pytest.mark.parametrize("width", [260, 520])
@pytest.mark.parametrize("rotation", [0, 90, 180])
@pytest.mark.parametrize("theme", ["signature", "orbit", "studio"])
def test_independent_decoder_reads_actual_branded_svg(url, width, rotation, theme):
    svg = render_checkout_svg(url, "a"*32, "BRL 2,089.05", theme)
    ET.fromstring(svg)
    with pymupdf.open(stream=svg.encode(), filetype="svg") as document:
        page = document[0]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(width/page.rect.width, width/page.rect.width), alpha=False)
        image = Image.open(io.BytesIO(pix.tobytes("png"))).rotate(rotation, expand=True)
    result = zxingcpp.read_barcode(image)
    assert result is not None and result.text == url
    assert checkout_matrix(url).error == "H"


def test_unknown_artwork_is_not_interpolated_into_svg():
    with pytest.raises(ValueError):render_checkout_svg("https://example.org/checkout/"+"a"*32,"a"*32,"BRL 1.00",'<script>bad</script>')


@pytest.mark.parametrize("theme,art",[("signature","circuit"),("orbit","constellation"),("studio","ribbon")])
def test_custom_art_preserves_every_dark_function_module_exactly(theme,art):
    from segno.consts import TYPE_DATA_DARK
    url="https://music.konaet.example/checkout/"+"z"*32
    qr=checkout_matrix(url)
    types=[list(row) for row in qr.matrix_iter(border=0,verbose=True)]
    expected={(str(32+(x+4)*8),str(106+(y+4)*8),str(kind)) for y,row in enumerate(types) for x,kind in enumerate(row) if kind >> 8 and kind!=TYPE_DATA_DARK}
    root=ET.fromstring(render_checkout_svg(url,"z"*32,"BRL 1.00",theme))
    actual={(r.attrib['x'],r.attrib['y'],r.attrib['data-function']) for r in root.iter() if 'data-function' in r.attrib}
    assert actual==expected
    assert any(n.attrib.get('data-art')==art for n in root.iter())


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://evil.example/checkout/id", "https://user:password@example.com/", "https://example.com/#fragment"])
def test_code_refuses_unsafe_or_incomplete_targets(url):
    with pytest.raises(ValueError):
        checkout_matrix(url)


def test_brand_values_are_escaped_and_symbol_has_no_logo_overlay():
    svg = render_checkout_svg("https://music.konaet.example/checkout/"+"a"*32, '<script>alert(1)</script>', '<svg onload="bad">')
    root = ET.fromstring(svg)
    assert not root.findall(".//{http://www.w3.org/2000/svg}script")
    assert not root.findall(".//{http://www.w3.org/2000/svg}image")
    assert "&lt;svg" in svg and "four-module quiet zone" in svg
