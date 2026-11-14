# The KONAET listening room

The store is organized as an instrument index: one measured grid, a small tool
rail, a searchable shelf and clear starting points beside the featured instrument.
Discover, Research and Guide are separate views of the same page. Their
navigation changes visibility; it does not replace the commerce or research
engines. The Sound Lab remains a separate page and keeps its local audio path.

The global search submits the existing structured catalog filters. `/` focuses
it when focus is outside a form or dialog. The rail opens the existing test
wallet and logic lab. The header provides lighting, appearance and connection
controls; preferences are stored only on the visitor's device. The appearance
drawer includes six palettes and three material finishes, two custom colors,
surface opacity, blur, corner and reading-size controls, reduced motion, sharper contrast, background photography,
reset and portable JSON export/import. Both pages use the same settings.
The lighting button changes the stage and product illumination. At zero glass
opacity on a light palette, labels switch to dark ink to remain readable.
Voice and microphone capture remain opt-in. Product artwork depicts instrument
families, not product photos.

The desktop rail stays fixed as an equipment strip with visible captions. Mobile
uses a bottom navigation row with short captions and accessible names on the
controls. The guitar stage has category keys that trigger the real catalog
filters. Catalog categories read as an index, and products have one consistent
frame with clear text below.

## Direction and references

The layout takes cues from real instrument interfaces: the product focus of
[Moog's synthesizer collection](https://www.moogmusic.com/synthesizers/), the
disciplined catalog navigation of [Teenage Engineering's store](https://teenage.engineering/store),
the tactile control study in [Voicu Apostol's switch](https://dribbble.com/shots/25895544-3D-Dark-Orange-Switch),
and the selective material effects described in [Aceternity's Liquid Glass](https://ui.aceternity.com/components/liquid-glass).
These are structural references, not copied pages or imported templates. KONAET
keeps its own content, instrumentation, colors and functional boundaries. Glass
appears where it helps navigation or focus; the product grid stays legible.

The amber guitar hero is an original transparent illustration generated with
the built-in image tool, then resized and stored as `emporio/web/hero-guitar.webp`.
Its brief called for a full acoustic instrument with visible wood grain, strings
and hardware under warm atelier lighting, without logos or a background. It is
an art study, not a photograph of a specific catalog product.

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

The main title scales with viewport width and the visitor's reading-size control;
body text is 14 px, navigation and filters 13 px, and assistant replies 15 px.
Supporting text is generally 11–12 px, with 16 px text-entry controls on mobile.
The light assistant drawer has a dark accent instead of inheriting the page
accent. The voice mark is a bounded 19 px SVG mask, replacing unbounded
Unicode bars. The featured instrument stays prominent above the catalog.

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
budgets. The home text bundle has a 260 KB raw / 72 KB gzip limit, the room and
instrument bitmaps have a separate 100 KB limit, the local font has a 30 KB limit,
and audio assets remain lazy with their own
70 KB raw / 22 KB gzip limits. The text limit includes the shared appearance
engine and responsive editorial layer; the bitmap is accounted for separately.

Desktop/mobile visual inspection of the new Music build is still required:
the connected browser was unavailable in this session. DOM checks do not
exercise physical microphones, touch devices or CSS layout. Checkout remains
a demonstration and does not move real money.
