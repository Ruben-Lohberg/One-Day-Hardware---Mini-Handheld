using System;
using System.IO;
using Antmicro.Renode.Core;

namespace Antmicro.Renode.Peripherals.SPI
{
    // Write-only, portrait ST7789 subset for this board. Pixel storage is big-endian RGB565.
    public class HandheldTft : ISPIPeripheral, IGPIOReceiver
    {
        public HandheldTft(IMachine machine) { this.machine = machine; }

        public ulong RejectedFrames { get; private set; }

        public void Reset()
        {
            selected = resetHeld = backlight = false;
            receiving = interrupted = false;
            RejectedFrames = resetStarted = readyAt = 0;
            ResetController(clearMemory: true);
        }

        public void OnGPIO(int number, bool value)
        {
            switch(number)
            {
                case 0: // PB12: CS#
                    if(receiving && selected == value) interrupted = true;
                    selected = !value;
                    break;
                case 1: // PB14: D/C
                    if(receiving && data != value) interrupted = true;
                    data = value;
                    break;
                case 2:                           // PB10: RESET#
                    if(receiving && resetHeld == value) interrupted = true;
                    if(!value && !resetHeld) resetStarted = Now;
                    if(value && resetHeld && Now - resetStarted >= 10_000)
                    {
                        ResetController();
                        readyAt = Now + 5_000_000;
                    }
                    if(resetHeld == value) dirty = true;
                    resetHeld = !value;
                    break;
                case 3:
                    if(backlight != value) dirty = true;
                    backlight = value;
                    break;
            }
        }

        public void BeginByte()
        {
            receiving = true;
            interrupted = !selected || resetHeld;
        }

        public void CompleteByte(byte value, bool wired)
        {
            receiving = false;
            if(!wired) return;
            if(interrupted || (readyAt != 0 && Now < readyAt)) { ++RejectedFrames; return; }
            readyAt = 0;
            Transmit(value);
        }

        public byte Transmit(byte value)
        {
            if(!selected || resetHeld) return 0;
            if(!data)
            {
                command = value;
                count = 0;
                highByte = true;
                switch(command)
                {
                    case 0x01: ResetController(); readyAt = Now + 5_000_000; break;
                    case 0x10: sleeping = true; dirty = true; readyAt = Now + 5_000_000; break;
                    case 0x11: sleeping = false; dirty = true; readyAt = Now + 5_000_000; break;
                    case 0x28: displayOn = false; dirty = true; break;
                    case 0x29: displayOn = true; dirty = true; break;
                    case 0x2c: x = x0; y = y0; break;
                }
                return 0;
            }

            switch(command)
            {
                case 0x2a:
                case 0x2b:
                    if(count >= args.Length) break;
                    args[count++] = value;
                    if(count == args.Length)
                    {
                        var first = (args[0] << 8) | args[1];
                        var last = (args[2] << 8) | args[3];
                        if(command == 0x2a) { x0 = first; x1 = last; }
                        else { y0 = first; y1 = last; }
                    }
                    break;
                case 0x36: orientation = value; break;
                case 0x3a: format = value; break;
                case 0x2c:
                case 0x3c:
                    if((format & 7) != 5 || (orientation & 0x20) != 0) break;
                    if(highByte) pixelHigh = value;
                    else WritePixel((ushort)((pixelHigh << 8) | value));
                    highByte = !highByte;
                    break;
            }
            return 0;
        }

        public void FinishTransmission() {}

        // Called by the host only while virtual time is paused.
        public string Capture(string path)
        {
            if(!dirty && File.Exists(path)) return "FRAME_UNCHANGED";
            File.WriteAllBytes(path, displayOn && !sleeping && !resetHeld && backlight ? pixels : black);
            dirty = false;
            return "FRAME_READY";
        }

        private void WritePixel(ushort pixel)
        {
            if(x0 > x1 || y0 > y1) return;
            if(x < Width && y < Height)
            {
                var col = (orientation & 0x40) != 0 ? Width - 1 - x : x;
                var row = (orientation & 0x80) != 0 ? Height - 1 - y : y;
                if((orientation & 8) != 0)
                    pixel = (ushort)(((pixel & 31) << 11) | (pixel & 0x07e0) | (pixel >> 11));
                var offset = 2 * (row * Width + col);
                pixels[offset] = (byte)(pixel >> 8);
                pixels[offset + 1] = (byte)pixel;
                dirty = true;
            }
            if(++x > x1)
            {
                x = x0;
                if(++y > y1) y = y0;
            }
        }

        private void ResetController(bool clearMemory = false)
        {
            if(clearMemory) Array.Clear(pixels, 0, pixels.Length);
            sleeping = true;
            displayOn = false;
            command = orientation = format = 0;
            highByte = dirty = true;
            count = x0 = y0 = x = y = 0;
            x1 = Width - 1;
            y1 = Height - 1;
        }

        private const int Width = 240, Height = 320;
        private ulong Now => machine.ElapsedVirtualTime.TimeElapsed.TotalNanoseconds;
        private readonly IMachine machine;
        private readonly byte[] pixels = new byte[Width * Height * 2];
        private readonly byte[] black = new byte[Width * Height * 2];
        private readonly byte[] args = new byte[4];
        private bool selected, data, resetHeld, backlight, displayOn, sleeping = true, highByte, dirty = true;
        private bool receiving, interrupted;
        private ulong resetStarted, readyAt;
        private byte command, orientation, format, pixelHigh;
        private int count, x0, x1 = Width - 1, y0, y1 = Height - 1, x, y;
    }
}
