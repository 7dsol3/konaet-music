# Checkout codes and future merchant payments

## Implemented in 2.0

The bag, comparison, server quote, idempotent quote retry and source-generated
SVG QR work without a payment provider. Every checkout receives a random
192-bit reference, a frozen product/amount snapshot and a fifteen-minute expiry.
The code opens that preview. It is not a Pix payload and never indicates paid.

The backend is authoritative for current recorded prices, quantities and the
no-stacking discount rule. The browser cannot submit a total. A quote contains
only products, prices and method; private customer/session identifiers are not
included. Anyone with the capability URL can view it until expiry, so share it
only when that public product selection may be shared.

The implementation does not reserve or decrement stock and excludes shipping.
There is no payment-create, mark-paid or refund endpoint. No payment environment
flag silently turns this fictional dataset into a live merchant. Production
keys and payer details are not requested for this demonstration.

The UI clearly distinguishes a KONAET checkout-link code from a bank-scannable
Pix request. Styling is project-authored; the standard encoding is supplied by
[Segno](https://segno.readthedocs.io/en/latest/api.html). Finder patterns and the
four-module quiet zone remain intact. A ZXing decoder reads the actual SVG
rendered to pixels at two sizes and three orientations in tests.

## Researched merchant path, not yet implemented

For a Brazilian store, Mercado Pago's Checkout API Orders documentation supports
creating an online Pix order. The backend sends the amount, external reference,+payer data and payment method with an idempotency key. The provider returns the
bank payment code/image and its status. This code must come from the authorized
provider, rather than deriving a supposed Pix charge from a shopping URL.
[Official Pix integration](https://www.mercadopago.com.br/developers/en/docs/checkout-api-orders/payment-integration/websites/pix).

Required work before collecting money:

1. Merchant account, approved catalog/fulfillment integration and sandbox credentials.
2. Verified shopper identity and explicit confirmation of final items, shipping and total.
3. Transactional reservation policy and one persisted payment attempt per idempotency key.
4. Backend provider adapter; private keys and payer data stay outside model prompts.
5. Authenticated webhook validation, event deduplication and server API reconciliation
   of external reference, currency, amount and final status before local fulfillment.
6. Tests for pending, expired, duplicate, delayed, mismatched and reversed payments.
7. Merchant review and live rollout separated from the fictional fixture mode.

Provider callbacks are not interchangeable across products. Use the notification
contract for the chosen **online Orders** integration; do not copy an in-person
QR example and assume the same signature behavior. The official notification
guide defines signature verification and event processing.
[Orders notifications](https://www.mercadopago.com.br/developers/en/docs/checkout-api-orders/notifications),
[Pix test purchase](https://www.mercadopago.com.br/developers/en/docs/checkout-api-orders/integration-test/pix).

A browser success redirect is not payment confirmation. Displaying a beautiful
QR, receiving a callback or recording a hash is not, by itself, authorization to
ship. The merchant's authoritative payment state must drive that decision.

This research was checked on 11 November 2026. No merchant sandbox account was
connected and no provider payment request or real charge was created.
