# PCB and display fit

Open the [populated PCB STEP](mini_handheld.step) or the [FreeCAD fit study](display-fit.FCStd) to see how the display sits above the board and how the flex folds into the socket. The case files and print instructions are in the [enclosure folder](enclosure/README.md).

Run `.\mechanical\export-board.ps1 -Once` from the repo root in PowerShell to refresh the PCB STEP. Add `-KiCadCli` with the executable path for a custom KiCad install. Omit `-Once` to refresh after each PCB save. To regenerate the fit study after exporting the PCB, run `build-display-fit.py` with FreeCAD's bundled Python.

The flex is modeled at a trial bend radius of 2.5 mm and a nominal insertion of 2.95 mm. Check seating, latch access, and the bend against a physical display. The display and USB-C STEP models come from the [EasyEDA library](https://easyeda.com/).
