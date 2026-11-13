# Firmware and Renode

Play the [browser demo](https://ruben-lohberg.github.io/One-Day-Hardware---Mini-Handheld/) with the arrow keys or on-screen D-pad. It runs the Snake C code as WebAssembly and models SPI transfers, TFT scanout, and pixel response.

## Play Snake in the browser

Use PowerShell from the repository root. Install Python 3 and put LLVM on PATH. For Renode, install [Renode 1.17.0](https://github.com/renode/renode/releases/tag/v1.17.0) or pass its executable with `-Renode`.

| Command | Result |
| --- | --- |
| `.\firmware\run-web.ps1 -Mock` | Browser timing mock at [localhost:8766/mock](http://127.0.0.1:8766/mock). Requires LLVM's `wasm-ld`. |
| `.\firmware\run-web.ps1` | STM32 firmware in Renode at [localhost:8765](http://127.0.0.1:8765/). Requires LLVM's `ld.lld`. |
| `.\firmware\run-web.ps1 -DisplayDemo` | Button and display diagnostic in Renode. |
| `.\firmware\build.ps1 -App Snake` | Build `firmware/build/handheld-snake.elf` for the STM32. |

Use `-Port` to choose a different port. Add `-SmokeTest` to the Renode web commands to check game play or the display diagnostic. Run `.\firmware\run-renode.ps1 -SmokeTest` for the GPIO-only test.

The [game](src/snake.c) is shared between the browser and STM32 builds. The [display driver](src/display.c) uses SPI2 at 2 MHz and sends RGB565 pixels.
