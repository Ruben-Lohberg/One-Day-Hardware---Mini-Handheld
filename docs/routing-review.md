# Routing goals and results

## Constraints

- Keep the outline, mounting holes, switches, LEDs, USB-C, display flex socket
  and SWD header fixed for the case. Keep the MCU and its bypass capacitors
  together, and preserve the existing power and ground routes.
- Keep the board on two copper layers. Preserve the ground pours and the
  mounting-hole copper exclusions. Use the existing board rules: 0.20 mm
  minimum trace width and clearance, 0.50 mm copper-to-edge clearance, and
  0.80 mm vias with 0.30 mm drills outside solder pads.
- Give the display clock first choice of a short route with nearby ground.
  Keep it under 15 mm and reduce the length without opposite-layer ground
  by at least 25%, without adding signal vias.
- Shorten display data where practical. Aim for at least 10% less MOSI
  length without increasing the via count. Accept an LCD_DC reroute only
  if it also preserves return coverage and avoids extra layer changes.
- Route SWCLK and SWDIO on the front, with at least 0.45 mm copper gap
  on long parallel runs beyond the MCU pin escape and at least 90% of
  each route directly backed by ground. No length matching is needed.
- Let buttons and indicator LEDs take detours when needed to make room
  for the clocks.

## Verified result

| Net | Trace length before → after | Length without ground directly opposite | Signal vias |
| --- | ---: | ---: | ---: |
| LCD_SCK | 11.3 → 12.4 mm | 8.9 → 6.2 mm | 2 → 2 |
| LCD_MOSI | 35.4 → 30.6 mm | 18.9 → 19.3 mm | 4 → 4 |
| SWCLK | 33.4 → 34.7 mm | 12.9 → 0.9 mm | 0 → 0 |
| SWDIO | 36.3 → 37.6 mm | 7.9 → 1.8 mm | 0 → 0 |

The tight SWD parallel gap improved from 0.20 mm to about 0.47 mm.
The main straight run has 0.50 mm between copper edges. MOSI is about
14% shorter; direct ground coverage did not improve along its whole route.
One added GND stitching via sits about 1.4 mm from a MOSI layer transition.
The shorter LCD_DC candidates made the ground reference worse or used more
vias, so that net was kept as routed. No footprints moved.

Ground coverage was estimated by sampling each trace centerline against
the filled GND polygons on the opposite layer. This flags geometric gaps;
it does not model return current, crosstalk, or the display flex. The
display clock still crosses gaps. Start bring-up with conservative SPI
and SWD clocks, then test at the intended settings.

KiCad reports zero board DRC violations and zero unrouted connections.
Schematic parity still reports only the four PCB-only mounting holes.
The via drill edges stay at least 0.15 mm outside the SMD pad bounds.
