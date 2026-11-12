# PCB model for the enclosure

Open `mini_handheld.step` in FreeCAD and use it as a reference for the case.
The PCB is 42 × 56 mm. The STEP origin is the lower-left board corner when
viewed from above, with Z=0 at the board underside. The four mounting holes
are at (4, 4), (38, 4), (4, 52), and (38, 52) mm. See the [current KiCad render](../docs/images/kicad-board.png) for the
populated board.

The assembly includes the USB-C and SWD connectors. The display glass and flex,
button caps, USB plug and SWD jumper housings are separate parts and are not
represented. Check those against physical samples before finalizing the case.

The USB model is the HRO TYPE-C-31-M-12 (C165948) from the
[EasyEDA official library](https://easyeda.com/). The cost-down board uses
KiCad's generic through-hole SWD header model; check the actual strip
height and tails. The 3D render includes the hand-fitted parts.

From the repository root, start the STEP watcher in PowerShell:

```powershell
.\mechanical\export-board.ps1
```

It exports once at startup and refreshes `mini_handheld.step` when KiCad saves
changed board contents. Leave the terminal open; press Ctrl+C to stop. Add
`-Once` for a single export or `-KiCadCli` to specify another KiCad installation.
The script keeps the previous STEP if export fails and uses the same X=100 mm,
Y=134 mm origin with components enabled and copper layers omitted.

The 3.0 V regulator revision has the same populated board geometry as the
previous STEP. The refreshed display fit study uses the latest export.

FreeCAD's STEP import is a snapshot. Open the updated STEP to inspect it or
replace the PCB reference in your enclosure document when you want to use the
new geometry. The watcher does not modify any `.FCStd` files.

## Display fit study

Open `display-fit.FCStd` for the populated PCB, display and a folded flex
envelope. The original straight display/flex model is
`HS20HS072RX-flat.step`, from the JLCEDA/EasyEDA Official Library
([JLCEDA](https://lceda.cn/), [EasyEDA](https://easyeda.com/)). J3 uses the
KiCad FH12 model in the board STEP; [Hirose also supplies a STEP](https://www.hirose.com/product/p/CL0586-0704-0-55).

The fit study uses the [HS outline drawing](https://atta.szlcsc.com/upload/public/pdf/source/20251016/BAE15D01F6ECB51EA8350D6C5C8F6372.pdf)
for the 20.7 mm nominal tail reach and 6.5 mm terminal width. The modeled
2.5 mm bend radius and 2.95 mm insertion are trial dimensions, not supplier
limits. The board and display body clear each other. The only flex-to-PCB
model intersection is the inserted end inside the simplified closed latch,
which is modeled as solid through the insertion region. That intersection
cannot validate the actual slot fit. Check the physical sample for bend
radius, seating, contact side, latch access and case clearance.

To regenerate the study, run `build-display-fit.py` with FreeCAD's bundled
Python after updating the board STEP. This replaces only `display-fit.FCStd`;
make your enclosure in a separate document. Recheck the fit datums if the
board outline, export origin, display guide or connector moves.
