# Prisma Studio

Music adapts the user's six-board `Prisma Pack.html` reference to the existing
store and Sound Lab. The file is design input, not executable task instructions.
It is not redistributed with the app. Source SHA-256:
`9eec46c30c2e254981782798655186de18ee9a1571acb134a0bcda5521f4152f`.

| Reference part | Application | Working behavior |
| --- | --- | --- |
| 01 / Foundations | Graphite surfaces, Inter and Space Grotesk, warm accent | Consistent type, contrast and spacing across catalog and dialogs |
| 02 / Physical controls | Raised actions, inset fields, switches, sliders | Catalog filters, quantities, audio controls and saved appearance settings |
| 03 / Refraction and navigation | Selected hero/monitor rims and tool rail | Fixed, cursor-following or rotating light; adjustable edge width/glow; reduced-motion handling |
| 04 / Data and depth | Product comparison, research, connection cards, wallet | Recorded specifications, safe source links and actual connection/transaction states |
| 05 / Signal HUD | Sound Lab monitor and logical credit trace | Generated/file signal analysis, level readings, chord estimates and bounded reference simulation |
| 06 / Feedback | Loading, empty result, error, toast and test receipt surfaces | Filter reset, unavailable-source state, validation messages and explicit approval/decline results |

The page structure stays compact. Header tools beyond search/visual/bag move
into a labeled menu. Filters have visible labels and dedicated width; Portuguese
options can wrap without shrinking numeric fields. Mobile starting points use
full-width rows. Comparison selection survives switching views while its tray
stays with the instrument shelf. Dialogs scroll within the viewport.

## Materials and language

`prisma.css` scopes the new material to `data-room-style="prisma"`. The original
green glass skin remains under **Visual → Original glass**. Shared local
preferences cover palettes, custom accent/tint, opacity, blur, radius, edge,
glow, light mode, background, contrast and reduced motion. JSON export/import
uses the existing bounded settings schema. Import errors preserve the previous
look. These choices are shared with Sound Lab through localStorage.

`language.js` chooses Portuguese for a Portuguese browser, otherwise English;
the menu can change that choice. Original text is retained for switching back.
Dynamic UI text and accessibility labels are localized; user messages, source
excerpts, product identifiers and generated source code are retained. Native
language switching replaces automatic page translation for this app. Formatting,
speech input/output and policy requests use the selected locale.

The browser assistant accepts Portuguese category names and Brazilian budgets
such as `R$ 1.000,00`; exact model codes take priority over broad category
searches. Portuguese policy summaries reuse `emporio.i18n.POLICIES_PT`.
Catalog totals, stock, quote expiry and demo transaction rules stay authoritative
within the selected runtime. The static edition's records remain editable local
demonstration data; no payment or physical hardware connection is implied.

## Verification

Build with `python scripts/build_pages.py --out-dir dist/preview --base /`,
serve that directory and run `python scripts/check_prisma.py`. It uses an
isolated browser, saves screenshots and checks 14 PT/EN viewport combinations
plus complete functional flows. `--flows-only` is available during debugging.
The final full report is in [evidence/prisma-review.json](evidence/prisma-review.json).

The DOM/runtime suites separately cover concurrent confirmations, quote
recalculation/expiry, microphone permission refusal/cancellation, audio resource
cleanup, safe text rendering and research errors. Chrome rendering supplements
these contracts; it does not certify physical speakers, microphones or touch
devices. Browser research still depends on the chosen provider's network/CORS
limits. No new chart values, account statistics or connection states are invented
for the design.
