"use strict";

const screen = document.querySelector("#screen");
const ctx = screen.getContext("2d");
const image = ctx.createImageData(screen.width, screen.height);
const status = document.querySelector("#status");
const keys = {ArrowUp: 1, ArrowDown: 2, ArrowLeft: 4, ArrowRight: 8};
const buttons = [...document.querySelectorAll("button[data-bit]")];
const held = new Map();
const pending = [];
let current = 0;
let needFrame = true;
let sendButtons = mask => pending.push(mask);

function setHeld(id, bit) {
  if (bit) held.set(id, bit);
  else held.delete(id);
  const next = [...held.values()].reduce((mask, direction) => mask | direction, 0);
  if (next === current) return;
  current = next;
  sendButtons(next);
  for (const button of buttons) button.classList.toggle("active", !!(next & Number(button.dataset.bit)));
}

for (const button of buttons) {
  const bit = Number(button.dataset.bit);
  button.addEventListener("pointerdown", event => {
    if (event.button !== 0) return;
    button.setPointerCapture(event.pointerId);
    setHeld("pointer" + event.pointerId, bit);
  });
  for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
    button.addEventListener(type, event => setHeld("pointer" + event.pointerId, 0));
  }
  button.addEventListener("click", event => {
    if (event.detail !== 0) return;
    setHeld("activate", bit);
    setHeld("activate", 0);
  });
}
window.addEventListener("keydown", event => {
  if (!Object.hasOwn(keys, event.key)) return;
  event.preventDefault();
  setHeld(event.key, keys[event.key]);
});
window.addEventListener("keyup", event => {
  if (!Object.hasOwn(keys, event.key)) return;
  event.preventDefault();
  setHeld(event.key, 0);
});
window.addEventListener("blur", () => {
  for (const id of held.keys()) setHeld(id, 0);
});

function draw(frame) {
  if (frame.byteLength !== screen.width * screen.height * 2) throw new Error("Incomplete framebuffer");
  const bytes = new Uint8Array(frame);
  for (let i = 0, j = 0; i < bytes.length; i += 2, j += 4) {
    const pixel = (bytes[i] << 8) | bytes[i + 1];
    image.data[j] = ((pixel >> 11) & 31) * 255 / 31;
    image.data[j + 1] = ((pixel >> 5) & 63) * 255 / 63;
    image.data[j + 2] = (pixel & 31) * 255 / 31;
    image.data[j + 3] = 255;
  }
  ctx.putImageData(image, 0, 0);
}

async function tick() {
  const started = performance.now();
  try {
    const response = await fetch("/api/step", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({buttons: pending.shift() ?? current, frame: needFrame}),
      signal: AbortSignal.timeout(35000),
    });
    if (!response.ok) throw new Error("Emulator disconnected");
    if (response.status === 200) draw(await response.arrayBuffer());
    needFrame = false;
    status.textContent = "● Live";
    status.dataset.state = "live";
    setTimeout(tick, Math.max(0, 33 - (performance.now() - started)));
  } catch {
    needFrame = true;
    pending.length = 0;
    status.textContent = "Disconnected";
    status.dataset.state = "error";
    setTimeout(tick, 1000);
  }
}
async function startMock() {
  document.querySelector("#runtime").textContent = "TIMING MOCK";
  status.textContent = "Loading Snake";
  try {
    const {SnakeMock} = await import("./mock.js");
    const response = await fetch("./snake.wasm");
    if (!response.ok) throw new Error("Snake mock build is missing");
    const mock = await SnakeMock.create(await response.arrayBuffer(), screen.width, screen.height);
    let timeUs = 0;
    let lastFrame = performance.now();
    const timeAt = now => timeUs + Math.min(100_000, Math.max(0, (now - lastFrame) * 1000));
    pending.length = 0;
    sendButtons = mask => mock.setButtons(mask, timeAt(performance.now()));
    sendButtons(current);
    status.textContent = "● Live";
    status.dataset.state = "live";
    function frame(now) {
      timeUs = timeAt(now);
      lastFrame = now;
      mock.advance(timeUs);
      mock.paint(image.data, timeUs);
      ctx.putImageData(image, 0, 0);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  } catch (error) {
    console.error(error);
    status.textContent = "Mock failed to load";
    status.dataset.state = "error";
  }
}

if (document.body.dataset.runtime === "mock" || location.pathname === "/mock") startMock();
else tick();
