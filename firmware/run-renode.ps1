param(
    [string]$Renode,
    [switch]$SmokeTest
)

$ErrorActionPreference = 'Stop'
if (!$Renode) {
    $portable = Join-Path $PSScriptRoot 'build/renode/Renode.exe'
    if (Test-Path -LiteralPath $portable) {
        $Renode = $portable
    } else {
        $Renode = (Get-Command renode -CommandType Application -ErrorAction SilentlyContinue).Source
    }
}
if (!$Renode) { throw 'Install Renode or pass -Renode <path-to-Renode.exe>.' }

& (Join-Path $PSScriptRoot 'build.ps1')
$options = @('--console', '--disable-gui', '--plain',
             (Join-Path $PSScriptRoot 'renode/handheld.resc'))
if (!$SmokeTest) {
    & $Renode @options
    if ($LASTEXITCODE -ne 0) { throw "Renode exited with code $LASTEXITCODE." }
    return
}

$gpio = 'sysbus.gpioPortA'
$sample = @('emulation RunFor "0.002"', "$gpio.led1 State", "$gpio.led2 State")
$commands = @('include $ORIGIN/../renode/handheld.resc') + $sample
$expected = @('False', 'False')
foreach ($button in @('up', 'down', 'left', 'right')) {
    $commands += "$gpio.$button Press"
    $commands += $sample
    if ($button -in @('up', 'down')) { $expected += @('True', 'False') }
    else { $expected += @('False', 'True') }
    $commands += "$gpio.$button Release"
    $commands += $sample
    $expected += @('False', 'False')
}
$commands += @("$gpio.up Press", "$gpio.left Press")
$commands += $sample
$expected += @('True', 'True')
$smoke = Join-Path $PSScriptRoot 'build/gpio-smoke.resc'
$commands | Set-Content -LiteralPath $smoke -Encoding ascii
$log = & $Renode --console --disable-gui --plain $smoke -e quit
$actual = @($log | ForEach-Object { $_.Trim() } | Where-Object { $_ -cmatch '^(True|False)$' })
if ($LASTEXITCODE -ne 0 -or ($actual -join ',') -cne ($expected -join ',') -or
    ($log -match 'There was an error executing command|No such command or device')) {
    $log | Write-Host
    throw "GPIO smoke test failed. Expected $($expected -join ','); got $($actual -join ',')."
}
Write-Host 'GPIO smoke test passed: idle, all four button presses and releases, and two simultaneous presses.'
