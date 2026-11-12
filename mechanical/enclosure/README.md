# Mini Handheld enclosure — prototype

The assembled shell is 47.2 × 95.2 × 15.0 mm, excluding the button tops.
The straight side walls are 2.0 mm thick; the PCB cavity and screw bosses
retain their dimensions.
Open `enclosure.FCStd` in FreeCAD. Toggle the Top bezel or Lower tray in the
tree to see how the display, flex and PCB sit inside. The Reference assembly
group is for fit checking and is not part of the print.

| Print file | Qty | Orientation in STL |
| --- | ---: | --- |
| `tray.stl` | 1 | Outside bottom on the bed |
| `bezel.stl` | 1 | Outside face on the bed |
| `plunger.stl` | 4 | Flat switch contact on the bed |

Start with 0.20 mm layers and three walls. Use 0.12–0.16 mm layers for the
button parts. A small brim can help hold the stems on their narrow feet.
Clear any brim or first-layer bulge from the sliding surfaces. The 6.0 mm
stem has 0.45 mm diametral clearance in the 4.8 mm long bezel guide.
The switch contact is flat and 3.5 mm across. The 7.2 mm internal lip
catches on the guide. The 6.0 mm button face sits 1.5 mm above the bezel.

The back inscription is recessed 0.50 mm into the tray, leaving 1.30 mm
of floor behind the text. Check the first layers in the slicer so the
lettering remains open.

1. Secure the PCB to its four standoffs with M2 × 5 mm pan-head self-tapping
   screws. The heads must be 3.5–4.3 mm across to bear on the PCB. The tray
   leaves clearance for the SWD solder pins below.
2. Set the display on the four side ledges with approximately 0.2 mm compliant
   pads. Connect the flex before closing the case. Use thin foam on the display
   frame under the bezel as needed to prevent rattle; leave the active glass
   and flex free of pressure. The ledges and lid stops locate the display.
3. Insert each one-piece plunger from the inside of the bezel, long stem
   first. Keep the bezel face down until closing the case. The inner lip
   blocks outward escape and the installed PCB and switch block inward
   escape. The plungers can drop loose when the case is opened.
4. Close the case with four M2 × 12 mm pan-head self-tapping screws, inserted
   through the back. Use heads at most 4.3 mm in diameter and 1.55 mm tall.
   The screws engage the blind bosses under the bezel. Check the actual
   screw length before driving them, and check the flex before tightening.
5. Confirm each switch clicks and releases freely. The switch now limits
   inward travel; the bezel has no separate press stop. Check that the USB
   plug seats through the left opening and the jumper housings fit the
   right SWD slot.

Both screw lengths are in the [parts list](../../docs/separate-parts.md).
The PETG pilot holes are 1.65 mm nominal. Test one screw by hand on a
trial print before tightening the others. The FreeCAD assembly includes
eight simplified screw models in a reference group; the STLs omit them.

The CAD checks cover case and assembly interference and both plunger
positions. They cannot account for print shrinkage, solder height, actual
switch stroke, or flex bend limits. Treat the first print as a fit prototype.
The USB aperture has a close inner opening and a wider exterior plug recess.
Check the small bridge above the aperture in the slicer. The SWD slot is
open to the lid seam; the pin tips project about 2.8 mm past the right wall.

To change dimensions, edit `build-enclosure.py` and run it with the bundled
FreeCAD Python. It uses the current board STEP and the display fit study in
the parent directory. Regeneration replaces these STLs and the CAD geometry;
in FreeCAD, use **Fit all** if opening a newly generated document.

For a first fit check, import `case-and-board-plate.stl` as one object. It
arranges one tray, one bezel, four plungers, and one PCB fit gauge on a
256 × 256 mm plate. The gauge is also available as `pcb-fit-gauge.stl`.
It preserves the board outline, mounting holes, and main component clearances.
Its connector shapes are solid gauges, its switches do not move, and it
omits underside SWD leads. Remove support material from the connector
overhangs before fitting it into the case.

For two complete cases, use `two-cases-plate.stl`. Previously saved slicer projects may contain older geometry. Use the STLs
here and re-slice for your printer.

Run `build-fit-plate.py` with FreeCAD's bundled Python after refreshing the
board STEP and rebuilding the enclosure to regenerate both files.
