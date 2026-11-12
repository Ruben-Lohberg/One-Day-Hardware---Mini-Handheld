# Mini Handheld design notes

For the illustrated build, start with the [project README](../README.md).
The following notes record part choices, pinouts and checks used while
designing the board. Dates and quotes in these notes are snapshots.

## Current design

| Part | Build |
|---|---|
| Power | USB-C supplying 5 V, with a TPS7A2430DBVR producing 3.0 V |
| Microcontroller | STM32G070CBT6, LQFP48, 128 KiB flash, up to 36 KiB RAM |
| Controls | Four XUNPU TS-1088-AR02016 SMD buttons, C720477, arranged as arrow keys |
| Indicators | Two LEDs, each controlled independently |
| Display | HS20HS072RX, 2-inch 240 x 320 colour TFT, ST7789 family, SPI |
| Programming | Five-pin 2.54 mm right-angle through-hole SWD header on the right edge, jumper leads to J-Link BASE Compact |
| Assembly | JLCPCB fits the SMD parts including J3; we solder J1 and J2 and plug in the display. See [separate parts](separate-parts.md). |

The [KiCad project](../mini_handheld/mini_handheld.kicad_pro) uses an A3
schematic sheet so the functional blocks are easy to follow. The placement and
assembly notes below retain the original design decisions and sample checks.

## Buttons, USB-C and SWD parts

Selected on 21 October 2026:

| References | Manufacturer / part | LCSC | Assigned footprint |
|---|---|---|---|
| SW1-SW4 | XUNPU TS-1088-AR02016 | C720477 | `Button_Switch_SMD:SW_SPST_TS-1088-xR020` |
| J1 | Korean Hroparts Elec TYPE-C-31-M-12 | C165948 | `MiniHandheld:USB_C_Receptacle_HRO_TYPE-C-31-M-12_Edge` |
| J2 | Right-angle 1×5 male 2.54 mm THT header | Hand fitted | `MiniHandheld:PinHeader_1x05_P2.54mm_Horizontal_Edge` |

The buttons retain UP/DOWN/LEFT/RIGHT as their visible schematic values; their
exact part numbers are stored in the MPN field, with supplier numbers in LCSC.
Their two terminals are a normally open contact: footprint pad 1 connects to the
GPIO/pull-up net and pad 2 to GND. These are two-terminal switches, so there are
no duplicate internal terminal pairs to map. The drawing specifies a 3.9 x 3 mm
body, 2 mm operating height, 1.6 N nominal force and 0.2 +/- 0.1 mm travel.
The footprint's two 1.05 x 2 mm lands have a 3.40 mm inner gap and 5.50 mm outer
span, matching the recommended drawing. Use printed caps/plungers with a case
stop to limit travel; tune fit on a physical sample.

The USB-C footprint matches the manufacturer's contact order: CC1=A5, CC2=B5;
VBUS=A4/A9/B4/B9; GND=A1/A12/B1/B12; shell=SH. Shared physical VBUS/GND contacts
are represented by overlapping paired pads in the KiCad footprint, all assigned
to the same respective net. D+/D- and SBU remain intentionally unused. The
four plated shell-anchor slots and two locating holes match the drawing. USB-C
signals are SMD; its shell anchors extend through the board for retention. Plan
the case opening around both the socket and the moulded USB plug, with the PCB
supported near the connector.

### Five-pin SWD jumper connection

J2 replaces the earlier 20-pin header. Its pin order is project-specific, not
the standard 10-pin Cortex or 20-pin Arm layout:

| J2 pin | Signal / board connection | J-Link 20-pin connection |
|---|---|---|
| 1 | VTref / +3V0 | 1 / VTref |
| 2 | GND | 4 / GND |
| 3 | SWDIO / PA13, MCU pin 35 | 7 / SWDIO |
| 4 | SWCLK / PA14, MCU pin 36 | 9 / SWCLK |
| 5 | NRST / MCU pin 10 | 15 / nRESET |

USB supplies board power. VTref is a voltage-sense connection to J-Link; leave
J-Link pin 19 (5 V supply) disconnected. The front silkscreen marks the
pin-1 land with a `1`; use the table above for the other pins.
Keep the jumper leads short and accessible with the case
back removed, away from the display flex.

The through-hole footprint has five 1.0 mm plated holes on 2.54 mm
centres and uses a square pad for pin 1. The row is centred at
(133, 114.5), 3.5 mm toward the buttons from the original SMD header.
Check clearance for the actual mating pins and jumper housings above
the PCB and the solder joints and cut tails below it.

Sources: [button drawing](https://www.lcsc.com/datasheet/C720477.pdf),
[USB-C drawing](https://www.lcsc.com/datasheet/C165948.pdf),
[SEGGER SWD pinout](https://www.segger.com/products/debug-probes/j-link/technology/interface-description/).

## LEDs, resistors and capacitors

Selected on 21 October 2026 from the JLCPCB Tools database updated on 18 October
2026, with JLCPCB product listings and manufacturer specifications cross-checked.
These are the database's first quantity-tier USD prices and stock snapshots, not
reserved inventory or a current PCBA quote.

| References | Value | Manufacturer part number | LCSC | Package | Library | USD each | Stock snapshot |
|---|---|---|---|---|---|---:|---:|
| R1, R2 | 5.1k | 0603WAF5101T5E | [C23186](https://jlcpcb.com/partdetail/C23186) | 0603 | Basic | $0.002 | 23,518,927 |
| R3, R4, R5, R6, R7, R13, R14 | 10k | 0603WAF1002T5E | [C25804](https://jlcpcb.com/partdetail/C25804) | 0603 | Basic | $0.002 | 30,981,226 |
| R8, R9 | 1k | 0603WAF1001T5E | [C21190](https://jlcpcb.com/partdetail/C21190) | 0603 | Basic | $0.003 | 23,215,596 |
| R10, R11, R15 | 100 | 0603WAF1000T5E | [C22775](https://jlcpcb.com/partdetail/C22775) | 0603 | Basic | $0.003 | 10,761,051 |
| R12 | 100k | 0603WAF1003T5E | [C25803](https://jlcpcb.com/partdetail/C25803) | 0603 | Basic | $0.003 | 19,338,133 |
| C3, C5, C6, C7, C8 | 100n | CC0603KRX7R9BB104 | [C14663](https://jlcpcb.com/partdetail/C14663) | 0603 | Basic | $0.011 | 31,785,866 |
| C1 | 2.2u | CL10A225KO8NNNC | [C23630](https://jlcpcb.com/partdetail/C23630) | 0603 | Basic | $0.013 | 3,388,537 |
| C9 | 1u | CL10A105KB8NNNC | [C15849](https://jlcpcb.com/partdetail/C15849) | 0603 | Basic | $0.014 | 9,260,434 |
| C2, C4 | 4.7u | CL21A475KAQNNNE | [C1779](https://jlcpcb.com/partdetail/C1779) | 0805 | Basic | $0.038 | 2,365,029 |
| D1, D2 | KT-0603R | KT-0603R | [C2286](https://jlcpcb.com/partdetail/C2286) | 0603 | Basic | $0.008 | 8,554,828 |

Resistors are UNI-ROYAL 1% thick-film 0603, 0.1 W / 75 V parts.
R10 and R15 replace the original Extended 47 Ohm part with two Basic
100 Ohm resistors in parallel. R11 still serves as the gate resistor.

C3/C5/C6/C7/C8 are 100 nF, 50 V, X7R, 10%, 0603. C1 is 2.2 µF, 16 V,
and C9 is 1 µF, 50 V, both X5R, 10%, 0603. C2/C4 are 4.7 µF, 25 V, X5R,
10%, 0805. These are non-polar ceramic
capacitors; either terminal may connect to either footprint pad. The footprint
body sizes match 0603 imperial / 1608 metric and 0805 imperial / 2012 metric.
Use short connections and local placement for bypass capacitors.

C1 and C2 give the TPS7A24 input and output capacitance margin under DC bias.
See the [capacitor and thermal estimates](hardware-bringup-audit.md#power-and-physical-interface).

D2 uses the same red KT-0603R / C2286 as the manually assigned D1. D1's saved
symbol and fields were preserved exactly. R8/R9 stay at 1 kOhm; nominal current
is about 1.3 mA for a 2 V forward drop, with actual current/brightness checked on
the board. Both LEDs use `LED_SMD:LED_0603_1608Metric`.

**LED polarity mapping:** KiCad's generic LED symbol and footprint use pad 1=K
(cathode, GND here) and pad 2=A (anode, series resistor here). The supplier's
package sketch instead labels its cathode terminal as 2/minus and anode as
1/plus. Thus KiCad pad 1 corresponds to supplier terminal 2, and KiCad pad 2 to
supplier terminal 1. Match the physical cathode marking to the footprint's K
side; do not infer polarity from the supplier's numeric labels alone. Check the
JLCPCB assembly preview against anode/cathode and apply any placement rotation
correction before ordering. No schematic wiring change is needed.

The exact MPN, manufacturer, LCSC number, voltage/power rating and tolerance are
stored in hidden schematic fields; capacitance dielectric is recorded too.
All selected two-terminal footprint pad numbers were checked against the symbols.
The standard KiCad land patterns provide assembly allowance around the nominal
package terminals; they need not be identical to a vendor's suggested land shape.

Sources: [TPS7A24 datasheet](https://www.ti.com/lit/ds/symlink/tps7a24.pdf),
[Samsung 4.7 uF specifications](https://product.samsungsem.com/mlcc/CL21A475KAQNNN.do),
[resistor series datasheet](https://www.lcsc.com/datasheet/C17969.pdf),
[YAGEO capacitor datasheet](https://www.lcsc.com/datasheet/C14663.pdf),
[Samsung capacitor catalogue](https://www.lcsc.com/datasheet/C15849.pdf),
[LED package/polarity drawing](https://www.lcsc.com/datasheet/C2286.pdf).

## Display procurement and connector

Buy the **HS20HS072RX display, LCSC C5329582**, separately from LCSC. JLCPCB's
assembly-parts library does not ship loose components. Keep the external display
out of the board's assembly BOM; J3 represents the socket, not the display.
No separate ribbon cable is planned: the display's integral flex plugs into J3.

J3 is **Hirose FH12-12S-0.5SH(55), C88360**, an SMD horizontal ZIF socket with
bottom contacts. JLCPCB lists this connector for SMT assembly on both Economic
and Standard PCBA. This avoids making the display itself a Standard-only
assembly item. Recheck stock and the actual assembly quote before ordering.

Compatibility checked against the display outline and Hirose FH12 drawings:

| Mating feature | Display tail | FH12 requirement |
|---|---|---|
| Contacts / pitch | 12 / 0.5 mm | 12 / 0.5 mm |
| Contact span / tail width | 5.5 / 6.5 mm | 5.5 / 6.5 mm nominal |
| Tail thickness | 0.3 mm | 0.3 +/- 0.05 mm |
| Exposed contact length | 3.5 mm | 3.5 mm minimum |
| Reinforced end length | 5 mm | 4.5 mm minimum |
| Contact orientation | Exposed side must face the socket contacts | Bottom contact: exposed contacts face toward PCB |

Assigned footprint:
`Connector_FFC-FPC:Hirose_FH12-12S-0.5SH_1x12-1MP_P0.50mm_Horizontal`.
Its signal pads run from pin 1 at x=-2.75 mm to pin 12 at x=+2.75 mm with
0.5 mm spacing. Mechanical hold-down pads are not signal pins. During PCB layout,
orient the socket so the tail reaches it without twisting and display pin 1
mates with socket pin 1. Check a physical sample before ordering the PCB; the
nominal drawing check does not establish production tolerances or fit by itself.

## Display electrical connections

J3 numbering follows the display's mechanical drawing and interface table.
The names SCL/SDA on this display mean SPI clock/data, not I2C.

| J3 pin | Display signal | Board connection |
|---|---|---|
| 1 | GND | GND |
| 2 | CS | LCD_CS: PB12, MCU pin 24; 10 kOhm pull-up R13 |
| 3 | RS / D-C | LCD_DC: PB14, MCU pin 26, ordinary GPIO output |
| 4 | SCL | LCD_SCK: PB13, MCU pin 25, SPI2_SCK AF0 |
| 5 | SDA | LCD_MOSI: PB15, MCU pin 27, SPI2_MOSI AF0 |
| 6 | RESET | LCD_RST: PB10, MCU pin 22; 10 kOhm pull-up R14 |
| 7 | NC | Intentionally unconnected |
| 8 | IOVCC | +3V0; C7 100 nF local bypass |
| 9 | VCI | +3V0; C8 100 nF local bypass |
| 10 | LEDA | USB_5V through R10 and R15 in parallel, 50 Ohm nominal |
| 11 | LEDK | Q1 drain, switched current return |
| 12 | GND | GND |

C9 adds 1 uF local bulk decoupling. C7-C9 use 0603 footprints; put the bypass
capacitors close to the socket and provide a short ground return. The display
supplies have a 3.3 V operating maximum. The shared 3.0 V rail leaves
240 mV of steady-state margin at the calculated upper corner. Check startup
and load transients on the [assembled board](hardware-bringup-audit.md).
PB14 is used as a GPIO; configure SPI2 for transmit-only operation rather
than enabling MISO there.

The supplier PDF has inconsistent controller labels (ST7789T3 in the general
table and ST7789V2 in the outline). Its appended example includes
panel-specific initialization settings, which the firmware sends at 2 MHz.
Verify the profile on the purchased sample. Confirm controller revision and
orientation offsets in bring-up. The socket pinout is consistent between the
outline and interface table.

### PWM backlight

The backlight uses a resistor-limited, low-side MOSFET circuit:

```text
USB_5V -> (R10 100 Ohm || R15 100 Ohm) -> J3.10 / LEDA
J3.11 / LEDK -> Q1 drain
Q1 source -> GND
PB0 / TIM3_CH3 AF1 -> LCD_BL_PWM -> R11 (100 Ohm) -> Q1 gate
Q1 gate -> R12 (100 kOhm) -> GND
```

Q1 is an Alpha & Omega AO3400A, SOT-23, C20917: gate=1, source=2, drain=3.
Its on-resistance is specified at 2.5 V gate drive, suitable for our 3.0 V GPIO.
R12 keeps the backlight off while the MCU GPIO is floating; high PWM turns it on.
The display lists 80 mA as its backlight operating point. This circuit
deliberately uses less: approximately (5.0 - 3.0) / 50 = **40 mA** while
on, or 40 mW in each resistor. At 5.5 V, an assumed 2.8 V LED drop and
-1% resistor tolerance, current is about 55 mA and power about 74 mW
per resistor. Check actual LED drop, resistor temperature and brightness
on the first board with the backlight at full duty.
This is not a regulated 80 mA driver; brightness varies with LED drop and USB
voltage, and PWM scales average current. Measure brightness/current on a sample
before changing the resistor. The backlight is supplied from USB_5V, avoiding
that load and its dissipation in the 3.0 V regulator.

## Schematic review before PCB layout

Reviewed on 21 October 2026 with KiCad CLI 10.0.7. Final ERC reports **zero
errors and zero warnings**, with no ERC exclusions. The 35 physical components in that revision
have LCSC/MPN fields and existing footprints; every symbol pin has a matching
numbered footprint pad. The final no-connect/metadata pass preserved all circuit
connections, existing UUIDs, wires, labels and symbol positions.

Completed the remaining sourcing fields: U2 is STMicroelectronics
[STM32G070CBT6 / C529338](https://www.lcsc.com/product-detail/microcontrollers-mcu-mpu-soc_st-stm32g070cbt6_C529338.html),
and the 3.0 V revision uses TI
[TPS7A2430DBVR / C2864435](https://jlcpcb.com/partdetail/TPS7A2430DBVR/C2864435)
for U1. The current [JLCPCB assembly files](../manufacturing/jlcpcb/)
include that regulator and C1. JLCPCB Tools writes fresh exports to
`production_files`. See the [assembly export notes](separate-parts.md) for
the project-local placement corrections.
The existing MCU and regulator footprints remain unchanged. Q1 and J3 now also
have explicit manufacturer and MPN fields alongside their existing LCSC fields.

### Intentionally unused MCU pins

A no-connect cross means the pin is deliberately left without a PCB connection.
It does not connect the pin to ground or change its electrical behaviour.

| Unused GPIOs in the installed symbol | U2 package pins | Reason |
|---|---|---|
| PC13 | 1 | No RTC/tamper or additional GPIO function needed |
| PC14, PC15 | 2, 3 | No external 32.768 kHz crystal |
| PF0, PF1 | 8, 9 | No external high-speed crystal; use internal HSI and PLL |
| PA6, PA7, PA8 | 17, 18, 28 | Spare GPIO/peripheral pins |
| PA9/PA11, PA10/PA12, PA15 | 33, 34, 37 | No UART or other functions assigned |
| PB1, PB2, PB11 | 20, 21, 23 | Spare GPIO/peripheral pins |
| PB3, PB4, PB5, PB6, PB7, PB8, PB9 | 42, 43, 44, 45, 46, 47, 48 | Spare GPIO/peripheral pins |
| PC6, PC7 | 30, 31 | Spare GPIO/peripheral pins |
| PD0, PD1, PD2, PD3 | 38, 39, 40, 41 | Spare GPIO/peripheral pins |

These account for the 27 previous ERC errors. Two further crosses mark package
pins 29 and 32 open: the installed KiCad symbol labels these `NC/PA9` and
`NC/PA10`, whereas ST's current DS12766 Rev 3 lists PA9 and PA10. Pins 33/34
default to PA11/PA12 and support remapping. This project uses none of these
four pins and does not depend on the symbol's NC interpretation. Recheck the
datasheet and symbol before reusing them in a later revision.

Configure unused GPIOs as analog inputs with no pull resistors in firmware,
leaving the external oscillators disabled. Keep PA13/PA14 enabled for SWD.
DS12766 also describes possible reset-time pull-downs on PA8, PB15, PD0 and PD2;
follow its SYSCFG UCPDx_STROBE startup guidance, including for our PB15 MOSI pin.

### Power, boot and interface checks

- VDD and VBAT are tied to +3V0, VSS to GND; VREF+ is tied to +3V0 with its
  100 nF capacitor. C3/C4 provide 100 nF plus 4.7 uF on the MCU supply, matching
  ST's supply scheme. Place these capacitors at the corresponding pins.
- The regulator has USB_5V on VIN/EN, 2.2 uF input capacitance and 4.7 uF output
  capacitance. NC remains open. The display backlight draws from USB_5V.
- NRST has the 10 kOhm pull-up, 100 nF capacitor and J2 connection. SWDIO and
  SWCLK reach PA13 and PA14 respectively, with target voltage sense and GND.
- PA14 also serves as BOOT0. RM0454's factory option-byte value has
  `nBOOT_SEL=1`, `nBOOT0=1`, `nBOOT1=1`: flash boot is selected through option
  bytes, so no external BOOT0 pull-down is required. Verify these settings
  during first programming and preserve the SWD configuration. Blank flash can
  enter the ROM bootloader, which reconfigures interface pins; program the
  board over SWD before testing the buttons/display.
- Buttons are active low with external 10 kOhm pull-ups; the two red LEDs are
  active high through 1 kOhm resistors. Their calculated GPIO currents are small.
- LCD uses SPI2 SCK/MOSI on PB13/PB15 (AF0), GPIO CS/DC/reset, and TIM3_CH3
  backlight PWM on PB0 (AF1). Configure SPI as transmit-only: PB14 is LCD_DC,
  not a MISO input. Q1's gate pull-down keeps the backlight off during reset.

These were the handoff checks for layout: short decoupling loops, regulator
copper and thermal performance, mounting holes, connector and display access,
and assembly orientation. In particular, retain the LED
polarity and header/display mechanical checks documented above; ERC cannot
verify those physical details. Prices and stock must be refreshed before ordering.

Boot reference: [ST RM0454, boot configuration and user option bytes](https://www.st.com/resource/en/reference_manual/rm0454-stm32g0x0-advanced-armbased-32bit-mcus-stmicroelectronics.pdf).
Pin, startup and power reference: [ST DS12766 Rev 3, Tables 11-13 and Figure 8](https://www.st.com/resource/en/datasheet/stm32g070cb.pdf).

## PCB, 3D model and enclosure plan

### Compact layout

The PCB is now **42 x 56 mm**, from (100, 78) to (142, 134), viewed from
front with increasing Y downward. This replaces the original 60 x 95 mm
outline: board area decreases from 5,700 to 2,352 mm2, or **58.7%**. This is a
PCB-area reduction, not a quoted manufacturing-cost reduction.

The portrait display body spans (102.9, 50) to (139.1, 101.8). It extends
28 mm above the PCB and must be independently supported by the printed case.
The combined display/PCB plan envelope is approximately 42 x 84 mm before case
walls and clearances. The case does not require PCB material under the whole
screen. Its front window and flex geometry remain subject to the sample fit test.

| Item | Centre / origin, mm | Orientation / intent |
|---|---|---|
| SW1 / UP | (121, 113) | 0 degrees; 6 mm printed-cap guide |
| SW2 / DOWN | (121, 127) | 0 degrees; 14 mm from UP |
| SW3 / LEFT | (114, 120) | 0 degrees; 6 mm cap |
| SW4 / RIGHT | (128, 120) | 0 degrees; 14 mm from LEFT |
| J1 / USB-C | (102.4, 96) | Faces left; mouth overhangs by 1.25 mm |
| J2 / SWD | pin 1 at (137.6, 108.5) | Row runs down the right edge, pins point right; pin 5 at (137.6, 118.66) |
| J3 / display socket | (121, 97) | 0 degrees; beneath lower end of display, mouth toward increasing Y |
| D1 / D2 | (107, 111) / (112, 111) | 0 degrees; below the display, left of UP |
| H1 / H2 | (104, 82) / (138, 82) | 2.7 mm unplated clearance holes |
| H3 / H4 | (104, 130) / (138, 130) | Same |

All electrical components remain on F.Cu for one-sided assembly. The 26 remaining
parts were re-optimized in functional groups for the compact outline; U2 is at
(121, 84.5), 0 degrees. See the [placement review](placement-review.md) for
all coordinates, optimization criteria and validation limits. Reference text was
repositioned for the new layout. The original footprint pin numbering and every
net assignment are unchanged.

The button cluster has approximately 9.9 mm between adjacent cap centres and
3.9 mm nominal gaps between 6 mm circular caps. Print an ergonomic fit piece
before freezing it; these smaller caps trade comfort for compactness. Plungers
contact only the switch actuators. The current case has no separate inward
travel stop; check switch travel on the first print.

The mounting holes retain 6 mm copper-exclusion areas on both layers, with
tracks, vias and copper fills prohibited. Their courtyards reserve component
space. User.Drawings graphics show display, cap and access envelopes; graphics
themselves are not keepout rules.

All nets are routed. The bottom GND pour follows the compact outline, and a
front GND pour and stitching vias reconnect areas separated by bottom traces.
KiCad reports zero board DRC violations and zero unrouted connections. The
schematic comparison reports only H1–H4, the four PCB-only mounting holes.
See the [routing review](routing-review.md) for the display and SWD
constraints, measurements, and bring-up checks.

J3's body and closed latch extend to Y=101.4. The display guide ends at
Y=101.8. The HS drawing gives 20.7 ± 0.5 mm of tail extension. Let the
tail leave the display toward the buttons, turn back underneath, and
enter J3 from the button side with the contacts down. This fold keeps
pin 1 on the left in the PCB front view. The nominal tail center is
about 0.4 mm right of the socket center with the display centered on its
guide; allow the display to shift sideways for alignment.

Keep the existing X=114..128, Y=101.5..107 guide clear and reserve the
narrow loop area X≈117..125.5 to at least Y=110.5 in the case. A simple
semicircle model, using illustrative radii of 2–3.5 mm and insertion of
2.5–3.5 mm, places the outer bend at Y≈108.5–109.8 with the longest
specified tail. These radii and insertion depths are modeling inputs,
not supplier limits. The modeled loop clears the switch and header in
plan view. Leave the latch accessible with the case open, allow room
above the PCB for the loop, and keep the stiffened end flat. Actual
insertion, bend radius and vertical clearance need a physical fit
check; the drawing check establishes nominal compatibility.

The USB port's nominal face overhangs the left PCB edge by 1.25 mm. The case
has a close-fitting opening around the receptacle and a wider recess outside
for the molded plug housing. The four shell anchors stay on the PCB. The
right-angle SWD header is accessed from the right side; keep room for jumper
housings and for solder tails below the PCB. The case supports the display
above the components.
LEDs need case openings or light pipes. Case dimensions and thickness are not
validated by PCB DRC.

### Original enclosure plan and sample checks

1. Obtain a display/socket sample. Check actual dimensions, tail thickness,
   contact side, pin numbering, socket fit, cable reach and bend arrangement.
   Bring up the display and establish acceptable brightness before finalising
   the board and case geometry.
2. Plan the display above the PCB, with four directional buttons in a comfortable
   arrangement. Decide USB-C, LEDs and J-Link access; add board mounting holes
   before routing. Reserve space for the flex, open socket latch and assembly
   tools. Keep components and sharp edges out of the cable path.
3. Export the PCB assembly as STEP from KiCad. Obtain or create a simplified
   display model including its glass/body, active area and flex envelope, plus
   the connector and latch clearance. Keep editable case CAD, drawings and
   print files in this Git repository when created.
4. Build a parametric two-piece case around the assembly. The display drawing
   gives a 51.8 x 36.2 mm body, about 2.05 mm thick, and a 40.8 x 30.6 mm active
   area. Verify these dimensions on the sample. Provide a bezel/window aligned
   to the active area, a frame supporting the display body, PCB standoffs,
   button openings/caps, LED openings and USB-C access. Avoid loading the glass
   or using the flex as a mechanical support. Include access for programming.
5. Print small fit-test pieces for the display cradle, socket clearance and
   button mechanism. Tune printer-specific clearances, then print a complete
   prototype. Keep screw/insert locations clear of PCB traces and the display.
6. Bench-test the assembled board, then disconnect USB and J-Link before fitting
   the display. Open J3's latch, insert the flex fully with contacts facing down
   and pin 1 aligned, then close the latch. Seat the display in its support,
   secure the PCB, check cable slack and close the case without pinching it.
   Reconnect power and test the display, brightness, buttons and LEDs.

The case provides mechanical support; the display is not soldered onto the PCB.
For the current model, print files and assembly order, see the
[enclosure notes](../mechanical/enclosure/README.md).

## References

- [Display purchase listing: HS20HS072RX / C5329582](https://www.lcsc.com/de/product-detail/LCD-Screen_span-style-background-color-ff0-HS-span-HS20HS072RX_C5329582.html)
- [Display datasheet](https://www.lcsc.com/datasheet/C5329582.pdf), outline and interface pages 10-11; electrical page 6.
- [Hirose FH12-12S-0.5SH(55)](https://www.hirose.com/en/product/p/CL0586-0704-0-55), including the FH12 series catalogue's mating-tail drawing.
- [Connector assembly listing / C88360](https://jlcpcb.com/partdetail/hrs_hirose-FH12_12S_0_5SH_55/C88360)
- [AO3400A datasheet](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)
- [STM32G070CB datasheet](https://www.st.com/resource/en/datasheet/stm32g070cb.pdf), alternate-function tables.

Selection and catalogue checks: 21 October 2026. Prices and availability are
snapshots; obtain the complete PCB assembly and separate display shipping quotes
before ordering.
