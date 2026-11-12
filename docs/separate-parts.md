# Parts to order separately

These parts go with the five-board assembly order.
JLCPCB populates the other 34 placements per board, including the J3
display socket. J1 and J2 are excluded from the assembly BOM and CPL;
their pads, slots and drill holes remain in the fabrication files.

Use the [current assembly files](../manufacturing/jlcpcb/).
To regenerate them, open JLCPCB Tools in the PCB Editor and click **Generate**.
The plugin writes to `mini_handheld/jlcpcb/production_files/`. The project-local
`mini_handheld/jlcpcb/project.db` stores the rotation corrections for Q1
(`^AO3400A$`) and U1 (`^TPS7A2430DBVR$`). Both export at 180° on this board.
Keep **Use global corrections** unchecked in the plugin's Corrections dialog
and confirm pin 1 in JLCPCB's placement preview before ordering.

| Item | Buy | Part |
| --- | --- | --- |
| J1 USB-C receptacle | **Ten**; five for this run and five spares | HRO **TYPE-C-31-M-12**, [LCSC C165948](https://www.lcsc.com/product-detail/C165948.html) |
| Fine soldering tip for J1 | **One** for all five boards | Ersa ERSADUR **0142PDLF03L/SB**, extended **0.3 mm** pencil point, for the iron currently fitted with **0142CDLF16**. [Reichelt](https://www.reichelt.com/de/en/shop/product/ersadur_soldering_tip_0_3_mm_pencil_tip_extended-331182?r=1) |
| J2 SWD header | **One 36-pin strip**, cut into five 1×5 headers plus spares | W+P **946-14-036-00**, right-angle, single-row male **2.54 mm** through-hole with 0.635 mm square pins and 6.1 mm mating pins. [Reichelt](https://www.reichelt.de/de/de/shop/produkt/stiftleiste_rm_2_54mm_gewinkelt_1-reihig_36-polig-330986) |
| Display | **Three** for the five-board run | HS **HS20HS072RX**, [LCSC C5329582](https://www.lcsc.com/product-detail/C5329582.html) |
| PCB mounting screws | **20**; four per case | **M2 × 5 mm** pan-head self-tapping screws from the kit below. Head diameter must be **3.5–4.3 mm** to bear on the PCB around its 2.7 mm holes. |
| Case closure screws | **20**; four per case | **M2 × 12 mm** pan-head self-tapping screws from the same kit. Heads up to **4.3 mm across × 1.55 mm tall** fit the back recesses. |

On 12 November 2026, LCSC quoted **$25.63** for three displays and ten
receptacles, including **$10.70** Germany shipping and the **$3.00** small-order
fee. Budget **about €39.42** after estimated VAT and import charges.

One [VooGenzek 800-piece M2 kit (GZ050T02, Amazon.de)](https://www.amazon.de/dp/B09NDMWBC2)
includes 100 screws of each required length and was listed at **€7.68**.
Measure one screw of each length against the head limits above before assembly.
The Amazon listing gives the thread diameter and length.

For the two cases on the current print plate, you need **eight of each screw
size**. Screw lengths are measured under the head. See the [enclosure assembly
notes](../mechanical/enclosure/README.md) for installation.

J2 mounts from the top and solders from the bottom. Keep the long pins
on top for the jumper leads. Pin 1 is the square pad next to the printed
`1`. Leave room in the enclosure for solder joints and lead ends below
the 1.6 mm board. J2 moved 3.5 mm toward the buttons relative to the
original SMD connector; refresh any imported enclosure STEP.

Use the part number on the fitted tip to identify the series. **0142CDLF16**
and **0142PDLF03L/SB** are both series 142. [Ersa catalog](https://kurtzersa.com/fileadmin/user_upload/download/Ersa-Soldering-Tools-Catalog-2026-en.pdf#page=44)
If the fitted tip reads **0102CDLF16**, the matching pencil tip is
**0102PDLF03L/SB** from series 102. [Ersa catalog](https://www.kurtzersa.com/fileadmin/KET/img/Ersa/download/Ersa-Soldering-Tools-Catalog-en.pdf#page=48) · [Conrad](https://www.conrad.de/de/p/ersa-0102pdlf03l-loetspitze-bleistiftform-spitzen-groesse-0-30-mm-inhalt-1-st-2202313.html)

J1 has 0.3 mm signal pads on 0.5 mm pitch. Use the pencil tip for the
signal pins and the existing 1.6 mm chisel tip for the four shell anchors.
Check the signal joints under magnification.
Before powering up, check VBUS to ground for a short. A stock of this
part is useful for repairs only when the target connector's contact
layout, anchor geometry and shell height match this exact receptacle.

Install the display by plugging its integral tail into J3. It is not a
soldering operation. Recheck stock and shipping together before buying.
