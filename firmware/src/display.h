#ifndef HANDHELD_DISPLAY_H
#define HANDHELD_DISPLAY_H

#include <stdint.h>

enum { DISPLAY_WIDTH = 240, DISPLAY_HEIGHT = 320 };
void display_init(void);
void display_fill(unsigned x, unsigned y, unsigned width, unsigned height, uint16_t color);
// Writes an in-bounds rectangle of RGB565 pixels in row-major order.
void display_blit(unsigned x, unsigned y, unsigned width, unsigned height, const uint16_t *pixels);

#endif
