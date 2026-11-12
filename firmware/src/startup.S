.syntax unified
.thumb

.section .vectors, "a", %progbits
.word _stack_top
.word Reset_Handler
.rept 13
.word Default_Handler
.endr
.word SysTick_Handler
.rept 32
.word Default_Handler
.endr

.section .text.Reset_Handler, "ax", %progbits
.global Reset_Handler
.type Reset_Handler, %function
.thumb_func
Reset_Handler:
    ldr r0, =_data_load
    ldr r1, =_data_start
    ldr r2, =_data_end
1:  cmp r1, r2
    bhs 2f
    ldmia r0!, {r3}
    stmia r1!, {r3}
    b 1b
2:  ldr r1, =_bss_start
    ldr r2, =_bss_end
    movs r3, #0
3:  cmp r1, r2
    bhs 4f
    stmia r1!, {r3}
    b 3b
4:  bl main

.type Default_Handler, %function
.thumb_func
Default_Handler:
    b Default_Handler

.weak SysTick_Handler
.thumb_set SysTick_Handler, Default_Handler
