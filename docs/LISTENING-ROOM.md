# The KONAET listening room

The store is organized as a workspace: a floating translucent frame, a tool
rail, a searchable instrument shelf and a small panel of useful starting points.
Discover, Research and Guide are separate views of the same page. Their
navigation changes visibility; it does not replace the commerce or research
engines. The Sound Lab remains a separate page and keeps its local audio path.

The global search submits the existing structured catalog filters. `/` focuses
it when focus is outside a form or dialog. The rail opens the existing test
wallet and logic lab. The header provides lighting, glass appearance and
connection controls; appearance is stored only on the visitor's device and
shared with Sound Lab. Prisma is the default material; the original glass
appearance remains selectable. Five palettes, custom colors, transparency,
blur, corners, refraction and comfort controls are optional. Voice and microphone capture
remain opt-in. Product artwork depicts instrument families, not product photos.

The desktop rail uses six uniform 44 px icon controls with 23 px SVG artwork.
Full names appear beside the rail on hover or keyboard focus, instead of
wrapping inside the narrow capsule. On mobile, the bottom rail uses short,
single-line captions; the full accessible names remain on the controls.

## Materials and type

The room photograph was generated for this project with the built-in image
generation tool. It contains no third-party movie artwork, logos or client
portraits. `emporio/web/studio-room.webp` is the optimized publication asset;
the design reference supplied by the user was not redistributed.

Inter and Space Grotesk are bundled locally for Prisma; Manrope remains for
the original glass room. All use `font-display: swap` and system fallbacks.
No font request goes to a third-party host. `prisma.css` scopes the new material
to the selected style, on top of the shared typography and existing layouts.
[Font source, hashes and licenses](FONT-PROVENANCE.md).

The main title is 38 px on a large display and 28–33 px at smaller breakpoints;
body text is 14 px, navigation and filters 13 px, and assistant replies 15 px.
Supporting text is generally 11–12 px, with 16 px text-entry controls on mobile.
Drawers follow the chosen material with separate readable surfaces for codes,
status messages and controls. The voice mark is a bounded 19 px SVG mask, replacing unbounded
Unicode bars. The hero is shorter so more of the catalog is visible.

These choices do not constitute an accessibility or performance certification.
The browser review below supplements source checks and DOM tests.

## Validation

The UI suite runs the actual DOM handlers with the server adapter and the
standalone browser runtime. It covers cross-view search, tool navigation,
lighting, catalog filters, comparison, bag, checkout, research and audio
lifecycles. The three QR artworks are independently decoded at three sizes and
two orientations, matching the generated quote URL in all 18 checks.

The source checker validates IDs, local HTML/CSS assets, SVG syntax and transfer
budgets. The home text bundle has a 280 KB raw / 86 KB gzip limit, the room
bitmap has a separate 30 KB limit, local fonts have a separate 100 KB limit,
and audio assets remain lazy with their own
70 KB raw / 22 KB gzip limits. The text limit includes the shared material
layer and native language dictionary. No dictionary is hidden from the budget.

The framing review now renders the standalone build in an isolated Chrome
session at 320, 390, 768, 1024, 1280, 1440 and 1920 px. It checks horizontal
overflow, header overlap, separation from the tool rail, tablet columns and
drawer bounds, and saves screenshots for inspection. It also exercises
comparison, the bag, checkout preview, appearance persistence/reset and generated
chord playback/stop. Run `python scripts/check_framing.py --url <preview-url>`
after serving a standalone build. The recorded result is in
[evidence/framing-review.json](evidence/framing-review.json).

`python scripts/check_prisma.py --url <preview-url>` additionally renders eight
views/dialogs in both PT and EN at those seven widths. It checks filtering and
empty-state recovery, comparison across views, quantities, quote art download,
test approval/decline, top-up, logic, connection states, Portuguese questions,
research failure, language persistence, style switching, look import/export,
reduced motion, shared settings, generated audio, metronome, coaching, core
parameters and local WAV playback. Screenshots stay in `artifacts/prisma-review`;
the committed [review record](evidence/prisma-review.json) contains the results.

The review covers browser rendering and generated audio state, not physical
microphones, speakers or touch hardware. Checkout remains a demonstration.
