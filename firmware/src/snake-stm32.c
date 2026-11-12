#include "board.h"
#include "snake.h"

static volatile uint32_t milliseconds;

void SysTick_Handler(void)
{
    ++milliseconds;
}

void board_clock_start(void)
{
    *(volatile uint32_t *)0xe000e014u = 16000u - 1u;
    *(volatile uint32_t *)0xe000e018u = 0;
    *(volatile uint32_t *)0xe000e010u = 7;
}

uint32_t board_millis(void)
{
    return milliseconds;
}

int main(void)
{
    snake_init();
    for (;;) {
        if (!snake_poll()) __asm volatile("wfi");
    }
}
