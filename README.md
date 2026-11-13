# One-Day Hardware: Mini Handheld

I wanted to see how far I could get in one day with a small handheld of my own. I picked Snake because it gives me a good excuse to use a screen, four real buttons and a microcontroller. By the end of the build day I had a routed board, a case, firmware running in an emulator, orders placed for the boards and parts, and the first case and PCB fit model on the printer.

I started from an earlier schematic and rough layout. The commits replay the build in order using the original saves where I had them. I used **Codex GPT-6.1 sol** throughout the project: it helped with file edits, datasheet checks, scripts, simulations and the write-up. The interesting part for me was figuring out what to check at each step.

![FreeCAD render of the assembled mini handheld with a dark bezel and four orange buttons](docs/images/freecad-enclosure.png)

## Try it while the boards are in the mail

**[Play Snake in your browser](https://ruben-lohberg.github.io/One-Day-Hardware---Mini-Handheld/)**. Press an arrow key or tap the on-screen D-pad to start. The demo runs the same Snake C code as WebAssembly and models how pixels reach the TFT over SPI. It runs entirely in the browser.

To try the STM32 firmware in Renode, run this from the repo on Windows with Python 3, LLVM and Renode installed.

```powershell
.\firmware\run-web.ps1
```

Open [localhost:8765](http://127.0.0.1:8765/). The browser sends button presses to Renode and shows the pixels written by the STM32 firmware. See the [firmware notes](firmware/README.md#play-snake-in-the-browser) for the mock's timing assumptions and how to run it locally.

## 1. Major component decisions

I knew I wanted JLCPCB to assemble the boards so I wouldn't have to solder all the small parts by hand. I compared microcontroller prices on JLCPCB and display prices on LCSC to find an affordable pair with enough memory for the game and a screen I could drive over SPI. Codex GPT-6.1 sol helped me compare the parts and check the pinouts and flex drawings.

- **STM32G070CBT6.** This is a 48-pin Arm Cortex-M0+ with up to 64 MHz clock speed, 128 KB of flash and 36 KB of RAM. It had enough memory for Snake and enough pins for the buttons, LEDs, SPI display and SWD. JLCPCB could fit it as part of the assembly order. [ST specifications](https://www.st.com/en/microcontrollers-microprocessors/stm32g070cb.html) · [JLCPCB C529338](https://jlcpcb.com/partdetail/STM32G070CBT6/C529338)
- **HS20HS072RX.** This is a 240 × 320 color TFT with a roughly 2-inch diagonal, an ST7789-family controller, a four-wire SPI interface and a 12-pin flex. It was small enough for the handheld and let me send pixel updates straight to the display without keeping a full screen buffer in the STM32's RAM. I could order the display separately and have JLCPCB fit the flex socket. [LCSC C5329582](https://www.lcsc.com/product-detail/C5329582.html) · [Display datasheet](https://datasheet.lcsc.com/datasheet/pdf/75d064ee0eeae326e605dda9d4b98e7e.pdf?productCode=C5329582)

## 2. KiCad schematic

USB-C gives me 5 V. I kept USB data out of this first board and brought out five pins for a J-Link: power sense, ground, SWDIO, SWCLK and reset. Then I added an STM32G070, four switches with pull-ups and two red LEDs. That gave me something simple to test before asking the screen to do anything.

I used SPI for pixels, a GPIO for data/command and a PWM output for the backlight. I changed the logic rail from 3.3 V to 3.0 V to give the display supply more headroom and left the backlight on the USB rail. Codex GPT-6.1 sol helped cross-check the symbol pins and footprints against the drawings and run KiCad's electrical rule check.

[![KiCad export of the schematic showing USB power, the STM32, the display interface and the four buttons](docs/images/kicad-schematic.png)](docs/images/kicad-schematic.png)

The [KiCad project](mini_handheld/mini_handheld.kicad_pro) and [design notes](docs/design-notes.md) have the pinouts, part numbers and SWD wiring.

## 3. KiCad board

I chose surface-mount parts wherever I could and kept them on one side so JLCPCB could populate them in a single SMT assembly pass. That kept assembly costs down and left me two connectors to solder by hand. The right-angle SWD header is the through-hole exception, and the USB-C receptacle has surface-mount contacts and through-hole shell anchors.

My first outline was 60 × 95 mm. The display didn't need a board behind all of it, so I let the case carry the glass. That took the PCB down to **42 × 56 mm**. The display flex folds back under the panel into a bottom-contact socket. USB comes out on the left, SWD on the right, and the buttons stay in a cross below the display.

![KiCad plot of the two copper layers, board outline and front silkscreen](docs/images/kicad-routing.png)

On this board, the shortest trace wasn't always the one I wanted. I kept the display clock short but gave it more ground directly underneath, and spaced out the long SWD runs. Codex GPT-6.1 sol helped compare route lengths and the copper on the opposite layer. KiCad found **zero ERC violations, zero board DRC violations and zero unrouted connections**. The schematic parity check flagged the four mounting holes, which exist only on the PCB.

![KiCad 3D render of the populated board with the USB-C port, display socket, four switches and right-angle SWD header](docs/images/kicad-board.png)

Here are the [placement](docs/placement-review.md) and [routing](docs/routing-review.md) notes, including what the ground coverage check can tell me.

## 4. Electrical simulations

I wanted to see what the rail would do if USB sagged at the same time the load stepped up. With the USB source at 4.4 V and a simulated 25 → 75 mA load step, the 3.0 V rail dropped to **2.979 V** in the nominal case and **2.929 V** in the stress case. The deeper dip farther right is a separate input fault I added on purpose.

![ngspice plot comparing nominal and stress cases for the 3.0 V rail during a load step and a deeper USB input dip](docs/images/ngspice-power.svg)

Codex GPT-6.1 sol helped turn those questions into SPICE decks and compare the display clock edges with ST's IBIS output models. I chose medium GPIO slew and 2 MHz SPI for the first firmware. The regulator loop and flex are approximations; I'll measure the actual rail and SCK with the screen connected. The [simulation commands](sim/README.md) and [bring-up notes](docs/hardware-bringup-audit.md) have the assumptions and measurement points.

## 5. Emulation and firmware development

I started with the four buttons and two LEDs, then added a display diagnostic and finally Snake. The screen on the left below is the virtual panel. Renode runs the compiled Cortex-M0+ firmware, and the display model turns its SPI writes into RGB565 pixels. The arrows on the right feed the same active-low GPIO inputs the switches will use.

![Screenshot of the Renode browser front end showing Snake and the virtual D-pad](docs/images/renode-snake.png)

Codex GPT-6.1 sol helped with the STM32 code, Renode's SPI and display models, and the test scripts. The tests cover the buttons and LEDs, display updates, steering, growth, scoring, wall collisions and retry. I also checked that the model catches an early chip-select release and a missing PB15 setup bit. The [firmware notes](firmware/README.md) show how to run the checks.

## 6. FreeCAD enclosure

I exported a STEP file from KiCad and opened it in FreeCAD. The folded flex is the part I most wanted to see in 3D: it needs to reach the socket without the lid pinching it or the panel leaning on a component. The case carries the display on ledges and holds the PCB on four standoffs.

![FreeCAD fit study showing the orange display flex folded under the TFT and back toward the board socket](docs/images/freecad-display.png)

The case is **47.2 × 95.2 × 15.0 mm** before the buttons. It has a tray, a bezel and four individual plungers. The plunger lip holds each one in the bezel while the case is closed. I used Codex GPT-6.1 sol to help script the geometry and check clearances at rest and with a button pressed. Next I need to see how that feels in an actual print.

![FreeCAD view inside the lower tray with the PCB, display and folded flex installed](docs/images/freecad-tray.png)

The [FreeCAD model](mechanical/enclosure/enclosure.FCStd), [assembly notes and STLs](mechanical/enclosure/README.md) and [STEP export workflow](mechanical/README.md) are in the repo.

## 7. Order board and parts

I ordered a batch of five boards from JLCPCB, with the small surface-mount parts and the flex socket already fitted. I'll solder the USB-C receptacle and SWD header myself and plug in the separately ordered display. The [fabrication ZIP, BOM and placement file](manufacturing/jlcpcb/) are together, and the [separate parts list](docs/separate-parts.md) covers what the assembly order doesn't include. Codex GPT-6.1 sol helped compare part and feeder costs and check the export rotations for the MOSFET and regulator.

## 8. 3D print prototype

I started printing the enclosure and a PCB fit model while waiting for the parts. The fit model gives me the board outline, mounting holes and connector envelopes so I can check the tray and ports without risking a real board.

![Slicer preview of the tray, bezel, four plungers and PCB fit gauge on one plate](docs/images/slicer-preview.png)

This is the saved slicer preview of the fit-print arrangement. Use the [current STLs](mechanical/enclosure/README.md) when preparing a new print.

Here's what came off the printer: the tray, bezel, four button plungers, and printed stand-ins for the PCB and screen.

![The printed tray, bezel, PCB model, screen and four plungers still on the build plate](docs/images/fit-print-build-plate.jpg)

I dropped the printed PCB and screen into the tray. With the bezel beside it, I can see where the board sits and how the screen lines up with the window.

![The open tray with the printed PCB and screen in place, next to the bezel](docs/images/fit-print-open-case.jpg)

Here it is with the bezel on and all four buttons in place. From the side you can see where the connector opening lands.

| From the front | At an angle | From the side |
| --- | --- | --- |
| ![Front view of the printed handheld with four buttons and the screen stand-in](docs/images/fit-print-front.jpg) | ![Angled view of the closed fit prototype](docs/images/fit-print-angled.jpg) | ![Angled side view showing the connector opening](docs/images/fit-print-side.jpg) |

Once the parts are here, I'll add photos of the delivered boards and first assembly. On the bench I'll check for shorts, measure the 3.0 V rail, connect J-Link and run the button/LED and screen diagnostics before trying Snake. I still need to check the flex latch, USB plug clearance and switch travel on real parts.
