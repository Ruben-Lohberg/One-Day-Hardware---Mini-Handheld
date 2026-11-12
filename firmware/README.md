# Firmware and Renode

## Play Snake in the browser

Run the timing mock from the repository root with PowerShell:

```powershell
.\firmware\run-web.ps1 -Mock
```

Open [http://127.0.0.1:8766/mock](http://127.0.0.1:8766/mock). The browser
runs the same Snake C application as WebAssembly, using Python 3 and
LLVM's `wasm-ld` to build and serve it. Renode can run alongside it on 8765.

The mock advances with the browser clock. It models SPI at 2 MHz, the
panel's nominal 60 Hz scanout as frame snapshots, and an estimated 15 ms
pixel transition. Snake still moves every 150 ms and targets a 33 ms border
update. The panel model uses datasheet values and can be checked against
the assembled board. [Controller frame rate table](https://files.waveshare.com/wiki/2inch-Capacitive-Touch-LCD/ST7789T3_SPEC_V1.0.pdf#page=284)
· [Panel response time](https://datasheet.lcsc.com/datasheet/pdf/75d064ee0eeae326e605dda9d4b98e7e.pdf?productCode=C5329582#page=7)

## Play Snake in Renode

Run this from the repository root in PowerShell:

```powershell
.\firmware\run-web.ps1
```

After the boot message, open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).
Press a keyboard arrow or tap the D-pad to start. Steer toward the orange
food to grow and score. Hitting a wall or your body ends the game; press
an arrow to reset, then press again to start. Use Ctrl+C to stop the server.
This requires Python 3 in addition to LLVM and Renode. Pass `-Port` if the
default port is occupied, or `-Renode` to specify the Renode executable.

The browser sends button states to Renode's GPIO inputs. The STM32 ELF
draws through SPI2, and the virtual panel decodes the CS, D/C, RESET, and
backlight GPIO signals plus the ST7789 address windows and RGB565 pixel
writes. The canvas displays the resulting framebuffer. The browser advances
virtual time while the page is running; use one controlling tab.

Snake draws an animated RGB565 rainbow around the screen. The firmware
targets one border update every 33 ms at 2 MHz SPI and polls the buttons
between edges. Browser playback speed depends on how fast Renode runs.

Run `.\firmware\run-web.ps1 -SmokeTest` to verify Snake's rainbow border,
movement, growth, scoring, wall collision, and retry in Renode. It also
checks SPI2 setup, transfer time, and that the model catches an early
chip-select release or missing PB15 strobe. Add
`-DisplayDemo` to run the four-button display diagnostic, or combine it
with `-SmokeTest` to check the diagnostic's button updates.

The [hardware model and bring-up notes](../docs/firmware-hw-simulation.md)
describe what is modeled, what the electrical simulations found, and what
still needs to be measured on the assembled board.

Snake's rules and drawing code are in `src/snake.c`. Restart the simulator
to rebuild and boot after editing it. The STM32 SPI driver is in `src/display.c`.
Both display builds send the HS20HS072RX module's porch, gate, power and gamma
settings and select serial RGB565. SPI runs at 2 MHz from HSI16 divided by eight.

## GPIO-only monitor

The first firmware image polls the four buttons and drives the two LEDs.
It builds for Cortex-M0+ with the STM32G070CB's 128 KiB flash and 36 KiB
SRAM layout. Renode boots that ARM ELF and runs the real GPIO code.

From the repo root in PowerShell:

```powershell
.\firmware\run-renode.ps1 -SmokeTest
.\firmware\run-renode.ps1
```

You need LLVM's `clang` and `ld.lld` on PATH and
[Renode 1.17.0](https://github.com/renode/renode/releases/tag/v1.17.0).
The script finds Renode on PATH or at `firmware/build/renode/Renode.exe`.
You can also pass `-Renode 'C:\path\to\Renode.exe'`. Build only with
`.\firmware\build.ps1`; the ELF and linker map go in `firmware/build/`.

At the Renode prompt, step virtual time and inspect LED state:

```text
emulation RunFor "0.002"
sysbus.gpioPortA.up Press
emulation RunFor "0.002"
sysbus.gpioPortA.led1 State
sysbus.gpioPortA.up Release
emulation RunFor "0.002"
sysbus.gpioPortA.led1 State
quit
```

`led1` should report `True` while Up is pressed and `False` after release.
Up/Down are PA0/PA1 and drive LED1 (PA4); Left/Right are PA2/PA3 and drive
LED2 (PA5). The buttons model the PCB's active-low wiring.

The platform extends Renode's [generic STM32G0 model](https://github.com/renode/renode/blob/v1.17.0/platforms/cpus/stm32g0.repl),
which is a functional approximation. This test does not validate clock
setup, electrical timing, or the panel. The GPIO-only test uses the
original build without the display model.

Keep game logic in separate portable modules, and put STM32-specific I/O
in `src/board.c` and `src/display.c`. A game loop with debounced input
can use the same display driver in Renode and on the board.
