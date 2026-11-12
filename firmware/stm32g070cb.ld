ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 128K
    SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 36K
}

_stack_top = ORIGIN(SRAM) + LENGTH(SRAM);

SECTIONS
{
    .vectors : { KEEP(*(.vectors)) } > FLASH
    .text : { *(.text*) *(.rodata*) } > FLASH
    .ARM.exidx : { *(.ARM.exidx*) } > FLASH
    .data : ALIGN(4) {
        _data_start = .;
        *(.data*)
        . = ALIGN(4);
        _data_end = .;
    } > SRAM AT > FLASH
    _data_load = LOADADDR(.data);
    .bss (NOLOAD) : ALIGN(4) {
        _bss_start = .;
        *(.bss*) *(COMMON)
        . = ALIGN(4);
        _bss_end = .;
    } > SRAM
    ASSERT(_bss_end <= _stack_top - 1024, "Reserve at least 1 KiB for the stack")
}
