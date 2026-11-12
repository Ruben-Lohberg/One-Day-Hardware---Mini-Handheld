# Five-board cost review

JLCONE quote viewed on 12 November 2026: **$48.31** for five assembled
boards, before shipping, taxes and the separately purchased displays.

| Line item | Batch |
| --- | ---: |
| Bare PCBs, including $1.20 lead-free finish | $3.20 |
| Setup and stencil | $9.79 |
| Components | $14.54 |
| Extended part feeder charges | $18.54 |
| SMT placement and nitrogen reflow | $2.24 |

The six Extended items on the quote were J1, J2, J3, R10, U1 and U2.
The fee works out to $3.09 per unique Extended item for this quote.
The switches and other passives are already Basic. U2 is the biggest
component expense at $7.43 for five; J3 is next at $2.61.

## Cost-down options for another revision

- R10: replace 47 ohms with two Basic C22775 100-ohm resistors in
  parallel (50 ohms, approximately 40 mA at 5 V with 3 V across the
  backlight, versus 43 mA today). This reuses the R11 SKU. With the
  existing conservative 5.5 V input and 2.8 V LED drop, each resistor
  dissipates at most about 74 mW at -1% resistance. Check the manufacturer's
  temperature derating for the enclosed board. This needs a schematic
  and local layout change; estimated savings are about $3 per batch.
- U1: JLCPCB lists the Torex XC6206P332MR-G (C5446) as Basic. It is a
  candidate for the logic rail only; the backlight is powered from USB.
  Its three-pin package and pinout require a board change. Check USB
  input headroom, transient load, thermal rise and effective ceramic
  capacitance before selecting it. Estimated savings: about $3.30 per
  batch at the observed small-quantity price, subject to requote.
- J2: omitting this header from assembly can avoid about $3.50 gross
  (part line plus feeder fee). Hand-solder the exact header on the
  existing board, or design probe pads and a jig in a later revision.
  Include the cost of the header or jig in the comparison.
- Keep J1, J3 and U2 for the first build. USB fit, the display tail and
  firmware memory are more important than an unverified substitution.
  Changing to another Extended component does not eliminate the feeder
  charge. Reducing PCB area does not remove any identified charge from
  this quote.

The cost-down revision implements the R10/R15 parallel pair and the
through-hole J2 row. Both J1 and J2 are hand fitted; see
[parts to order separately](separate-parts.md). The three removed Extended
items represent about $9.27 in feeder fees on the original quote, before
accounting for component changes, separate parts and shipping. Requote
the revision rather than using that number as the final savings.

The current board uses the 3.0 V TI TPS7A2430DBVR (C2864435) and the
2.2 µF C23630 input capacitor. The local JLCPCB catalog estimates a net
increase of $0.312 per board, or $1.56 for five, with the same Extended
feeder count. Requote the [current assembly files](../manufacturing/jlcpcb/)
before ordering. See the [bring-up audit](hardware-bringup-audit.md) for
voltage, capacitance and thermal estimates.
