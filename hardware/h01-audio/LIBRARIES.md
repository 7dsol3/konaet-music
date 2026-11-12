# Library provenance

`H01.pretty/` contains a frozen subset of KiCad 10.0.8 official footprints,
modified with project references, metadata and relative 3D paths. `models/`
contains the corresponding official KiCad STEP models. Copyright belongs to
the KiCad library contributors. These library subsets are distributed under
**CC-BY-SA 4.0 with the KiCad design exception**, not under the application's MIT
license. See [LICENSE-KICAD.txt](LICENSE-KICAD.txt),
[CC-BY-SA-4.0.txt](CC-BY-SA-4.0.txt), and
[KiCad's library license](https://www.kicad.org/libraries/license/).

The installer was downloaded from the official KiCad GitHub release and its
Authenticode signature verified as valid, KICAD SERVICES CORPORATION. The
source footprint identifier for each placement is in `bom.csv`. Local models
are hash-bound in `validation.json`.

Y1: the official ASE footprint references a missing STEP in that distribution.
The project therefore uses `Crystal_SMD_3225-4Pin_3.2x2.5mm.step` as a visibly
declared geometric proxy. Do not use that proxy to approve oscillator height,
enclosure clearance or assembly fit; verify the actual manufacturer drawing.

PCB/schematic design, generator scripts and original symbols use the repository
MIT license. Datasheets are linked, not redistributed. Freerouting 2.5.0 and
KiCad 10.0.8 are build tools, not incorporated inference or runtime code.
