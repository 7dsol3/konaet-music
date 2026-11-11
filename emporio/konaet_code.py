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


def render_checkout_svg(url: str, reference: str, amount: str, theme: str = "signature") -> str:
    themes = {"signature": ("#f7f7ef", "#143f36", "#d7dfcc"),
              "orbit": ("#eef3fb", "#172f4c", "#c7d6e9"),
              "studio": ("#fff7e9", "#3e3425", "#e1cfaf")}
    if theme not in themes:
        raise ValueError("Choose signature, orbit or studio code artwork")
    paper, ink, border = themes[theme]
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
    ornament = f'<circle cx="{width-48}" cy="49" r="8" fill="#c5f075"/>'
    if theme == "orbit":
        ornament = f'<g transform="translate({width-57} 50)" fill="none" stroke="#658aaf"><ellipse rx="29" ry="13" transform="rotate(-28)"/><ellipse rx="13" ry="29" transform="rotate(-28)"/><circle r="5" fill="#a8c9ed" stroke="none"/><circle cx="24" cy="-11" r="4" fill="#e3b773" stroke="none"/></g>'
    elif theme == "studio":
        ornament = f'<g transform="translate({width-66} 48) rotate(-26)" fill="none" stroke="#9b7545" stroke-width="2"><path d="M-8 4C-27-6-27 18-18 24-6 34 15 23 8 9L6 4V-23H-4V5Z" fill="#efdfbd"/><circle cx="-7" cy="13" r="5"/><path d="M1-22V21M-6-19H6M-6-13H6"/><path d="M-15 24H3"/></g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">KONAET Music checkout {safe_reference}</title>
<desc id="description">Scan to open this checkout. QR code, error correction H, four-module quiet zone. This code is not a payment confirmation.</desc>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="30" fill="{paper}" stroke="{border}" stroke-width="2"/>
<path d="M38 39 53 30 68 39 68 57 53 66 38 57Z M38 39 53 48 68 39 M53 48V66" fill="none" stroke="#164c41" stroke-width="3" stroke-linejoin="round"/>
<text x="82" y="48" font-family="Arial,sans-serif" font-size="24" font-weight="700" letter-spacing="3" fill="#164c41">KONAET</text>
<text x="83" y="68" font-family="Arial,sans-serif" font-size="10" letter-spacing="3" fill="#64796a">MUSIC / CHECKOUT CODE</text>
{ornament}
<rect x="{left}" y="{top}" width="{symbol}" height="{symbol}" rx="12" fill="white"/>
<g fill="{ink}">{''.join(rects)}</g>
<path d="M32 {top+symbol+25}H{width-32}" stroke="#d7dfcc"/>
<text x="32" y="{top+symbol+54}" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#164c41">{safe_amount}</text>
<text x="{width-32}" y="{top+symbol+54}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" letter-spacing="1" fill="#64796a">{safe_reference}</text>
<text x="32" y="{top+symbol+80}" font-family="Arial,sans-serif" font-size="12" fill="#64796a">Scan to open. Preview, never proof of payment.</text>
</svg>'''
