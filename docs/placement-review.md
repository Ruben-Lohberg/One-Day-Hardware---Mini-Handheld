# Compact placement review

23 October 2026; KiCad 10.0.7. Placement stage before routing.

I reworked the arrangement for a smaller board. The PCB is 42 x 56 mm instead of 60 x 95 mm: 58.7% less board area. The
screen is supported by the printed case and overhangs the PCB's top edge by
28 mm. Its full body remains represented on User.Drawings.

USB-C now faces left, SWD is horizontal below/right of the display, LEDs sit
below/left of UP, and the four buttons form a smaller cross. Button-cap guides
are 6 mm in diameter; opposite centres are 14 mm apart. Mounting holes and their
6 mm copper keepouts moved with the new outline. No component types or electrical
connections were changed, and all electrical parts remain on the front side.

## Placement method

The mechanical parts were assigned compact coordinates first. A deterministic
Python/KiCad API search then re-optimized the other 26 components, keeping bypass,
reset, regulator and backlight circuits grouped by function. Four initial MCU
poses, coordinate-descent moves and 0.5 mm refinements were explored.

The objective was weighted half-perimeter wirelength, with additional weight on
LCD clock/data, lower weight on power distribution and GND omitted in favour of
its plane. This is an approximate connectivity metric, not routed length or a
global-optimality claim. It does not simulate return paths, signal coupling,
temperature or manufacturing price.

The search reserved at least 1 mm from ordinary component courtyards to the
board edge, avoided courtyard overlaps with 0.1 mm additional margin, kept parts
out of 6.6 mm square envelopes around the button caps, and left the FPC fold
corridor X=114..128, Y=101.5..107 empty. MCU/decoupling and regulator/input-output
capacitor groups retain deliberate local relationships. Q1/R10 centres remain
at least 12 mm from U2 as a geometric separation choice, not an isolation rating.
The fixed USB socket is an intentional edge-placement exception.

The compact grouped seed's objective decreased from 661.85 to 585.16 arbitrary units during this search. It is not directly equivalent to PCB area or routing cost.

## Coordinates

All coordinates are absolute KiCad mm, viewed from the front. All footprints
are on F.Cu; rotations are KiCad degrees.

| Reference | X | Y | Angle |
|---|---:|---:|---:|
| C1 | 103.800 | 102.550 | 180 |
| C2 | 112.200 | 102.550 | 0 |
| C3 | 114.200 | 85.200 | 180 |
| C4 | 110.500 | 84.500 | 180 |
| C5 | 114.200 | 83.000 | 180 |
| C6 | 114.200 | 89.400 | 180 |
| C7 | 121.750 | 92.000 | 90 |
| C8 | 124.250 | 92.000 | 90 |
| C9 | 119.250 | 92.000 | 90 |
| D1 | 107.000 | 111.000 | 0 |
| D2 | 112.000 | 111.000 | 0 |
| H1 | 104.000 | 82.000 | 0 |
| H2 | 138.000 | 82.000 | 0 |
| H3 | 104.000 | 130.000 | 0 |
| H4 | 138.000 | 130.000 | 0 |
| J1 | 104.000 | 96.000 | 270 |
| J2 | 133.000 | 111.000 | 90 |
| J3 | 121.000 | 97.000 | 0 |
| Q1 | 132.500 | 99.000 | 0 |
| R1 | 111.000 | 94.250 | 90 |
| R10 | 133.000 | 104.500 | 180 |
| R11 | 128.700 | 98.050 | 0 |
| R12 | 128.700 | 100.350 | 180 |
| R13 | 116.500 | 92.000 | 270 |
| R14 | 114.000 | 92.000 | 270 |
| R2 | 111.000 | 97.750 | 90 |
| R3 | 114.200 | 87.500 | 0 |
| R4 | 128.000 | 85.500 | 180 |
| R5 | 128.000 | 89.500 | 180 |
| R6 | 127.000 | 92.000 | 180 |
| R7 | 128.000 | 87.500 | 180 |
| R8 | 103.500 | 111.000 | 0 |
| R9 | 115.500 | 111.000 | 180 |
| SW1 | 121.000 | 113.000 | 0 |
| SW2 | 121.000 | 127.000 | 0 |
| SW3 | 114.000 | 120.000 | 0 |
| SW4 | 128.000 | 120.000 | 0 |
| U1 | 108.000 | 103.500 | 0 |
| U2 | 121.000 | 84.500 | 0 |

## Validation and remaining work

KiCad CLI DRC: zero violations; 82 unrouted connections remain. The bottom GND
zone was refilled. Independent checks verify 39 unique footprint references,
unchanged footprint/pad UUIDs and schematic links, identical pad nets and component
metadata, correct new outline/zone/hole positions, unchanged electrical rules,
and no added tracks or vias. A top copper/silkscreen/guide export was rendered
and visually inspected.

This does not verify routability, display contact orientation, flex bend radius,
case interference, package heights or thermal performance. Before ordering,
fit-test the 6 mm button caps and the display/socket/case stack. Most electronics
sit under the display; provide proper case supports and vertical clearance. SWD's
approximately 9.2 mm pin height remains the main tall item and needs a case-height
allowance, plus jumper housing space during programming. Keep short bypass supply
connections and nearby GND vias during routing; preserve bottom-plane continuity.
The socket and overall case geometry remain provisional pending this fit test.

### Ground routing — 2026-10-23

All GND pads now connect to the refilled B.Cu GND plane. Added 23 ordinary
0.8 mm / 0.3 mm through vias and 29 short 0.2 mm front-copper segments;
the existing C3 ground via and both existing supply segments were preserved.
USB ground pads connect to the grounded plated shell anchors. New via drills
remain outside all SMD solder pads; the MCU, regulator and display connector
have some vias beneath their bodies, clear of their solder pads.

KiCad CLI checks report zero DRC violations, zero unrouted GND connections,
and 55 remaining connections on other nets. Footprints, pad nets, component
positions, mechanical guides, electrical rules and zone settings were verified
unchanged. This is an intermediate routing state; power and signals still need
routing and the plane must be refilled and checked after further changes.
