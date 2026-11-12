# JLCPCB assembly files

| File | Use |
| --- | --- |
| [GERBER-mini_handheld.zip](GERBER-mini_handheld.zip) | Fabrication: two copper layers, drill files and board outline |
| [BOM-mini_handheld.csv](BOM-mini_handheld.csv) | Parts to populate |
| [CPL-mini_handheld.csv](CPL-mini_handheld.csv) | Top-side placements and rotations |

This is the 3.0 V board revision, with TPS7A2430DBVR at U1 and 2.2 µF at C1.
JLCPCB fits 34 parts per board, including the J3 display socket. The fabrication
files include the lands for the hand-fitted USB-C and SWD connectors. See the
[separate parts list](../../docs/separate-parts.md) for those and the display.

To make a new set, use JLCPCB Tools in KiCad. The plugin writes to
`mini_handheld/jlcpcb/production_files/`; review those exports before copying
them here. See the [rotation notes](../../docs/separate-parts.md) for the
project-local corrections to Q1 and U1.
