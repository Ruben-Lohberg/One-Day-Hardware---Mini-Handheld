# Firmware hardware simulation

For the release-blocking rail tolerance and panel initialization findings,
see the [hardware bring-up audit](hardware-bringup-audit.md).

Renode boots the same Cortex-M0+ ELF built for the STM32G070CBT6's
128 KiB flash and 36 KiB SRAM. No simulator-specific display or game code
is compiled into it. The browser only drives the four active-low GPIO
inputs, advances virtual time, and displays the panel framebuffer.

| Path | What the model checks | What remains outside the model |
| --- | --- | --- |
| GPIO and time | Board pin mapping, active-low input, 16 MHz SysTick, Cortex-M0+ interrupt and sleep behavior | Switch bounce, crystal/oscillator tolerances, and complete reset and clock behavior |
| SPI2 | Clock gates used by the driver; PB13/PB15 AF0; 8-bit mode-0 transmit; a four-byte FIFO and a separate shifter; the baud divider, TXE, FTLVL, and BSY | DMA and SPI IRQ, other transfer modes, non-HSI16 clock profiles, and sub-byte timing |
| LCD | CS/D/C stable during each byte; reset pulse and command recovery; sleep/display/backlight state; address windows and portrait RGB565 writes | Analog power-on, panel-specific initialization and scanout/tearing, backlight brightness, readback, and unsupported controller commands |
| Electrical board | Separate ngspice power and IBIS clock experiments in [the simulation notes](../sim/README.md) | A live electrical co-simulation, real flex and input clamps, voltage/temperature corners, and any measured prototype behavior |

The PB15 power-on pull-down is disabled with the SYSCFG strobe before
the SPI pins are configured. Renode deliberately flags a transfer without
that strobe; it does not calculate the analog effect of the pull-down
against an active output driver. See [ST RM0454](https://www.st.com/resource/en/reference_manual/rm0454-stm32g0b0-advanced-armbased-32bit-mcus-stmicroelectronics.pdf).

## Current settings and speed

The earlier IBIS clock experiment found less ringing with medium rather
than high GPIO slew on PB13. The firmware uses medium slew for both SCK
and MOSI and keeps SPI at 2 MHz for bring-up. Slew sets the edge shape; the
SPI divider sets the byte rate. At 2 MHz, an 8-bit transfer takes 4 µs and
one full 240 × 320 RGB565 screen takes **at least 614.4 ms** on the wire.
Snake redraws only the changed tiles during play.

The [HS20HS072RX module datasheet](https://datasheet.lcsc.com/datasheet/pdf/75d064ee0eeae326e605dda9d4b98e7e.pdf?productCode=C5329582#page=12)
lists a 66 ns minimum write clock period and 10 ns data setup and hold.
The model checks the period, but a byte-level simulation cannot measure
setup or hold at J3. The HSI16-only profile tops out at 8 MHz SPI;
12–14 MHz would require a new clock profile and a hardware timing check.
The theoretical limit at 14 MHz is about 11.4 full-screen transfers per
second, before firmware and command overhead. Browser wall-clock speed
is not a measurement of display throughput.

## Repeatable checks and first board

Run `.\firmware\run-web.ps1 -SmokeTest` for game behavior and the bus
checks. It tests that a cold screen is still incomplete at 0.5 s, and
injects early CS and missing-PB15-strobe faults after the gameplay checks.
Run `.\firmware\run-web.ps1 -DisplayDemo -SmokeTest` to exercise the
diagnostic's four input paths and SPI pixel output.

For the first assembled board, build `.\firmware\build.ps1 -App Display`
and load `firmware/build/handheld-display.elf` with the J-Link over SWD.
Check button response, panel colors and orientation, and backlight
operation before loading `handheld-snake.elf` (build with `-App Snake`).
Probe SCK and MOSI at J3 with the real display flex attached, and watch
the 3.0 V rail while switching the backlight. Use those measurements
before raising the SPI clock or adding a DMA path.
