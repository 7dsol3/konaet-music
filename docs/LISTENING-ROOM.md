# The KONAET listening room

The store is organized as a workspace: a floating translucent frame, a tool
rail, a searchable instrument shelf and a small panel of useful starting points.
Discover, Research and Guide are separate views of the same page. Their
navigation changes visibility; it does not replace the commerce or research
engines. The Sound Lab remains a separate page and keeps its local audio path.

The global search submits the existing structured catalog filters. `/` focuses
it when focus is outside a form or dialog. The rail opens the existing test
wallet and logic lab. The header provides lighting and connection controls;
lighting is stored only on the visitor's device. Voice and microphone capture
remain opt-in. Product artwork depicts instrument families, not product photos.

## Materials and type

The room photograph was generated for this project with the built-in image
generation tool. It contains no third-party movie artwork, logos or client
portraits. `emporio/web/studio-room.webp` is the optimized publication asset;
the design reference supplied by the user was not redistributed.

Segoe UI/Arial provide the main interface type without downloading fonts.
Large serif marketing headlines were replaced by short sans-serif headings.
Supporting labels use a larger size and the search controls retain 16 px input
text on mobile. These choices do not constitute a measured accessibility or
performance certification.

## Validation

The UI suite runs the actual DOM handlers with the server adapter and the
standalone browser runtime. It covers cross-view search, tool navigation,
lighting, catalog filters, comparison, bag, checkout, research and audio
lifecycles. The three QR artworks are independently decoded at three sizes and
two orientations, matching the generated quote URL in all 18 checks.

The source checker validates IDs, local HTML/CSS assets, SVG syntax and transfer
budgets. The home text bundle has a 170 KB raw / 50 KB gzip limit, the room
bitmap has a separate 30 KB limit, and audio assets remain lazy with their own
70 KB raw / 22 KB gzip limits. The text limit was expanded with the explicit
view navigation; the bitmap is accounted for separately.

Desktop/mobile visual inspection of the new Music build is still required:
the connected browser was unavailable in this session. DOM checks do not
exercise physical microphones, touch devices or CSS layout. Checkout remains
a demonstration and does not move real money.
