# Bundled fonts

`emporio/web/manrope-latin.woff2` is the unmodified Latin variable WOFF2 supplied
by Google Fonts for Manrope, normal style, weights 400–800. The CSS family name
remains Manrope. The browser loads it from the application's own static path.

- Source repository: https://github.com/google/fonts/tree/main/ofl/manrope
- Source request: https://fonts.googleapis.com/css2?family=Manrope:wght@400..800&display=swap
- Binary: https://fonts.gstatic.com/s/manrope/v23/xn7gYHE41ni1AdIRggexSg.woff2
- Downloaded: 2026-11-13
- Size: 24,532 bytes
- SHA-256: `8c2def024c1bf31aacf3624ae3c4d701269b4ec3dc765c04830839f0d36b2d9e`
- License: SIL Open Font License 1.1, copied verbatim to
  [FONT-LICENSE.txt](../emporio/web/FONT-LICENSE.txt) and included in the Pages export.

The project does not claim authorship of the font. The Latin subset covers the
English interface and common Western European accents. Characters outside it
use the local system fallback.

## Prisma typography

Inter (body and controls) and Space Grotesk (headings) are unmodified variable
Latin WOFF2 files supplied inside the user's `Prisma Pack.html` export. They
were extracted for the interactive profile and copied unchanged into Music.
The pack's embedded font notice states that these files were saved from Google
Fonts. Their original copyright and full OFL 1.1 notices are appended to
`emporio/web/FONT-LICENSE.txt` and included in the Pages build.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `inter-latin.woff2` | 48,256 | `3100e775e8616cd2611beecfa23a4263d7037586789b43f035236a2e6fbd4c62` |
| `space-grotesk-latin.woff2` | 22,288 | `0640890476fc1198ab4de571fb658de443c4d85b66466ec09534a8737ab1ce9d` |

Copyright holders: [Inter Project Authors](https://github.com/rsms/inter) and
[Space Grotesk Project Authors](https://github.com/floriankarsten/space-grotesk).
The CSS keeps the original family names. All three font files total 95,076
bytes; the classic skin loads Manrope, while Prisma loads Inter and Space Grotesk.
