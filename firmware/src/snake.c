#include "board.h"
#include "display.h"
#include "snake.h"

enum {
    COLS = 16, ROWS = 20, CELLS = COLS * ROWS, TILE = 12,
    LEFT = 24, TOP = 52, STEP_MS = 150,
    BG = 0x1107, FIELD = 0x08c5, LINE = 0x326b, TEXT = 0xe77f,
    HEAD = 0x47f4, BODY = 0x2d50, FOOD = 0xfc87,
};

typedef enum { UP, DOWN, WEST, EAST } Direction;
typedef enum { READY, PLAYING, LOST, WON } Phase;

static uint16_t body[CELLS];
static unsigned tail, length;
static char digits[] = "000";
static uint16_t food;
static Direction direction, queued;
static Phase phase;
static bool turn_queued;
static uint32_t random_state = 0x37a4f24bu;
static uint32_t previous, deadline, border_deadline;
static unsigned border_edge, border_hue;

static const uint8_t glyphs[36][5] = {
    {7,5,5,5,7}, {2,6,2,2,7}, {7,1,7,4,7}, {7,1,7,1,7}, {5,5,7,1,1},
    {7,4,7,1,7}, {7,4,7,5,7}, {7,1,2,2,2}, {7,5,7,5,7}, {7,5,7,1,7},
    {2,5,7,5,5}, {6,5,6,5,6}, {7,4,4,4,7}, {6,5,5,5,6}, {7,4,6,4,7},
    {7,4,6,4,4}, {7,4,5,5,7}, {5,5,7,5,5}, {7,2,2,2,7}, {1,1,1,5,7},
    {5,5,6,5,5}, {4,4,4,4,7}, {5,7,7,5,5}, {5,7,7,7,5}, {7,5,5,5,7},
    {7,5,7,4,4}, {7,5,5,7,1}, {7,5,6,5,5}, {7,4,7,1,7}, {7,2,2,2,2},
    {5,5,5,5,7}, {5,5,5,5,2}, {5,5,7,7,5}, {5,5,2,5,5}, {5,5,2,2,2},
    {7,1,2,4,7},
};

static void text(unsigned x, unsigned y, const char *str, unsigned scale, uint16_t color)
{
    for (; *str; ++str, x += 4 * scale) {
        unsigned i;
        if (*str >= '0' && *str <= '9') i = (unsigned)(*str - '0');
        else if (*str >= 'A' && *str <= 'Z') i = 10u + (unsigned)(*str - 'A');
        else continue;
        for (unsigned row = 0; row < 5; ++row) {
            for (unsigned col = 0; col < 3; ++col) {
                if (glyphs[i][row] & (4u >> col))
                    display_fill(x + col * scale, y + row * scale, scale, scale, color);
            }
        }
    }
}

static unsigned index_at(unsigned offset)
{
    unsigned i = tail + offset;
    return i >= CELLS ? i - CELLS : i;
}

static uint16_t cell(unsigned x, unsigned y)
{
    return (uint16_t)(y * COLS + x);
}

static void tile(uint16_t p, uint16_t color)
{
    unsigned x = LEFT + (p & (COLS - 1)) * TILE;
    unsigned y = TOP + (p / COLS) * TILE;
    display_fill(x + 1, y + 1, TILE - 2, TILE - 2, color);
}

static void show_score(void)
{
    display_fill(186, 23, 24, 10, BG);
    text(186, 23, digits, 2, TEXT);
}

static void footer(const char *message, uint16_t color)
{
    display_fill(24, 300, 192, 12, BG);
    text(24, 301, message, 2, color);
}

static void new_game(void)
{
    tail = 0;
    digits[0] = digits[1] = digits[2] = '0';
    length = 3;
    body[0] = cell(5, 10);
    body[1] = cell(6, 10);
    body[2] = cell(7, 10);
    food = cell(10, 10);
    direction = queued = EAST;
    turn_queued = false;
    phase = READY;
    display_fill(LEFT, TOP, COLS * TILE, ROWS * TILE, FIELD);
    tile(body[0], BODY);
    tile(body[1], BODY);
    tile(body[2], HEAD);
    tile(food, FOOD);
    show_score();
    footer("PRESS AN ARROW", TEXT);
}

static bool occupied(uint16_t p, unsigned first)
{
    for (unsigned i = first; i < length; ++i)
        if (body[index_at(i)] == p) return true;
    return false;
}

static void place_food(void)
{
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    uint16_t candidate = (uint16_t)(((random_state & 0xffffu) * CELLS) >> 16);
    while (occupied(candidate, 0)) {
        if (++candidate == CELLS) candidate = 0;
    }
    food = candidate;
    tile(food, FOOD);
}

static void move(void)
{
    uint16_t head = body[index_at(length - 1)];
    int x = head & (COLS - 1), y = head / COLS;
    direction = queued;
    turn_queued = false;
    switch (direction) {
        case UP: --y; break;
        case DOWN: ++y; break;
        case WEST: --x; break;
        case EAST: ++x; break;
    }
    if (x < 0 || x >= COLS || y < 0 || y >= ROWS) {
        phase = LOST;
        return;
    }
    uint16_t next = cell((unsigned)x, (unsigned)y);
    bool grow = next == food;
    if (occupied(next, grow ? 0u : 1u)) {
        phase = LOST;
        return;
    }
    if (!grow) {
        tile(body[tail], FIELD);
        tail = index_at(1);
        --length;
    }
    body[index_at(length++)] = next;
    tile(head, BODY);
    tile(next, HEAD);
    if (grow) {
        if (++digits[2] > '9') {
            digits[2] = '0';
            if (++digits[1] > '9') { digits[1] = '0'; ++digits[0]; }
        }
        show_score();
        if (length == CELLS) phase = WON;
        else place_food();
    }
}

enum {
    BORDER_INSET = 5,
    BORDER_THICKNESS = 3,
    BORDER_WIDTH = DISPLAY_WIDTH - 2 * BORDER_INSET,
    BORDER_HEIGHT = DISPLAY_HEIGHT - 2 * BORDER_INSET,
    SIDE_HEIGHT = BORDER_HEIGHT - 2 * BORDER_THICKNESS,
    PERIMETER = 2 * (BORDER_WIDTH + SIDE_HEIGHT),
    HUE_COUNT = 6 * 64,
    HUE_SCALE = (HUE_COUNT << 16) / PERIMETER,
    BORDER_FRAME_MS = 33,
    BORDER_EDGES = 4,
};

static uint16_t strip[BORDER_THICKNESS * SIDE_HEIGHT];

static uint16_t rainbow(unsigned phase, unsigned distance)
{
    unsigned hue = phase + ((distance * HUE_SCALE) >> 16);
    if (hue >= HUE_COUNT) hue -= HUE_COUNT;
    const unsigned rising = hue & 63u;
    const unsigned falling = 63u - rising;
    unsigned red, green, blue;
    switch (hue >> 6) {
    case 0: red = 63;      green = rising;  blue = 0;       break;
    case 1: red = falling; green = 63;      blue = 0;       break;
    case 2: red = 0;       green = 63;      blue = rising;  break;
    case 3: red = 0;       green = falling; blue = 63;      break;
    case 4: red = rising;  green = 0;       blue = 63;      break;
    default: red = 63;     green = 0;       blue = falling; break;
    }
    return (uint16_t)(((red >> 1) << 11) | (green << 5) | (blue >> 1));
}

static void horizontal_edge(unsigned y, unsigned phase, unsigned start, bool reverse)
{
    for (unsigned x = 0; x < BORDER_WIDTH; ++x) {
        const unsigned offset = reverse ? BORDER_WIDTH - 1 - x : x;
        const uint16_t color = rainbow(phase, start + offset);
        for (unsigned row = 0; row < BORDER_THICKNESS; ++row) {
            strip[row * BORDER_WIDTH + x] = color;
        }
    }
    display_blit(BORDER_INSET, y, BORDER_WIDTH, BORDER_THICKNESS, strip);
}

static void vertical_edge(unsigned x, unsigned phase, unsigned start, bool reverse)
{
    for (unsigned y = 0; y < SIDE_HEIGHT; ++y) {
        const unsigned offset = reverse ? SIDE_HEIGHT - 1 - y : y;
        const uint16_t color = rainbow(phase, start + offset);
        for (unsigned col = 0; col < BORDER_THICKNESS; ++col) {
            strip[y * BORDER_THICKNESS + col] = color;
        }
    }
    display_blit(x, BORDER_INSET + BORDER_THICKNESS, BORDER_THICKNESS, SIDE_HEIGHT, strip);
}

static void draw_border_edge(unsigned hue, unsigned edge)
{
    switch (edge) {
    case 0:
        horizontal_edge(BORDER_INSET, hue, 0, false);
        break;
    case 1:
        vertical_edge(DISPLAY_WIDTH - BORDER_INSET - BORDER_THICKNESS, hue, BORDER_WIDTH, false);
        break;
    case 2:
        horizontal_edge(DISPLAY_HEIGHT - BORDER_INSET - BORDER_THICKNESS, hue,
                        BORDER_WIDTH + SIDE_HEIGHT, true);
        break;
    case 3:
        vertical_edge(BORDER_INSET, hue, 2 * BORDER_WIDTH + SIDE_HEIGHT, true);
        break;
    }
}

void snake_init(void)
{
    board_init();
    display_init();
    const unsigned bottom = TOP + ROWS * TILE;
    display_fill(0, 0, DISPLAY_WIDTH, TOP, BG);
    display_fill(0, bottom, DISPLAY_WIDTH, DISPLAY_HEIGHT - bottom, BG);
    display_fill(0, TOP, LEFT, ROWS * TILE, BG);
    display_fill(LEFT + COLS * TILE, TOP, DISPLAY_WIDTH - LEFT - COLS * TILE,
                 ROWS * TILE, BG);
    text(24, 19, "SNAKE", 3, HEAD);
    text(134, 23, "SCORE", 2, TEXT);
    display_fill(LEFT - 1, TOP - 1, COLS * TILE + 2, 1, LINE);
    display_fill(LEFT - 1, bottom, COLS * TILE + 2, 1, LINE);
    display_fill(LEFT - 1, TOP, 1, ROWS * TILE, LINE);
    display_fill(LEFT + COLS * TILE, TOP, 1, ROWS * TILE, LINE);
    new_game();
    board_clock_start();
    previous = board_buttons();
    border_deadline = BORDER_FRAME_MS;
}

bool snake_poll(void)
{
    uint32_t buttons = board_buttons();
    uint32_t pressed = buttons & ~previous;
    previous = buttons;
    uint32_t now = board_millis();
    if (pressed && (phase == LOST || phase == WON)) {
        new_game();
        board_leds(false, false);
    } else if (pressed) {
        if (phase == READY) {
            phase = PLAYING;
            deadline = now + STEP_MS;
            footer("FIND THE FOOD", TEXT);
        }
        if (!turn_queued) {
            for (unsigned i = 0; i < 4; ++i) {
                if ((pressed & (1u << i)) && i != (unsigned)direction &&
                    i != ((unsigned)direction ^ 1u)) {
                    queued = (Direction)i;
                    turn_queued = true;
                    break;
                }
            }
        }
    }
    if (phase == PLAYING && (int32_t)(now - deadline) >= 0) {
        move();
        deadline += STEP_MS;
        if (phase == LOST) {
            footer("GAME OVER  RETRY", FOOD);
            board_leds(false, true);
        } else if (phase == WON) {
            footer("YOU WIN  RETRY", HEAD);
            board_leds(true, false);
        }
    }
    now = board_millis();
    if (border_edge == BORDER_EDGES && (int32_t)(now - border_deadline) >= 0) {
        border_edge = 0;
        border_deadline = now + BORDER_FRAME_MS;
        border_hue += 5;
        if (border_hue >= HUE_COUNT) border_hue -= HUE_COUNT;
    }
    // Poll buttons and check the game deadline between SPI writes.
    if (border_edge < BORDER_EDGES) {
        draw_border_edge(border_hue, border_edge++);
        return true;
    }
    return false;
}
