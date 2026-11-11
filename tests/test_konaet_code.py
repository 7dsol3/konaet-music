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
])
@pytest.mark.parametrize("width", [260, 520])
@pytest.mark.parametrize("rotation", [0, 90, 180])
def test_independent_decoder_reads_actual_branded_svg(url, width, rotation):
    svg = render_checkout_svg(url, "a"*32, "BRL 2,089.05")
    ET.fromstring(svg)
    with pymupdf.open(stream=svg.encode(), filetype="svg") as document:
        page = document[0]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(width/page.rect.width, width/page.rect.width), alpha=False)
        image = Image.open(io.BytesIO(pix.tobytes("png"))).rotate(rotation, expand=True)
    result = zxingcpp.read_barcode(image)
    assert result is not None and result.text == url
    assert checkout_matrix(url).error == "H"


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
