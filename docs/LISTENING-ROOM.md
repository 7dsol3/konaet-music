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
shared with Sound Lab. The original appearance remains the default. Five
palettes, custom colors, transparency, blur, corners and comfort controls are
optional. Voice and microphone capture
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

Manrope is bundled locally as one variable Latin WOFF2, with Segoe UI/Arial as
fallbacks and `font-display: swap`. No font request goes to a third-party host.
The shared `typography.css` owns the store and drawer scale; audio-only type
stays in the lazy Sound Lab stylesheet. Legacy workspace rules no longer set
competing text sizes. [Font source, hash and license](FONT-PROVENANCE.md).

The main title is 38 px on a large display and 28–33 px at smaller breakpoints;
body text is 14 px, navigation and filters 13 px, and assistant replies 15 px.
Supporting text is generally 11–12 px, with 16 px text-entry controls on mobile.
The light assistant drawer has a dark accent instead of inheriting the pale
page accent. The voice mark is a bounded 19 px SVG mask, replacing unbounded
Unicode bars. The hero is shorter so more of the catalog is visible.

These choices do not constitute a measured accessibility or performance
certification. A DOM/CSS diagnostic checks the 1920, 1280 and 390 px rules;
it does not replace visual inspection in an actual browser.

## Validation

The UI suite runs the actual DOM handlers with the server adapter and the
standalone browser runtime. It covers cross-view search, tool navigation,
lighting, catalog filters, comparison, bag, checkout, research and audio
lifecycles. The three QR artworks are independently decoded at three sizes and
two orientations, matching the generated quote URL in all 18 checks.

The source checker validates IDs, local HTML/CSS assets, SVG syntax and transfer
budgets. The home text bundle has a 195 KB raw / 58 KB gzip limit, the room
bitmap has a separate 30 KB limit, the local font has a separate 30 KB limit,
and audio assets remain lazy with their own
70 KB raw / 22 KB gzip limits. The text limit was expanded with the explicit
view navigation; the bitmap is accounted for separately.

Desktop/mobile visual inspection of the new Music build is still required:
the connected browser was unavailable in this session. DOM checks do not
exercise physical microphones, touch devices or CSS layout. Checkout remains
a demonstration and does not move real money.
