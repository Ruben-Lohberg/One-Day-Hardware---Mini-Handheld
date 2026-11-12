# kicad_first_project

## Goal

USB-powered mini handheld for text experimants and playing Snake:
- four arrow buttons
- two programmable LEDs
- a small monochrome graphics display
- a microcontroller programmed with J-Link

## Proposed design

| Part | Plan |
|---|---|
| Power | USB-C supplying 5 V, with a regulator producing 3.3 V |
| Microcontroller | An STM32; exact model chosen after checking parts and cost |
| Controls | Four SMD buttons arranged as arrow keys |
| Indicators | Two LEDs, each controlled independently |
| Display | Target a 128 × 64 monochrome OLED |
| Programming | A header for your J-Link, using SWD |