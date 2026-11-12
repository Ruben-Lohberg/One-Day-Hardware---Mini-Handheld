# Electrical simulation

These are standalone SPICE decks for questions the production schematic and
KiCad's rule checks cannot answer. They are approximations, so compare their
predictions with measurements during [bring-up](../docs/hardware-bringup-audit.md).

- [Power transients](power-transients.cir): USB source impedance, backlight PWM
  and a 25 → 75 mA logic load step. The LDO behavior and effective capacitance
  are assumptions. See the [actual simulated rail traces](../docs/images/ngspice-power.svg).
- [Display clock](lcd-sck-layout.cir): a board-informed interconnect model for
  the 12.35 mm route, two vias and estimated flex. The older [lumped
  experiment](lcd-sck.cir) is useful for comparing simple edge damping.
- [IBIS clock](build-lcd-ibis.py): builds a transient deck from
  [ST's STM32G0 IBIS archive](https://www.st.com/resource/en/ibis_model/stm32g0_ibis.zip).
  It compares four PB13 slew settings using ST's 3.3 V curves. The receiver
  is an unclamped capacitive load, and the PCB and flex are estimated LC
  networks, so the voltage peaks are not predictions of pin stress on this
  3.0 V board.

From the repo root, use standalone ngspice for the power and layout decks:

```sh
ngspice -b sim/power-transients.cir
ngspice -b sim/lcd-sck-layout.cir
```

On Windows, this also works with the ngspice DLL that ships with KiCad. Adjust
the KiCad path and download ST's IBIS archive before running the last two lines.

```powershell
$kicadBin = Split-Path (Get-Command kicad-cli.exe -CommandType Application | Select-Object -First 1).Source
$ibisArchive = "$env:USERPROFILE/Downloads/stm32g0_ibis.zip"
$clockDeck = "$env:TEMP/handheld-lcd-ibis.cir"
python sim/run-kicad-ngspice.py --kicad-bin $kicadBin sim/power-transients.cir
python sim/run-kicad-ngspice.py --kicad-bin $kicadBin sim/lcd-sck-layout.cir
python sim/build-lcd-ibis.py --kicad-cli "$kicadBin/kicad-cli.exe" --st-archive $ibisArchive --output $clockDeck
python sim/run-kicad-ngspice.py --kicad-bin $kicadBin $clockDeck
```


## Results and assumptions

The power test uses a behavioral TPS7A24 approximation, with headroom and DC
load regulation informed by the [TI datasheet](https://www.ti.com/lit/ds/symlink/tps7a24.pdf).
The loop response, effective capacitance, cable impedance, and logic load are
assumptions. With a 4.4 V source and a 25 → 75 mA logic load step, the two
scenarios reached 2.979 V and 2.929 V, returning above 2.99 V after about 12 µs
and 56 µs. A separate 3.05 V fault dip brought the rail to about 2.91 V and
2.83 V late in the dip. Measure LDO stability, supply ripple and the effects
of PWM on the real 3.0 V rail.

The clock test uses ST's 3.3 V PB13 output curves and LQFP48 package
parasitics to compare drive settings. Its absolute voltages are for that
model supply. KiCad converts the four push-pull modes; the script fills
the missing voltage-range field in a temporary model copy from ST's pull-up
reference. The PCB and flex are estimated LC networks, and the receiver is
a capacitive load without clamps. The 2 MHz test spaces the edges far enough
apart to use all four IBIS waveform tables; it is an edge test, not a maximum
SPI frequency test. At the nominal interconnect/load, high drive gave
3.69 V peak and −0.40 V minimum; medium drive gave 3.30 V and approximately
0 V, with a 3.44 ns rise. High drive with an illustrative 33 Ω source resistor
gave 3.35 V and −0.05 V. These are simulated unclamped voltages, not pin-stress
predictions. The interconnect model does not capture plane splits or coupling.
Start bring-up with moderate GPIO slew and conservative SPI timing, and probe
3.0 V at the MCU and SCK near J3 with the actual display connected.
