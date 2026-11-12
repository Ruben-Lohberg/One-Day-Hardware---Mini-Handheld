using System.Collections.Generic;
using Antmicro.Renode.Core;
using Antmicro.Renode.Core.Structure;
using Antmicro.Renode.Logging;
using Antmicro.Renode.Peripherals.Bus;
using Antmicro.Renode.Peripherals.Timers;
using Antmicro.Renode.Time;

namespace Antmicro.Renode.Peripherals.Miscellaneous
{
    // The board's HSI16 reset clock and the gates used by the display driver.
    // Other clock sources are deliberately unsupported, not simulated at HSI16 speed.
    public sealed class HandheldRcc : IDoubleWordPeripheral, IKnownSize
    {
        public long Size => 0x400;
        public bool GpioBEnabled => (ioEnable & 2) != 0;
        public bool Spi2Enabled => (apb1Enable & (1u << 14)) != 0;
        public bool SyscfgEnabled => (apb2Enable & 1) != 0;
        public bool UsesResetClock => (cr & (1u << 8)) != 0 && (cfgr & 0x7f07) == 0;

        public void Reset()
        {
            cr = 1u << 8;
            cfgr = ioEnable = apb1Enable = apb2Enable = 0;
        }

        public uint ReadDoubleWord(long offset)
        {
            switch(offset)
            {
                case 0: return cr | ((cr & (1u << 8)) << 2); // HSI ready
                case 8: return cfgr;
                case 0x34: return ioEnable;
                case 0x3c: return apb1Enable;
                case 0x40: return apb2Enable;
                default: this.LogUnhandledRead(offset); return 0;
            }
        }

        public void WriteDoubleWord(long offset, uint value)
        {
            switch(offset)
            {
                case 0: cr = value; break;
                case 8: cfgr = value; break;
                case 0x34: ioEnable = value; break;
                case 0x3c: apb1Enable = value; break;
                case 0x40: apb2Enable = value; break;
                default: this.LogUnhandledWrite(offset, value); break;
            }
        }

        private uint cr = 1u << 8, cfgr, ioEnable, apb1Enable, apb2Enable;
    }

    public sealed class HandheldSyscfg : IDoubleWordPeripheral, IKnownSize
    {
        public HandheldSyscfg(HandheldRcc rcc) { this.rcc = rcc; }
        public long Size => 0x400;
        public bool Pb15Released => (cfgr1 & (1u << 9)) != 0;
        public void Reset() { cfgr1 = 0; }
        public uint ReadDoubleWord(long offset) => rcc.SyscfgEnabled && offset == 0 ? cfgr1 : 0;
        public void WriteDoubleWord(long offset, uint value)
        {
            if(rcc.SyscfgEnabled && offset == 0) cfgr1 = value;
        }
        private readonly HandheldRcc rcc;
        private uint cfgr1;
    }
}

namespace Antmicro.Renode.Peripherals.SPI
{
    using Miscellaneous;

    // STM32G070 SPI2 in the mode wired on this PCB: mode-0, 8-bit, one-wire
    // master transmitter, GPIO chip select. Time is virtual, not host wall time.
    public sealed class HandheldSpi2 : NullRegistrationPointPeripheralContainer<ISPIPeripheral>,
        IDoubleWordPeripheral, IWordPeripheral, IBytePeripheral, IKnownSize
    {
        public HandheldSpi2(IMachine machine, HandheldRcc rcc, HandheldSyscfg syscfg) : base(machine)
        {
            this.rcc = rcc;
            this.syscfg = syscfg;
            bus = machine.GetSystemBus(this);
            timer = new LimitTimer(machine.ClockSource, ClockHz, this, "SPI2 shift",
                limit: 64, direction: Direction.Ascending, workMode: WorkMode.OneShot, eventEnabled: true);
            timer.LimitReached += CompleteByte;
            Reset();
        }

        public long Size => 0x400;
        public uint ClockDivider => 2u << (int)((cr1 >> 3) & 7);
        public uint BitRate => ClockHz / ClockDivider;
        public ulong WireBytes { get; private set; }
        public ulong RejectedBytes { get; private set; }
        public ulong WireCycles { get; private set; }
        public bool Busy => shifting;

        public string Status()
        {
            var medium = (bus.ReadDoubleWord(0x50000408) & 0xcc000000) == 0x44000000;
            var panelRejected = (RegisteredPeripheral as HandheldTft)?.RejectedFrames ?? 0;
            return $"SPI2_STATUS {BitRate} {WireBytes} {WireCycles} {RejectedBytes} {panelRejected} " +
                $"{(Busy ? 1 : 0)} {(medium ? 1 : 0)} {(syscfg.Pb15Released ? 1 : 0)}";
        }

        public override void Reset()
        {
            timer.Reset();
            fifo.Clear();
            shifting = false;
            cr1 = 0;
            cr2 = 0x700;
            WireBytes = RejectedBytes = WireCycles = 0;
        }

        public uint ReadDoubleWord(long offset)
        {
            if(!rcc.Spi2Enabled) return 0;
            switch(offset)
            {
                case 0: return cr1;
                case 4: return cr2;
                case 8:
                    // FTLVL encodes empty, quarter, half (2 or 3), or full.
                    var level = fifo.Count == 4 ? 3u : fifo.Count >= 2 ? 2u : (uint)fifo.Count;
                    return (level << 11) | (fifo.Count <= 2 ? 2u : 0u) | (Busy ? 0x80u : 0u);
                case 12: return 0; // The panel has no read wire.
                default: this.LogUnhandledRead(offset); return 0;
            }
        }

        public void WriteDoubleWord(long offset, uint value)
        {
            if(!rcc.Spi2Enabled) return;
            switch(offset)
            {
                case 0: cr1 = value & 0xffff; break;
                case 4: cr2 = value & 0xffff; break;
                case 12: EnqueuePacked((ushort)value); break;
                default: this.LogUnhandledWrite(offset, value); break;
            }
        }

        public byte ReadByte(long offset) => (byte)ReadDoubleWord(offset);
        public ushort ReadWord(long offset) => (ushort)ReadDoubleWord(offset);
        public void WriteByte(long offset, byte value)
        {
            if(offset == 12) Enqueue(value);
            else WriteDoubleWord(offset, value);
        }
        public void WriteWord(long offset, ushort value)
        {
            if(offset == 12) EnqueuePacked(value);
            else WriteDoubleWord(offset, value);
        }

        private void EnqueuePacked(ushort value)
        {
            Enqueue((byte)value);
            Enqueue((byte)(value >> 8));
        }

        private void Enqueue(byte value)
        {
            if(!rcc.Spi2Enabled) return;
            const uint modeMask = 0xffffu & ~(7u << 3); // Ignore only baud divider.
            const uint txMaster = (3u << 14) | (3u << 8) | (1u << 6) | (1u << 2);
            if(!rcc.UsesResetClock || (cr1 & modeMask) != txMaster || (cr2 & ~0x1000u) != 0x700)
            {
                Reject("SPI2 requires HSI16 and 8-bit mode-0 master transmit with software NSS");
                return;
            }
            if(fifo.Count == 4)
            {
                Reject("SPI2 TX FIFO overflow");
                return;
            }
            fifo.Enqueue(value);
            if(!shifting) StartByte();
        }

        private void StartByte()
        {
            current = fifo.Dequeue();
            shifting = true;
            (RegisteredPeripheral as HandheldTft)?.BeginByte();
            currentCycles = ClockDivider * 8;
            timer.Limit = currentCycles;
            timer.Value = 0;
            timer.Enabled = true;
        }

        private void CompleteByte()
        {
            WireCycles += currentCycles;
            var wired = false;
            // 66 ns minimum SCL write period for the HS20HS072RX module.
            if((ulong)currentCycles * 1_000_000_000 < 8ul * 66 * ClockHz)
                Reject("Display SCL exceeds the module's rated write speed");
            else if(!rcc.Spi2Enabled || !rcc.GpioBEnabled || !syscfg.Pb15Released ||
                (bus.ReadDoubleWord(0x50000400) & 0xcc000000) != 0x88000000 ||
                (bus.ReadDoubleWord(0x50000424) & 0xf0f00000) != 0)
                Reject("SPI2 display path requires GPIOB clock, PB13/PB15 AF0 and PB15 UCPD strobe");
            else if(RegisteredPeripheral != null)
            {
                ++WireBytes;
                wired = true;
            }
            if(RegisteredPeripheral is HandheldTft panel) panel.CompleteByte(current, wired);
            else if(wired) RegisteredPeripheral.Transmit(current);
            if(fifo.Count != 0) StartByte();
            else shifting = false;
        }

        private void Reject(string reason)
        {
            if(RejectedBytes++ == 0) this.Log(LogLevel.Warning, reason);
        }

        private const uint ClockHz = 16_000_000;
        private readonly HandheldRcc rcc;
        private readonly HandheldSyscfg syscfg;
        private readonly IBusController bus;
        private readonly LimitTimer timer;
        private readonly Queue<byte> fifo = new Queue<byte>(4);
        private uint cr1, cr2, currentCycles;
        private byte current;
        private bool shifting;
    }
}
