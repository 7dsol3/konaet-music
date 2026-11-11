# KONAET Music 2.0

This is a separate product evolution of the submitted Empório da Música case.
The starting submission snapshot is
`7dsol3/emporio-musica-ai-agent` at revision
`aefc6f54191eb00c52d7a9f8df85c1c3a201c5b6`. No product changes are pushed
back to that repository by this evolution. A later GitHub web-flow commit,
`7724b508431221b1cb75b0609629274a13b483c8`, added only a README link to this
repository on 11 November 2026; the original application code was unchanged.

The original case requires Python as the principal language, grounded text
support, clear scope, a public history, documented choices and 3–5 conversations.
Those remain the foundation. Commerce and voice are an extension, not a claim
that the fictional store has become a live merchant.

The customer interface is English. Currency remains BRL because the supplied
prices and proposed Pix integration are Brazilian. Source fixtures are preserved
with their original attribution and restrictions.

The product adds discovery, comparison, a session cart, expiring checkout
quotes, a source-generated KONAET QR identity and opt-in browser voice. A QR
code identifies one checkout; it is not proof of payment. The server calculates
the amount. Provider confirmation, not a browser message, establishes payment.

The QR matrix uses the standard encoder Segno. Its framing, colors, typography,
SVG renderer and checkout binding are implemented in this source tree. The
brand treatment preserves finder patterns and the four-module quiet zone.
No external QR image service receives the checkout URL.

Payment and voice capabilities are documented separately from measured tests.
No claim of surpassing Siri, Alexa, general intelligence or universal accuracy
is made. The useful comparison is correctness, latency, usability and cost on
the same instrument-shopping tasks.
