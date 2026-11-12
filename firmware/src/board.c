#include "board.h"

// STM32G070 GPIO register layout (RM0454).
#define REG32(addr) (*(volatile uint32_t *)(addr))
#define RCC_IOPENR  REG32(0x40021034u)
#define GPIOA_MODER REG32(0x50000000u)
#define GPIOA_OTYPER REG32(0x50000004u)
#define GPIOA_PUPDR REG32(0x5000000cu)
#define GPIOA_IDR   REG32(0x50000010u)
#define GPIOA_BSRR  REG32(0x50000018u)

enum {
    BUTTON_PINS = 0x0fu,   // PA0–PA3, external pull-ups
    LED1_PIN = 1u << 4,
    LED2_PIN = 1u << 5,
    LED_PINS = LED1_PIN | LED2_PIN,
};

void board_init(void)
{
    RCC_IOPENR |= 1u;      // GPIOA clock
    (void)RCC_IOPENR;     // Allow clock enable to take effect
    GPIOA_BSRR = LED_PINS << 16;
    GPIOA_OTYPER &= ~(uint32_t)LED_PINS;
    GPIOA_PUPDR &= ~0xfffu;
    // Only change PA0–PA5. Leave PA13/PA14 configured for SWD.
    GPIOA_MODER = (GPIOA_MODER & ~0xfffu) | (1u << 8) | (1u << 10);
}

uint32_t board_buttons(void)
{
    return ~GPIOA_IDR & BUTTON_PINS;
}

void board_leds(bool led1, bool led2)
{
    const uint32_t on = (led1 ? LED1_PIN : 0u) | (led2 ? LED2_PIN : 0u);
    GPIOA_BSRR = on | ((LED_PINS & ~on) << 16);
}
