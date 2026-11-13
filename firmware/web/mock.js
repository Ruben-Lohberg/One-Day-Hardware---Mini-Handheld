const SPI_BYTE_US = 4; // 2 MHz, eight bits per byte.
const PIXEL_US = 2 * SPI_BYTE_US;
const WINDOW_US = 11 * SPI_BYTE_US; // CASET, RASET and RAMWR.
const INIT_US = 320_000 + 59 * SPI_BYTE_US; // Reset, sleep-out waits and initialization bytes.
const SCAN_US = 1_000_000 / 60; // ST7789 normal mode, C6h = 0Fh.
const TRANSITION_US = 15_000; // Approximate each transition as half the panel's typical Tr + Tf.

export class SnakeMock {
  static async create(wasm, width, height) {
    const mock = new SnakeMock(width, height);
    const {instance} = await WebAssembly.instantiate(wasm, {env: {
      board_init() {},
      board_leds() {},
      board_buttons: () => mock.readButtons(),
      board_clock_start: () => { mock.clockStartUs = mock.cpuUs; },
      board_millis: () => Math.floor((mock.cpuUs - mock.clockStartUs) / 1000),
      display_init: () => { mock.cpuUs += INIT_US; },
      display_fill: (x, y, w, h, color) => mock.write(x, y, w, h, color),
      display_blit: (x, y, w, h, pointer) => {
        // The next C call may reuse the strip buffer before the modeled write finishes.
        const pixels = new Uint16Array(instance.exports.memory.buffer, pointer, w * h).slice();
        mock.write(x, y, w, h, pixels);
      },
    }});
    mock.poll = instance.exports.snake_poll;
    instance.exports.snake_init();
    return mock;
  }

  constructor(width, height) {
    this.width = width;
    this.ram = new Uint16Array(width * height);
    this.scan = new Uint16Array(this.ram.length);
    this.previousScan = new Uint16Array(this.ram.length);
    this.cpuUs = 0;
    this.clockStartUs = 0;
    this.scanTimeUs = 0;
    this.nextScanUs = 0;
    this.buttons = 0;
    this.input = [];
    this.transfers = [];
  }

  setButtons(mask, timeUs) {
    this.input.push({mask, timeUs});
  }

  readButtons() {
    // Keep a quick tap visible for one poll even if both edges arrive together.
    if (this.input.length && this.input[0].timeUs <= this.cpuUs) {
      this.buttons = this.input.shift().mask;
    }
    return this.buttons;
  }

  write(x, y, width, height, pixels) {
    const startUs = this.cpuUs + WINDOW_US;
    this.transfers.push({x, y, width, count: width * height, pixels, startUs, sent: 0});
    this.cpuUs = startUs + width * height * PIXEL_US;
  }

  receivePixels(timeUs) {
    while (this.transfers.length) {
      const transfer = this.transfers[0];
      const arrived = Math.min(transfer.count, Math.floor((timeUs - transfer.startUs) / PIXEL_US));
      while (transfer.sent < arrived) {
        const column = transfer.sent % transfer.width;
        const row = Math.floor(transfer.sent / transfer.width);
        const count = Math.min(transfer.width - column, arrived - transfer.sent);
        const offset = (transfer.y + row) * this.width + transfer.x + column;
        if (typeof transfer.pixels === "number") {
          this.ram.fill(transfer.pixels, offset, offset + count);
        } else {
          this.ram.set(transfer.pixels.subarray(transfer.sent, transfer.sent + count), offset);
        }
        transfer.sent += count;
      }
      if (transfer.sent < transfer.count) break;
      this.transfers.shift();
    }
  }

  advance(timeUs) {
    while (this.cpuUs <= timeUs) {
      if (!this.poll()) {
        // The STM32 sleeps until the next 1 ms SysTick when it has no work.
        const elapsed = this.cpuUs - this.clockStartUs;
        this.cpuUs = this.clockStartUs + (Math.floor(elapsed / 1000) + 1) * 1000;
      }
    }
    while (this.nextScanUs <= timeUs) {
      this.receivePixels(this.nextScanUs);
      [this.previousScan, this.scan] = [this.scan, this.previousScan];
      this.scan.set(this.ram);
      this.scanTimeUs = this.nextScanUs;
      this.nextScanUs += SCAN_US;
    }
  }

  paint(rgba, timeUs) {
    const mix = Math.min(1, (timeUs - this.scanTimeUs) / TRANSITION_US);
    for (let i = 0, j = 0; i < this.scan.length; i++, j += 4) {
      const from = this.previousScan[i], to = this.scan[i];
      const red = from >> 11, green = (from >> 5) & 63, blue = from & 31;
      rgba[j] = (red + ((to >> 11) - red) * mix) * 255 / 31;
      rgba[j + 1] = (green + (((to >> 5) & 63) - green) * mix) * 255 / 63;
      rgba[j + 2] = (blue + ((to & 31) - blue) * mix) * 255 / 31;
      rgba[j + 3] = 255;
    }
  }
}
