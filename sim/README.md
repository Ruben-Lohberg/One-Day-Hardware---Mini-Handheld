# Electrical simulations

Run these decks from the repository root with ngspice.

```sh
ngspice -b sim/power-transients.cir
ngspice -b sim/lcd-sck-layout.cir
```

The power deck models USB droop, backlight PWM, and load steps. The clock deck estimates the effect of the PCB route, vias, and display flex on the SPI edge. See the [power plot](../docs/images/ngspice-power.svg). Verify the rail and clock on the assembled board.

On Windows, you can also use KiCad's bundled ngspice DLL. Put `kicad-cli.exe` on PATH or set `$kicadBin` to the folder containing it. For the IBIS comparison, download [ST's STM32G0 IBIS archive](https://www.st.com/resource/en/ibis_model/stm32g0_ibis.zip) into the current folder before running the final two commands.

```powershell
$kicadBin = Split-Path (Get-Command kicad-cli.exe -CommandType Application | Select-Object -First 1).Source
$clockDeck = Join-Path $env:TEMP 'handheld-lcd-ibis.cir'
python sim/run-kicad-ngspice.py --kicad-bin $kicadBin sim/power-transients.cir
python sim/build-lcd-ibis.py --kicad-cli (Join-Path $kicadBin 'kicad-cli.exe') --st-archive ./stm32g0_ibis.zip --output $clockDeck
python sim/run-kicad-ngspice.py --kicad-bin $kicadBin $clockDeck
```
