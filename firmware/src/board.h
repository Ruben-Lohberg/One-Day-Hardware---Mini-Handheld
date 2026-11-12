#ifndef HANDHELD_BOARD_H
#define HANDHELD_BOARD_H

#include <stdbool.h>
#include <stdint.h>

enum {
    BUTTON_UP    = 1u << 0,
    BUTTON_DOWN  = 1u << 1,
    BUTTON_LEFT  = 1u << 2,
    BUTTON_RIGHT = 1u << 3,
};

void board_init(void);
uint32_t board_buttons(void);
void board_leds(bool led1, bool led2);
void board_clock_start(void);
uint32_t board_millis(void);

#endif
