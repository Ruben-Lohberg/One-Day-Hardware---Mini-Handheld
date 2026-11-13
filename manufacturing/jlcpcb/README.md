# JLCPCB assembly files

Upload the [Gerber and drill ZIP](GERBER-mini_handheld.zip), [BOM](BOM-mini_handheld.csv), and [placement file](CPL-mini_handheld.csv) for the 3.0 V board. JLCPCB fits 34 components per board, including the display socket.

## Parts to fit by hand

| Part | Specification |
| --- | --- |
| J1 USB-C | HRO TYPE-C-31-M-12, [LCSC C165948](https://www.lcsc.com/product-detail/C165948.html) |
| J2 SWD | Right-angle 1 × 5 through-hole header, 2.54 mm pitch. Cut from a [W+P 946-14-036-00 strip](https://www.reichelt.de/de/de/shop/produkt/stiftleiste_rm_2_54mm_gewinkelt_1-reihig_36-polig-330986). |
| Display | HS20HS072RX, [LCSC C5329582](https://www.lcsc.com/product-detail/C5329582.html). Plug the flex into J3 with contacts facing the board and pin 1 aligned. |
| Screws | Four M2 × 5 mm and four M2 × 12 mm pan-head self-tapping screws per case. See the [enclosure notes](../../mechanical/enclosure/README.md) for head sizes. |

If you regenerate the files with JLCPCB Tools, exclude J1, J2, and mounting holes H1–H4 from the BOM and placement file. Use project rotation corrections of 180° for Q1 (AO3400A) and U1 (TPS7A2430DBVR), and verify both orientations in JLCPCB's placement preview.

## SWD header

Power the board via USB. Connect J2 to the 20-pin J-Link connector as shown below. Leave J-Link pin 19 (5 V supply) disconnected.

| J2 pin | Signal | J-Link pin |
| --- | --- | --- |
| 1 | VTref / 3.0 V sense | 1 |
| 2 | GND | 4 |
| 3 | SWDIO | 7 |
| 4 | SWCLK | 9 |
| 5 | nRESET | 15 |

Check for a short between USB VBUS and ground before powering the first board. Verify the 3.0 V rail, connect J-Link, and run the button and display diagnostics before trying Snake.
