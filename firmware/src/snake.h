#ifndef HANDHELD_SNAKE_H
#define HANDHELD_SNAKE_H

#include <stdbool.h>

void snake_init(void);
// Returns true when the next poll should run without waiting for a clock tick.
bool snake_poll(void);

#endif
