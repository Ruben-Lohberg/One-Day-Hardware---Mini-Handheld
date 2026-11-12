param([ValidateSet('Gpio', 'Display', 'Snake', 'SnakeMock')][string]$App = 'Gpio')

$ErrorActionPreference = 'Stop'
$clang = (Get-Command clang -CommandType Application).Source
$out = Join-Path $PSScriptRoot 'build'
New-Item -ItemType Directory -Path $out -Force | Out-Null
if ($App -eq 'SnakeMock') {
    Get-Command wasm-ld -CommandType Application | Out-Null
    $output = Join-Path $out 'handheld-snake.wasm'
    & $clang --target=wasm32 -std=c11 -Os -Wall -Wextra -Werror -ffreestanding -nostdlib -fuse-ld=lld `
        '-Wl,--no-entry,--allow-undefined,--export=snake_init,--export=snake_poll' `
        (Join-Path $PSScriptRoot 'src/snake.c') -o $output
    if ($LASTEXITCODE -ne 0) { throw 'Snake mock build failed.' }
    Write-Host "Built $output"
    return
}
Get-Command ld.lld -CommandType Application | Out-Null
switch ($App) {
    'Snake' { $name = 'handheld-snake'; $sources = @('display.c', 'snake.c', 'snake-stm32.c') }
    'Display' { $name = 'handheld-display'; $sources = @('display.c', 'display-demo.c') }
    'Gpio' { $name = 'handheld'; $sources = @('main.c') }
}
$flags = @(
    '--target=arm-none-eabi', '-mcpu=cortex-m0plus', '-mthumb',
    '-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
    '-fno-asynchronous-unwind-tables', '-ffunction-sections', '-fdata-sections',
    '-std=c11', '-Os', '-g', '-Wall', '-Wextra', '-Werror',
    '-nostdlib', '-fuse-ld=lld', '-Xlinker', '-T', '-Xlinker',
    (Join-Path $PSScriptRoot 'stm32g070cb.ld'), '-Wl,--gc-sections',
    '-Xlinker', '-Map', '-Xlinker', (Join-Path $out "$name.map"),
    (Join-Path $PSScriptRoot 'src/startup.S'),
    (Join-Path $PSScriptRoot 'src/board.c'),
    '-o', (Join-Path $out "$name.elf")
)
$flags += @($sources | ForEach-Object { Join-Path $PSScriptRoot "src/$_" })
& $clang @flags
if ($LASTEXITCODE -ne 0) { throw 'Firmware build failed.' }
Write-Host "Built $out/$name.elf"
