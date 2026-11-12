#include "display.h"

#define REG32(addr) (*(volatile uint32_t *)(addr))
#define RCC_IOPENR REG32(0x40021034u)
#define RCC_APBENR1 REG32(0x4002103cu)
#define RCC_APBENR2 REG32(0x40021040u)
#define SYSCFG_CFGR1 REG32(0x40010000u)
#define GPIOB_MODER REG32(0x50000400u)
#define GPIOB_OSPEEDR REG32(0x50000408u)
#define GPIOB_BSRR REG32(0x50000418u)
#define GPIOB_AFRH REG32(0x50000424u)
#define SPI2_CR1 REG32(0x40003800u)
#define SPI2_CR2 REG32(0x40003804u)
#define SPI2_SR REG32(0x40003808u)
#define SPI2_DR8 (*(volatile uint8_t *)0x4000380cu)
#define SYST_CSR REG32(0xe000e010u)
#define SYST_RVR REG32(0xe000e014u)
#define SYST_CVR REG32(0xe000e018u)

enum {
    BL = 1u << 0, RESET = 1u << 10, CS = 1u << 12, DC = 1u << 14,
    TXE = 1u << 1, BSY = 1u << 7, FTLVL = 3u << 11,
};

static void delay_ms(unsigned ms)
{
    SYST_RVR = 16000u - 1u; // HSI16 after reset, no clock tree changes.
    SYST_CVR = 0;
    SYST_CSR = 5;
    while (ms--) {
        while (!(SYST_CSR & (1u << 16))) {}
    }
    SYST_CSR = 0;
}

static void send(uint8_t byte)
{
    while (!(SPI2_SR & TXE)) {}
    SPI2_DR8 = byte;
}

static void drain(void)
{
    // TXE allows further writes; it doesn't mean the FIFO or shift register is empty.
    while (SPI2_SR & FTLVL) {}
    while (SPI2_SR & BSY) {}
}

static void begin_command(uint8_t cmd)
{
    GPIOB_BSRR = (CS | DC) << 16;
    send(cmd);
    drain();
    GPIOB_BSRR = DC;
}

static void end_command(void)
{
    drain();
    GPIOB_BSRR = CS;
}

static void command(uint8_t cmd)
{
    begin_command(cmd);
    end_command();
}

void display_init(void)
{
    // HS20HS072RX module specification, pp. 19–20. The serial pixel format is RGB565.
    static const struct {
        uint8_t command, count, data[14];
    } panel_settings[] = {
        {0x36, 1, {0x00}},                          // Portrait, RGB
        {0x3a, 1, {0x05}},                          // Serial RGB565
        {0xb2, 5, {0x0c, 0x0c, 0x00, 0x33, 0x33}},  // Porch control
        {0xb7, 1, {0x35}},                          // Gate control
        {0xbb, 1, {0x20}},                          // VCOM
        {0xc0, 1, {0x2c}},                          // LCM control
        {0xc2, 1, {0x01}},                          // VDV/VRH command enable
        {0xc3, 1, {0x0b}},                          // VRH
        {0xc4, 1, {0x20}},                          // VDV
        {0xc6, 1, {0x0f}},                          // Frame rate
        {0xd0, 2, {0xa4, 0xa1}},                    // Power control
        {0xe0, 14, {0xd0, 0x03, 0x09, 0x0e, 0x11, 0x3d, 0x47,
                    0x55, 0x53, 0x1a, 0x16, 0x14, 0x1f, 0x22}}, // Positive gamma
        {0xe1, 14, {0xd0, 0x02, 0x08, 0x0d, 0x12, 0x2c, 0x43,
                    0x55, 0x53, 0x1e, 0x1b, 0x19, 0x20, 0x22}}, // Negative gamma
    };

    RCC_IOPENR |= 1u << 1;
    (void)RCC_IOPENR;
    RCC_APBENR1 |= 1u << 14;
    (void)RCC_APBENR1;
    RCC_APBENR2 |= 1u;
    (void)RCC_APBENR2;
    SYSCFG_CFGR1 |= 1u << 9; // Disconnect the power-on pull-down on PB15 (SPI2 MOSI).
    GPIOB_BSRR = (CS | RESET) | ((DC | BL) << 16);
    const uint32_t modes = (3u << 0) | (3u << 20) | (3u << 24) |
                           (3u << 26) | (3u << 28) | (3u << 30);
    GPIOB_AFRH &= ~((15u << 20) | (15u << 28)); // PB13/PB15 AF0: SPI2
    GPIOB_OSPEEDR = (GPIOB_OSPEEDR & ~((3u << 26) | (3u << 30))) |
                   (1u << 26) | (1u << 30); // Medium slew on SCK and MOSI.
    GPIOB_MODER = (GPIOB_MODER & ~modes) | (1u << 0) | (1u << 20) |
                  (1u << 24) | (2u << 26) | (1u << 28) | (2u << 30);
    GPIOB_BSRR = RESET << 16;
    SPI2_CR2 = (7u << 8) | (1u << 12); // 8-bit data and FIFO threshold
    // Master, mode 0, HSI16/8, software NSS, one-wire transmit-only.
    SPI2_CR1 = (1u << 2) | (2u << 3) | (1u << 8) | (1u << 9) |
               (1u << 14) | (1u << 15) | (1u << 6);

    delay_ms(20);
    GPIOB_BSRR = RESET;
    delay_ms(150);
    command(0x11);             // Sleep out
    delay_ms(150);
    for (unsigned i = 0; i < sizeof panel_settings / sizeof panel_settings[0]; ++i) {
        begin_command(panel_settings[i].command);
        for (unsigned j = 0; j < panel_settings[i].count; ++j) {
            send(panel_settings[i].data[j]);
        }
        end_command();
    }
    command(0x29);             // Display on
    GPIOB_BSRR = BL;
}

static void send16(uint16_t value)
{
    send((uint8_t)(value >> 8));
    send((uint8_t)value);
}

static void window(uint8_t cmd, unsigned first, unsigned last)
{
    begin_command(cmd);
    send16((uint16_t)first);
    send16((uint16_t)last);
    end_command();
}

static void begin_write(unsigned x, unsigned y, unsigned width, unsigned height)
{
    window(0x2a, x, x + width - 1);
    window(0x2b, y, y + height - 1);
    begin_command(0x2c);
}

void display_fill(unsigned x, unsigned y, unsigned width, unsigned height, uint16_t color)
{
    if (!width || !height || x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    if (width > DISPLAY_WIDTH - x) width = DISPLAY_WIDTH - x;
    if (height > DISPLAY_HEIGHT - y) height = DISPLAY_HEIGHT - y;
    begin_write(x, y, width, height);
    for (unsigned i = 0; i < width * height; ++i) send16(color);
    end_command();
}

void display_blit(unsigned x, unsigned y, unsigned width, unsigned height, const uint16_t *pixels)
{
    if (!width || !height || x >= DISPLAY_WIDTH || y >= DISPLAY_HEIGHT) return;
    if (width > DISPLAY_WIDTH - x || height > DISPLAY_HEIGHT - y) return;
    begin_write(x, y, width, height);
    for (unsigned i = 0; i < width * height; ++i) send16(pixels[i]);
    end_command();
}
