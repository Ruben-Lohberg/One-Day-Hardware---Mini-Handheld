# AI-assisted KiCad workflow

Research and local verification: 21 October 2026. Project: KiCad 10.0.7 on Windows.

Codex GPT-6.1 sol helped organize these checks and replay the main design
milestones from the saved project files.

## What works with this project

The schematic editor can stay open during assistant file edits. Use a controlled
save/edit/reload handoff; do not edit independently in both places at once.
The editor holds a separate in-memory document. Replacing the disk file alone
does not update that document, and a later editor save can overwrite the replacement.

This workflow was tested on the actual project while adding the reset circuit
and 20-pin J-Link SWD header:

1. Save the schematic in the existing editor window with Ctrl+S.
2. Preserve a byte-for-byte snapshot and its SHA-256 hash, including a copy of
   the project settings for validation. Prepare changes in a separate directory.
3. Export the candidate netlist and run ERC with the installed `kicad-cli`.
   Check intended component-pin connections and verify that existing circuit nets
   and symbol UUIDs are preserved. Export SVG and inspect the rendered layout.
4. Pause manual editing for the handoff. Check that the editor has no new unsaved
   changes and that the original file still matches the snapshot hash. A hash
   check only detects disk changes; the editor check is also necessary.
5. Write the validated candidate to a temporary sibling file, then atomically
   replace the schematic. Retain the original snapshot.
6. In the still-open editor, select **File > Revert** and confirm. This reloads
   the file now on disk. Only do this after saving the user's work: Revert
   discards the current in-memory document and its undo history.
7. Confirm the new circuitry is visible. Save once from the editor, export the
   netlist again, and verify that the changes survived the round trip.

This is coordinated editing with the editor open, not automatic merging of
simultaneous edits. No lock files need to be removed and no second editor
instance needs to be opened. No new AI plugin was installed for this test.

The review used KiCad CLI 10.0.7.
Use `sch erc --format json`, `sch export netlist --format kicadxml`, and
`sch export svg` for machine-readable and visual checks.

## Available approaches

| Approach | Schematic synchronization | Assessment |
|---|---|---|
| KiCad 10 official IPC API | Does not provide the supported live schematic editing API needed here | Appropriate for live PCB operations; insufficient for this schematic workflow |
| KiCad 11 development IPC API | Experimental schematic editing support has been announced | Closest architectural match for live editor transactions; not the installed stable version |
| Konnect / kicad-mcp | Schematics use direct file editing with atomic writes; PCBs use IPC; separate viewer refreshes from disk | Potentially useful automation, but a live viewer does not merge KiCad's editor buffer |
| KiCad AI Assistant | Offers schematic tools; README acknowledges schematic refresh limitations | Its documentation still recommends reloading after schematic edits |
| pcbGPT | Circuit-code generation, checking, previews, project import/export and synchronization | Useful generation workflow; no documented guarantee of concurrent merging with an open KiCad editor |

Recommendation: retain stable KiCad 10.0.7 and use the tested handoff for now.
Revisit the official schematic IPC API when KiCad 11 is stable. A plugin can
improve the tool interface, but file-based tools still need synchronization.

## The pcbGPT paper

The paper uses a Python circuit DSL, library/datasheet grounding, ERC, semantic
review, and iterative repair. Its web workflow synchronizes projects; it does not
establish simultaneous merging with KiCad's editor buffer. The reported best
pass@1 of 0.90 covers 20 schematic tasks, not fabrication success. The authors
explicitly exclude full PCB realization and guaranteed electrical correctness.

For our board, the useful practices are exact pin/library lookup, netlist checks,
ERC, rendered inspection, and human review. We retain the native KiCad schematic
as the editable source.

## Sources

- [KiCad IPC API status](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/index.html)
- [KiCad developer announcement: experimental schematic API, September 2026](https://forum.kicad.info/t/post-v10-new-features-and-development-news/66611/37)
- [KiCad 10 schematic File menu implementation](https://github.com/KiCad/kicad/blob/10.0/eeschema/menubar.cpp)
- [Konnect / kicad-mcp](https://github.com/obhox/kicad-mcp)
- [KiCad AI Assistant](https://github.com/paul356/KiCad-AI-Assistant)
- [pcbGPT paper, version 1](https://arxiv.org/html/2606.01188v1)
- [pcbGPT source and setup](https://github.com/tk-king/pcbGPT)

## Reset and SWD milestone (historical 20-pin version)

- R3: 10 kOhm from +3V3 to NRST; C6: 100 nF from NRST to GND.
- J2 pin 1: +3V3 voltage reference.
- J2 pin 7: SWDIO, MCU PA13 / pin 35.
- J2 pin 9: SWCLK, MCU PA14 / pin 36.
- J2 pin 15: NRST, MCU pin 10.
- J2 even pins 4 through 20: GND.
- J2 pins 2, 3, 5, 11, 13, 17 and 19: intentionally unconnected.
- The board remains powered by USB-C; J-Link target power is not connected.
- Physical connector sourcing and J2 footprint assignment are still pending.
- ERC at this milestone: 39 unconnected MCU pin errors, no other violations.

Pinout reference: [SEGGER SWD connector description](https://www.segger.com/products/debug-probes/j-link/technology/interface-description/).
The five-pin SWD milestone below supersedes this connector and its pin numbering.

## Directional buttons milestone

Each normally open button connects its GPIO net to GND when pressed. A separate
10 kOhm resistor connects that net to +3V3, so released reads 1 and pressed reads 0.
Configure PA0-PA3 as digital inputs in firmware; an internal pull-up is unnecessary
with these external resistors. Debounce in firmware, for example by accepting a
state after it has stayed unchanged for 10-20 ms, then tune using the actual switches.

| Button | Net | MCU GPIO / pin | Pull-up |
|---|---|---|---|
| SW1 / UP | BTN_UP | PA0 / 11 | R4, 10 kOhm |
| SW2 / DOWN | BTN_DOWN | PA1 / 12 | R5, 10 kOhm |
| SW3 / LEFT | BTN_LEFT | PA2 / 13 | R6, 10 kOhm |
| SW4 / RIGHT | BTN_RIGHT | PA3 / 14 | R7, 10 kOhm |

The schematic uses generic two-contact switch symbols. SMD switch selection,
footprints, and the physical arrow-key arrangement will be decided during sourcing
and PCB layout. For any four-terminal tactile switch, verify which terminals are
internally common before selecting the symbol/footprint combination.

ERC at this milestone: 35 unconnected MCU pin errors, no other violations.

## Files and CLI only handoff

The user now operates the editor save/reload actions. The assistant uses direct
file edits and `kicad-cli`, without GUI automation:

1. User saves the schematic and hands off editing.
2. Assistant snapshots, prepares, checks and applies the change, guarding against
   intervening disk edits.
3. User selects **File > Revert > Yes** before making further edits or saving.

The editor can stay open, but its old buffer must be reloaded before the next save.

## GPIO LEDs milestone

| LED | GPIO / MCU pin | Net | Series resistor |
|---|---|---|---|
| D1 | PA4 / 15 | LED_1 | R8, 1 kOhm |
| D2 | PA5 / 16 | LED_2 | R9, 1 kOhm |

Each branch is GPIO -> resistor -> LED anode (pin 2), with LED cathode (pin 1)
connected to GND. Configure the GPIOs as push-pull outputs: high turns the LED on,
low turns it off. Each LED needs its own series resistor. The current is roughly
(GPIO high voltage - LED forward voltage) / resistance; for example, 3.3 V and a
2.0 V LED give about 1.3 mA with 1 kOhm. Actual current and brightness depend on
the selected LED and the GPIO output voltage under load.

At this historical milestone, LED colors, supplier parts and SMD footprints were pending; the passive-sourcing milestone below resolves them. Recheck the resistor
values against those parts before ordering. Current expected ERC: 33 unconnected
MCU pin errors, no other violations. Polarity and all series connections were
verified in the CLI-exported netlist; ERC alone does not verify LED polarity.

## Display milestone

J3 is the Hirose FH12-12S-0.5SH(55) / C88360 socket for the separately purchased
HS20HS072RX / C5329582 display. The README records the mating geometry check,
pinout, current calculation and mechanical/enclosure plan. Added C7-C9 supply
decoupling, R13/R14 CS/reset pull-ups, and Q1/R10-R12 for a default-off PWM
backlight supplied from USB_5V. SPI2 uses PB13/PB15; CS/DC/reset use PB12/PB14/PB10;
PB0 provides TIM3_CH3 PWM. The sheet was expanded from A4 to A3.

Validation: exact J3, MOSFET and resistor nets checked in the CLI netlist;
existing connected nets and all pre-existing symbol instances preserved; unique
UUIDs; SVG rendered for visual review. ERC reports 27 unfinished MCU-pin errors
and no other warnings or errors. A physical mating/fit check remains before manufacture. The passive-sourcing
milestone below assigns the new passives. Reload the editor
using the handoff above after the assistant applies the disk change.

## Mechanical parts and five-pin SWD milestone

Assigned SW1-SW4 to TS-1088-AR02016 / C720477 and J1 to TYPE-C-31-M-12 / C165948
after checking their manufacturer drawings against the installed KiCad land
patterns. Kept button direction values visible; exact parts are in MPN/LCSC.

Replaced J2 with a five-pin connector while retaining its symbol UUID and the
pin UUIDs for the retained signals. J2 now uses DEALON DZ254S-11-05-48 / C5160788
and a project-local footprint. Pin order: 1=VTref/+3V3, 2=GND, 3=SWDIO,
4=SWCLK, 5=NRST. README documents the jumper mapping, footprint geometry,
USB shell retention and enclosure clearances. The previous 20-pin wires,
no-connects and unused cached symbol were removed.

Validation: CLI netlist equivalence for every existing circuit after removing
the old J2 endpoints; exact new J2 connections; unchanged MCU and display nets;
symbol-to-pad number coverage; rendered schematic review. ERC remains 27
unfinished MCU-pin errors with no other warnings or errors. The header has no
3D model until an accurate one is added for enclosure design.

## LED and passive sourcing milestone

Preserved the user's manual D1 assignment exactly and assigned D2, R1-R14 and
C1-C9 from the stock/price snapshot documented in README. All are Basic except
the 0.25 W 1206 backlight resistor R10. C2 increased from 1 uF to 4.7 uF for
regulator output capacitance margin; C2/C4 use 0805, other capacitors use 0603.
All new metadata is hidden; visible R/C values remain readable. Recorded the
supplier-vs-KiCad LED terminal-number mapping for assembly polarity review.

Validation: complete exported-netlist equivalence; all UUIDs, positions, wires,
labels and unrelated symbols preserved; exact part/footprint field checks;
two-terminal footprint pin coverage; schematic SVG rendered and inspected.
ERC remains 27 unfinished MCU-pin errors and no other warnings/errors. The
user must reload via File > Revert > Yes before editing or saving again.

## Final schematic review milestone

Added 27 no-connect markers at the unused MCU GPIO endpoints and two additional
markers on pins 29/32. The latter are labelled NC/PA9 and NC/PA10 in the
installed symbol; current ST DS12766 identifies PA9/PA10. Both remain unused,
so no symbol replacement or circuit change was needed. README records the full
pin review, internal-clock decision, boot option bytes and firmware startup notes.

Completed U1/U2 LCSC, manufacturer and MPN fields; completed J3/Q1 manufacturer
and MPN fields. Preserved every other symbol, including the user's D1, exactly.

Validation: KiCad CLI 10.0.7 ERC has zero errors/warnings and no exclusions;
all before/after net endpoint sets match; wires, labels, positions and existing
UUIDs match; all 35 physical parts have supplier/MPN fields and existing
footprints with full symbol-pin/pad coverage. Independently checked MCU power,
reset, GPIO, LCD and SWD pin assignments; exported and visually inspected SVG.
The standard project ERC settings were retained, including its existing disabled
footprint-filter advisory; actual footprint existence/pad coverage was checked
separately. This is schematic validation, not PCB DRC or assembly approval.

Save the backup, candidate, ERC report, netlists, footprint audit, and preview
in a temporary review folder.
Reload the editor with File > Revert > Yes before saving or editing again.
