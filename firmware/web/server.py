"""Local browser bridge for the STM32 ELF and SPI peripheral running in Renode."""
import argparse
from collections import deque
from contextlib import suppress
import errno
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import queue
import socket
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic


WEB = Path(__file__).resolve().parent
PLATFORMS = WEB.parent / "renode"
MOCK_FIRMWARE = WEB.parent / "build" / "handheld-snake.wasm"
DIRECTIONS = ("up", "down", "left", "right")
FRAME_SIZE = 240 * 320 * 2
BOOT_SECONDS = "1.3"  # Reset delays plus the first RGB565 screen at 2 Mbit/s.


class SimulatorServer(HTTPServer):
    # On Windows SO_REUSEADDR can let two simulators listen on the same port.
    allow_reuse_address = not hasattr(socket, "SO_EXCLUSIVEADDRUSE")
    allow_reuse_port = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Emulator:
    def __init__(self, renode, frame_path, script):
        self.frame_path = frame_path
        self.mask = 0
        self.lines = queue.Queue()
        self.log = deque(maxlen=20)
        config = frame_path.with_name("renode.config")
        config.write_text(f"[general]\nhistory-path = {frame_path.with_name('history')}\n",
                          encoding="utf-8")
        self.process = subprocess.Popen(
            [renode, "--console", "--disable-gui", "--plain", "--config", str(config),
             str(PLATFORMS / script)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            self.lines.put(line.strip())
        self.lines.put(None)

    def step(self, mask, seconds="0.033", force=False):
        commands = []
        for i, name in enumerate(DIRECTIONS):
            bit = 1 << i
            if (self.mask ^ mask) & bit:
                commands.append(f"sysbus.gpioPortA.{name} {'Press' if mask & bit else 'Release'}")
        commands += [f'emulation RunFor "{seconds}"',
                     "sysbus.spi2.lcd Capture " + json.dumps(self.frame_path.as_posix(), ensure_ascii=False)]
        result = self._exchange(commands, lambda s: s in ("FRAME_READY", "FRAME_UNCHANGED"))
        self.mask = mask
        if result == "FRAME_READY" or force:
            frame = self.frame_path.read_bytes()
            if len(frame) != FRAME_SIZE:
                raise ValueError("Renode produced an incomplete framebuffer")
            return frame
        return None

    def spi_status(self, *commands):
        line = self._exchange([*commands, "sysbus.spi2 Status"], lambda s: s.startswith("SPI2_STATUS "))
        keys = ("rate", "bytes", "cycles", "rejected", "panel_rejected", "busy", "medium", "pb15_released")
        return dict(zip(keys, map(int, line.split()[1:]), strict=True))

    def _exchange(self, commands, finished):
        try:
            self.process.stdin.write("\n".join(commands) + "\n")
            self.process.stdin.flush()
            end = monotonic() + 30
            while monotonic() < end:
                line = self.lines.get(timeout=max(0, end - monotonic()))
                if line is None:
                    break
                if finished(line):
                    return line
                if line:
                    self.log.append(line)
                if line.startswith(("There was an error executing", "No such command or device",
                                    "Errors during compilation", "Could not find file")):
                    break
        except (queue.Empty, OSError) as exc:
            raise RuntimeError("Renode stopped responding:\n" + "\n".join(self.log)) from exc
        raise RuntimeError("Renode could not step the display:\n" + "\n".join(self.log))

    def close(self):
        if self.process.poll() is None:
            try:
                self.process.stdin.write("quit\n")
                self.process.stdin.flush()
                self.process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                self.process.kill()
                self.process.wait()
        with suppress(OSError):
            self.process.stdin.close()
        self.process.stdout.close()


def handler(emulator, host):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host") != host:
                self.send_error(403)
                return
            if emulator is None and self.path == "/":
                self.send_response(302)
                self.send_header("Location", "/mock")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            assets = {"/": (WEB / "index.html", "text/html; charset=utf-8"),
                      "/app.js": (WEB / "app.js", "text/javascript; charset=utf-8"),
                      "/style.css": (WEB / "style.css", "text/css; charset=utf-8")}
            if emulator is None:
                assets.update({"/mock": assets["/"],
                               "/mock.js": (WEB / "mock.js", "text/javascript; charset=utf-8"),
                               "/snake.wasm": (MOCK_FIRMWARE, "application/wasm")})
            if self.path not in assets:
                self.send_error(404)
                return
            file, kind = assets[self.path]
            self.reply(200, file.read_bytes(), kind)

        def do_POST(self):
            if self.headers.get("Host") != host or self.headers.get("Origin") not in (None, "http://" + host):
                self.send_error(403)
                return
            if emulator is None or self.path != "/api/step":
                self.send_error(404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 128 or self.headers.get_content_type() != "application/json":
                    raise ValueError
                data = json.loads(self.rfile.read(size))
                mask, force = data["buttons"], data.get("frame", False)
                if type(mask) is not int or not 0 <= mask < 16 or type(force) is not bool:
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                self.send_error(400, "Expected a four-bit button mask")
                return
            try:
                frame = emulator.step(mask, force=force)
            except (RuntimeError, ValueError) as exc:
                print(exc, flush=True)
                self.send_error(503, "Renode stopped; restart the simulator")
                return
            self.reply(204 if frame is None else 200, frame or b"", "application/octet-stream")

        def reply(self, code, body, content_type):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return Handler


def sample(frame, x, y):
    offset = 2 * (y * 240 + x)
    return int.from_bytes(frame[offset:offset + 2], "big")


def verify_display(emulator):
    points = ((101, 105), (101, 213), (47, 159), (155, 159))
    base = emulator.step(0, seconds=BOOT_SECONDS, force=True)
    if sample(base, 0, 0) != 0x1107 or any(sample(base, *p) != 0x326b for p in points):
        raise RuntimeError("The firmware's initial RGB565 test card did not reach the display")
    for i, name in enumerate(DIRECTIONS):
        frame = emulator.step(1 << i, force=True)
        if any(sample(frame, *p) != (0x47f4 if i == j else 0x326b) for j, p in enumerate(points)):
            raise RuntimeError(f"Pressing {name} did not update the expected SPI-rendered tile")
        if emulator.step(0, force=True) != base:
            raise RuntimeError(f"Releasing {name} did not restore the display")
    print("Display smoke test passed: boot frame, all four GPIO presses, and release frames.", flush=True)


def verify_snake(emulator):
    def check(condition, message):
        if not condition:
            raise RuntimeError(message)

    def tile(frame, x, y):
        return sample(frame, 26 + x * 12, 54 + y * 12)

    def step(mask, time):
        return emulator.step(mask, seconds=time, force=True)

    def rectangle(frame, x, y, width, height):
        return b"".join(frame[2 * (row * 240 + x):2 * (row * 240 + x + width)]
                        for row in range(y, y + height))

    def interior(frame):
        return rectangle(frame, 8, 8, 224, 304)

    def edges(frame):
        strips = ((5, 5, 230, 3), (232, 8, 3, 304), (5, 312, 230, 3), (5, 8, 3, 304))
        return [rectangle(frame, *strip) for strip in strips]

    partial = step(0, "0.50")
    check(tile(partial, 7, 10) != 0x47f4, "First screen completed faster than the wire permits")
    base = step(0, "0.80")
    check(tile(base, 7, 10) == 0x47f4 and tile(base, 10, 10) == 0xfc87, "Missing initial game board")
    border = edges(base)
    colors = {pixel for edge in border for pixel in zip(edge[::2], edge[1::2])}
    check(len(colors) >= 100 and {(0xf8, 0x00), (0x07, 0xe0), (0x00, 0x1f)} <= colors,
          "The border is missing the expected RGB565 color range")
    for _ in range(3):
        idle = step(0, "0.033")
        check(interior(idle) == interior(base), "Snake moved before a button was pressed")
        next_border = edges(idle)
        check(all(before != after for before, after in zip(border, next_border, strict=True)),
              "The rainbow did not advance on all four edges")
        border = next_border
    step(8, "0.01")
    ate = step(0, "0.45")
    check(tile(ate, 10, 10) == 0x47f4 and tile(ate, 7, 10) == 0x2d50,
          "Snake did not advance and grow after eating")
    check(sample(base, 202, 23) != sample(ate, 202, 23), "Score did not change")
    check(all(before != after for before, after in zip(border, edges(ate), strict=True)),
          "The rainbow stopped animating during play")
    up = step(1, "0.15")
    check(tile(up, 10, 9) == 0x47f4, "Up did not turn the snake")
    reverse = step(2, "0.15")
    check(tile(reverse, 10, 8) == 0x47f4, "A 180-degree reversal was accepted")
    left = step(4, "0.15")
    check(tile(left, 9, 8) == 0x47f4, "Left did not turn the snake")
    lost = step(0, "1.6")
    check(sample(lost, 24, 301) == 0xfc87, "Wall collision did not end the game")
    check(interior(step(1, "0.5")) == interior(base), "Retry did not reset the board and score")
    print("Snake smoke test passed: rainbow border, start, growth, score, steering, "
          "reversal guard, wall collision, and retry.", flush=True)

    # Halt the CPU and let any queued border bytes drain before injecting a fault.
    status = emulator.spi_status("sysbus.cpu IsHalted true", 'emulation RunFor "0.000040"')
    check(status["rate"] == 2_000_000 and status["medium"] and status["pb15_released"],
          f"Unexpected firmware setup: {status}")
    check(status["bytes"] >= FRAME_SIZE and status["cycles"] == 64 * status["bytes"]
          and not (status["rejected"] or status["panel_rejected"] or status["busy"]),
          f"Unexpected SPI transfer totals: {status}")

    before = emulator.spi_status("sysbus WriteDoubleWord 0x50000418 0x50000000",
                                 "sysbus WriteByte 0x4000380c 0x00")
    check(before["busy"] and before["bytes"] == status["bytes"], "SPI sent a byte instantly")
    midway = emulator.spi_status('emulation RunFor "0.000003"')
    check(midway["busy"] and midway["bytes"] == status["bytes"], "SPI finished before 4 us")
    after = emulator.spi_status("sysbus WriteDoubleWord 0x50000418 0x1000",
                                'emulation RunFor "0.000005"')
    check(not after["busy"] and after["bytes"] == status["bytes"] + 1
          and after["panel_rejected"] == status["panel_rejected"] + 1,
          "Panel accepted a byte after CS changed mid-transfer")
    unstrobbed = emulator.spi_status("sysbus.syscfg Reset",
                                     "sysbus WriteDoubleWord 0x50000418 0x10000000",
                                     "sysbus WriteByte 0x4000380c 0x00",
                                     'emulation RunFor "0.000008"')
    check(not unstrobbed["pb15_released"] and unstrobbed["bytes"] == after["bytes"]
          and unstrobbed["rejected"] == after["rejected"] + 1,
          "SPI2 did not report missing PB15 strobe")
    print("SPI fidelity checks passed: medium slew, 2 MHz, 4 us byte, early CS, missing PB15 strobe.",
          flush=True)


def serve(port, emulator=None):
    host = f"127.0.0.1:{port}"
    try:
        server = SimulatorServer(("127.0.0.1", port), handler(emulator, host))
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE and getattr(exc, "winerror", None) not in (10048, 10013):
            raise
        raise SystemExit(f"Cannot listen on http://{host}/. Stop the existing simulator "
                         "with Ctrl+C or choose another port with -Port.") from None
    with server:
        if emulator is None:
            print(f"Snake timing mock: http://{host}/mock  (Ctrl+C to stop)", flush=True)
        else:
            print("Booting the display firmware in Renode…", flush=True)
            emulator.step(0, seconds=BOOT_SECONDS)
            print(f"Handheld simulator: http://{host}/  (Ctrl+C to stop)", flush=True)
        server.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--renode")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--display-demo", action="store_true")
    args = parser.parse_args()
    if args.mock:
        if not MOCK_FIRMWARE.is_file():
            parser.error("Build the timing mock with build.ps1 -App SnakeMock")
        try:
            serve(args.port)
        except KeyboardInterrupt:
            pass
        return
    if not args.renode:
        parser.error("--renode is required for STM32 emulation")
    with TemporaryDirectory(prefix="handheld-lcd-") as directory:
        emulator = Emulator(args.renode, Path(directory) / "frame.rgb565",
                            "display.resc" if args.display_demo else "snake.resc")
        try:
            if args.smoke_test:
                (verify_display if args.display_demo else verify_snake)(emulator)
                return
            serve(args.port, emulator)
        except KeyboardInterrupt:
            pass
        finally:
            emulator.close()


if __name__ == "__main__":
    main()
