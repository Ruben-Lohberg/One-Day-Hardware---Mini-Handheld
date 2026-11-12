# STM32G070 and HS20HS072RX bring-up audit

The design uses a shared 3.0 V rail and the panel-specific initialization at
2 MHz. Startup, power transients and display behavior still need verification
on an assembled board with the purchased panel.

## Power and physical interface

- **Display rail:** The module's normal limits are IOVCC 1.65–3.3 V and VCI
  2.4–3.3 V at 25 ±2 °C. J3.8 and J3.9 share U1's 3.0 V rail with the MCU.
  Adding TI's ±1.25% temperature accuracy, ±0.25% line and ±0.50% load limits
  gives a steady-state budget of 2.94–3.06 V under the specified conditions.
  That leaves 240 mV to the panel's 3.3 V ceiling before transients. Check
  overshoot at J3 on plug-in and backlight switching, and check LED
  brightness, Q1 drive and SWD VTref on the prototype.
- **Regulator capacitors:** Samsung's typical DC-bias data gives about
  0.88 µF for C1 (CL10A225KO8NNNC, 2.2 µF X5R) at 5.5 V and about
  4.04 µF for C2 (CL21A475KAQNNNE, 4.7 µF X5R) at 3.06 V. Applying
  −10% tolerance and −15% temperature allowances to those typical
  values gives about 0.67 µF and 3.09 µF. TI's nominal 1 µF input and
  1 µF minimum / 2.2 µF typical output recommendations already allow
  for 50% derating. The old C1 budgets about 0.47 µF by the same method.
  These calculations are design estimates from typical curves.
- **Regulator thermal margin:** With 5.5 V in and 2.94 V out, 50 mA of
  logic load dissipates 128 mW and 100 mA dissipates 256 mW. TI's
  reference-board thermal resistance of 167.8 °C/W gives about 21 °C
  and 43 °C rise respectively, or about 81 °C and 103 °C junction at a
  60 °C local ambient. Both estimates are below the 125 °C operating
  limit. The backlight bypasses U1, and the panel vendor leaves logic
  current unspecified. Measure startup and running current, rail
  waveforms and U1 temperature with the assembled enclosure. Pins 2
  and 4 connect to the ground plane through the nearby shared via.
- **MCU rail:** STM32G070CBT6 permits 2.0–3.6 V. For this LQFP48, U2.4
  VBAT, U2.5 VREF+ and U2.6 VDD/VDDA all go to the logic rail; U2.7
  VSS/VSSA goes to GND. C3/C4 provide 100 nF and 4.7 µF nominal at the
  supply, and C5 provides 100 nF at VREF+. Recheck decoupling and
  regulator stability with the actual effective capacitor values under
  DC bias if U1 changes. No separate analog supply or battery is needed.
- **Flex:** J3 pins 1–12 agree with the module drawing and interface
  table: GND, CS, D/C, SCK, SDA, RESET, NC, IOVCC, VCI, LEDA, LEDK,
  GND. This is four-wire SPI with GPIO D/C. The drawing shows 0.50 mm
  pitch and a 0.30 mm tail. J3 is a bottom-contact Hirose FH12;
  confirm the real sample's exposed contact face, pin 1 and thickness
  with the proposed fold before power-on. The schematic cannot verify
  the physical contact face.
- **Backlight:** The module lists 80 mA as the absolute forward-current
  limit and characterizes its forward voltage at 80 mA. The two 100 Ω
  resistors in parallel deliberately run below that at nominal USB
  voltage. The quoted 2.8–3.2 V LED drop is not a bound at all currents
  and temperatures. Measure current and resistor temperature at full
  duty and the upper USB supply corner. PB0 is currently GPIO on/off
  in firmware; timer PWM is a future option. The 100 kΩ gate pulldown
  keeps Q1 off before GPIO configuration.

## Reset, straps and register audit

| Function | Saved design and firmware |
| --- | --- |
| Boot | PA14/BOOT0 (U2.36) is SWCLK on J2.4; PA13 (U2.35) is SWDIO on J2.3. Production option bytes select main flash with `nBOOT_SEL=1` and `nBOOT0=1` (factory `nBOOT1=1`). No external strap is required for this mode. Verify the option bytes on the actual part, leave read protection at level 0 for development, program over SWD and confirm a cold boot without the debugger. A blank device can enter system bootloader. Do not select pin-based boot if relying on SWCLK sharing. |
| Reset | U2.10 NRST has 10 kΩ to the rail and 100 nF to GND, and goes to J2.5. ST's reference reset circuit shows 100 nF. Use J-Link VTref as sense, not supply; power the board separately. |
| LCD idle and reset | CS (PB12) and RESET (PB10) are pulled high by 10 kΩ. Firmware sets CS high, pulses RESET low and waits after release. PB14 is GPIO D/C. The panel exposes no interface-mode strap or separate readback output on J3. |
| SPI mux | PB13 (U2.25) is SPI2_SCK AF0 and PB15 (U2.27) is SPI2_MOSI AF0. PB14 (U2.26) remains GPIO. Firmware enables GPIOB in RCC_IOPENR[1], SPI2 in APBENR1[14], and SYSCFG in APBENR2[0], then writes CFGR1[9] to release the PB15 power-on pull-down. PA8/PD0/PD2 are unused; no UCPD connection is made to USB-C. J1 CC1 and CC2 have separate 5.1 kΩ pulldowns. |
| SPI transfer | CR1 configures master, mode 0, MSB first, software NSS and one-line transmit (BIDIMODE/BIDIOE). CR2.DS=7 selects 8 bits; firmware uses byte writes to DR. TXE admits data, then FTLVL=0 and BSY=0 are awaited before changing D/C or releasing CS. ES0468 §§2.10.1–2.10.2 cover disabling SPI while active and slave-mode BSY, not the current always-enabled transmit-master path. Revisit before adding power gating, DMA or mode changes. |
| Inputs | PA0–PA3 match the active-low buttons and PA4/PA5 match the LEDs. There is no mechanical switch debounce in Snake yet. The simulator's button edges are clean. |

## SPI clock and timing margin

The current firmware uses HSI16, reset clock dividers and SPI BR=010
(divide by eight): **2 MHz nominal**, 500 ns per period. DS12766 Table 37
shows 15.88–16.08 MHz at 3.0 V / 30 °C, plus separate temperature and
supply drifts. The modest HSI variation is immaterial to the 2 MHz SCK
period margin, but matters to a delay set exactly at its minimum.

Use the module's **stricter** 4-wire table (p. 12): 66 ns minimum write
period, 15 ns minimum SCK high and low, 15 ns write CS setup/hold, 40 ns
CS-high gap, and 10 ns setup/hold for D/C and SDA. That gives a period-only
ceiling of 15.15 MHz; **16 MHz is out of spec**. The bare ST7789T3 lists
a 16 ns minimum write period at its stated conditions. The bare V2 table
and MCU's up-to-32 MHz master rating also do not override the module.

Both GPIO speed fields are set to 01, but they are not equivalent pads.
PB13 is FT_f (DS12766 Table 49, 10 MHz at 50 pF and 15 MHz at 10 pF for
the 01 setting at 2.7–3.6 V); PB15 is FT_c and uses the low bit of
OSPEEDR (Table 50, 10 MHz at 50 pF with bit set, up to 35 ns rise/fall
under those conditions). These are test conditions, not predictions for
the board's flex/load. The previous IBIS simulation was for PB13.
If the rail changes, re-evaluate the signal model at the new supply voltage.
Start at 2 MHz and measure both lines at J3, with CS and D/C, before
raising the clock. Try 4/8 MHz first. Treat 12–14 MHz as a measured
performance experiment requiring a different clock tree, not an
approved setting. Renode models whole-byte timing, not these edge limits.

## LCD initialization

The module PDF is internally inconsistent: its overview says ST7789T3,
the outline says ST7789V2, and its appended example is labelled ST7789V.
Both controller documents support the basic command family used by the
firmware. Use the module's example as the starting point for this
specific glass, and confirm the delivered revision with the supplier or
a sample. The example sets portrait MADCTL and RGB565 (COLMOD 0x05 on
the serial path), then applies panel porch/gate, power/VCOM, frame-rate
and positive/negative gamma settings before display-on.

The driver sends this profile, including serial RGB565 (COLMOD 0x05),
after sleep-out. It waits 150 ms after releasing reset and again after
sleep-out. Renode checks the SPI transfers and resulting pixels. Use solid
RGB/black/white, corner markers and a checkerboard on the physical panel
to confirm colors, inversion, address offsets and scanout.

## Checks and sources

The saved schematic XML netlist was compared with the package and module
tables. KiCad reports zero ERC and board DRC violations and zero unconnected
items. The schematic comparison lists the four intentional PCB-only
mounting holes.

After first programming, fully power-cycle the board and test without the
debugger. The empty-flash flag is evaluated on option-byte load, so a
system reset alone may still select the ROM loader on a freshly programmed
part. ES0468 also documents that connecting a debugger latches the PA14
level for pin-selected boot until power-down.

- [ST DS12766 Rev 3](https://www.st.com/resource/en/datasheet/stm32g070cb.pdf):
  LQFP48 pinout, Tables 11/13, 37, 49–51 and 64, and Figure 8.
- [ST RM0454](https://www.st.com/resource/en/reference_manual/rm0454-stm32g0b0-advanced-armbased-32bit-mcus-stmicroelectronics.pdf):
  Table 7, option bytes, RCC, SYSCFG and SPI registers.
- [ST ES0468 Rev 5](https://www.st.com/resource/en/errata_sheet/es0468-stm32g070cbkbrb-device-errata-stmicroelectronics.pdf):
  boot/reset and SPI limitations.
- [HS20HS072RX module specification](https://datasheet.lcsc.com/datasheet/pdf/75d064ee0eeae326e605dda9d4b98e7e.pdf?productCode=C5329582):
  PDF pp. 5–6, 10–12 and 19–20.
- Sitronix [ST7789T3](https://files.waveshare.com/wiki/2inch-Capacitive-Touch-LCD/ST7789T3_SPEC_V1.0.pdf)
  and [ST7789V2](https://dfimg.dfrobot.com/nobody/wiki/b1770205edde40407a1c37b4a6c5ffb7.pdf):
  4-wire timing, reset, and command definitions.
- [TI TPS7A24](https://www.ti.com/lit/ds/symlink/tps7a24.pdf), §§5, 6.3–6.5
  and 8.1.2–8.1.6.
- Samsung capacitance data for [C1](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do),
  [C2](https://product.samsungsem.com/mlcc/CL21A475KAQNNN.do) and
  [the old C1](https://product.samsungsem.com/mlcc/CL10A105KB8NNN.do).
- [Hirose FH12-12S-0.5SH(55)](https://www.hirose.com/product/p/CL0586-0704-0-55).
