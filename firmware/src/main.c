#include "board.h"

int main(void)
{
    board_init();
    for (;;) {
        const uint32_t buttons = board_buttons();
        board_leds((buttons & (BUTTON_UP | BUTTON_DOWN)) != 0,
                   (buttons & (BUTTON_LEFT | BUTTON_RIGHT)) != 0);
    }
}
