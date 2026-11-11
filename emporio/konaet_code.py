"""KONAET Code: an original brand renderer around a standard QR matrix.

Segno supplies ISO-compatible encoding and error correction. Checkout identity,
composition and SVG are project code. The finder patterns and quiet zone remain
unobstructed; the logo is outside the symbol, not painted over payment data.
"""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

import segno


def checkout_matrix(url: str):
    parsed = urlsplit(url)
    if len(url) > 500 or parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError("A complete checkout URL is required")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Invalid checkout URL")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Public checkout codes require HTTPS")
    return segno.make_qr(url, error="h", encoding="utf-8", boost_error=False)


def render_checkout_svg(url: str, reference: str, amount: str) -> str:
    qr = checkout_matrix(url)
    module = 8
    symbol = (len(qr.matrix) + 8) * module
    width, height = symbol + 64, symbol + 220
    left, top = 32, 106
    rects = []
    for y, row in enumerate(qr.matrix):
        for x, dark in enumerate(row):
            if dark:
                rects.append(f'<rect x="{left+(x+4)*module}" y="{top+(y+4)*module}" width="8" height="8" rx="0.75"/>')
    safe_reference = escape(reference[-10:].upper())
    safe_amount = escape(amount)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">KONAET Music checkout {safe_reference}</title>
<desc id="description">Scan to open this checkout. QR code, error correction H, four-module quiet zone. This code is not a payment confirmation.</desc>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="30" fill="#f7f7ef" stroke="#d7dfcc" stroke-width="2"/>
<path d="M38 39 53 30 68 39 68 57 53 66 38 57Z M38 39 53 48 68 39 M53 48V66" fill="none" stroke="#164c41" stroke-width="3" stroke-linejoin="round"/>
<text x="82" y="48" font-family="Arial,sans-serif" font-size="24" font-weight="700" letter-spacing="3" fill="#164c41">KONAET</text>
<text x="83" y="68" font-family="Arial,sans-serif" font-size="10" letter-spacing="3" fill="#64796a">MUSIC / CHECKOUT CODE</text>
<circle cx="{width-48}" cy="49" r="8" fill="#c5f075"/>
<rect x="{left}" y="{top}" width="{symbol}" height="{symbol}" rx="12" fill="white"/>
<g fill="#143f36">{''.join(rects)}</g>
<path d="M32 {top+symbol+25}H{width-32}" stroke="#d7dfcc"/>
<text x="32" y="{top+symbol+54}" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#164c41">{safe_amount}</text>
<text x="{width-32}" y="{top+symbol+54}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" letter-spacing="1" fill="#64796a">{safe_reference}</text>
<text x="32" y="{top+symbol+80}" font-family="Arial,sans-serif" font-size="12" fill="#64796a">Scan to open. Preview, never proof of payment.</text>
</svg>'''
