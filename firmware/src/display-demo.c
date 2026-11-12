#include "board.h"
#include "display.h"

static void arrow(unsigned direction, bool pressed)
{
    static const uint8_t x[] = {100, 100, 46, 154};
    static const uint8_t y[] = {104, 212, 158, 158};
    const unsigned left = x[direction], top = y[direction];
    display_fill(left, top, 40, 40, pressed ? 0x47f4 : 0x326b);
    const uint16_t ink = pressed ? 0x0944 : 0xf7ff;
    for (unsigned row = 0; row < 10; ++row) {
        const unsigned width = 2 * row + 1;
        if (direction == 0) display_fill(left + 20 - row, top + 14 + row, width, 1, ink);
        if (direction == 1) display_fill(left + 20 - row, top + 24 - row, width, 1, ink);
        if (direction == 2) display_fill(left + 14 + row, top + 20 - row, 1, width, ink);
        if (direction == 3) display_fill(left + 24 - row, top + 20 - row, 1, width, ink);
    }
}

int main(void)
{
    board_init();
    display_init();
    display_fill(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT, 0x1107);
    display_fill(20, 22, 200, 2, 0x47f4);
    display_fill(20, 35, 200, 22, 0x2149);
    display_fill(30, 42, 52, 8, 0x47f4);
    display_fill(94, 42, 46, 8, 0x6d7f);
    display_fill(152, 42, 58, 8, 0xfdee);
    display_fill(100, 158, 40, 40, 0x2149);
    display_fill(20, 288, 200, 2, 0x326b);
    uint32_t previous = UINT32_MAX;
    for (;;) {
        const uint32_t buttons = board_buttons();
        const uint32_t changed = previous ^ buttons;
        if (changed) {
            previous = buttons;
            board_leds((buttons & (BUTTON_UP | BUTTON_DOWN)) != 0,
                       (buttons & (BUTTON_LEFT | BUTTON_RIGHT)) != 0);
            for (unsigned direction = 0; direction < 4; ++direction) {
                const uint32_t bit = 1u << direction;
                if (changed & bit) arrow(direction, (buttons & bit) != 0);
            }
        }
    }
}
