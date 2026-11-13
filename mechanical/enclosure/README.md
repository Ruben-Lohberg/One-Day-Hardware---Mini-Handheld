# Mini Handheld enclosure

Open the [FreeCAD model](enclosure.FCStd) and toggle the bezel or tray to see the board and display inside. The shell measures 47.2 × 95.2 × 15.0 mm, excluding the buttons.

| STL | Quantity | Orientation |
| --- | ---: | --- |
| [Tray](tray.stl) | 1 | Outside bottom on the bed |
| [Bezel](bezel.stl) | 1 | Outside face on the bed |
| [Plunger](plunger.stl) | 4 | Flat switch contact on the bed |

The [combined plate](case-and-board-plate.stl) includes the case parts and a PCB fit gauge on a 256 × 256 mm bed. The [gauge](pcb-fit-gauge.stl) is also available on its own. Use the [two-case plate](two-cases-plate.stl) to print two shells. Start with 0.20 mm layers and three walls, and try 0.12–0.16 mm layers for the plungers.

1. Fasten the PCB with four M2 × 5 mm pan-head self-tapping screws. The heads should be 3.5–4.3 mm across.
2. Seat the display on the ledges and connect its flex before closing the case. Keep pressure off the active glass and cable.
3. Insert the plungers from inside the bezel, long stem first. They can fall out when the case is open.
4. Close the case with four M2 × 12 mm pan-head self-tapping screws. Use heads up to 4.3 mm across and 1.55 mm tall. Check that the buttons move freely, the flex clears the lid, and the USB and SWD plugs fit.

To regenerate the models, refresh the [PCB STEP and display fit](../README.md), then run `build-enclosure.py` and `build-fit-plate.py` with FreeCAD's bundled Python. Run `build-plate.py` to regenerate the two-case plate. Set `MINI_HANDHELD_ENGRAVING_FONT` to a TrueType font path if the default Windows font is unavailable.
