param(
    [string]$Renode,
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [switch]$DisplayDemo,
    [switch]$SmokeTest,
    [switch]$Mock
)

$ErrorActionPreference = 'Stop'
if ($Mock) {
    if ($DisplayDemo -or $SmokeTest) { throw 'The timing mock runs Snake. Use -Mock by itself or with -Port.' }
    if (!$PSBoundParameters.ContainsKey('Port')) { $Port = 8766 }
    & (Join-Path $PSScriptRoot 'build.ps1') -App SnakeMock
    & python (Join-Path $PSScriptRoot 'web/server.py') --mock --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Snake timing mock exited with code $LASTEXITCODE." }
    return
}
if (!$Renode) {
    $portable = Join-Path $PSScriptRoot 'build/renode/Renode.exe'
    if (Test-Path -LiteralPath $portable) { $Renode = $portable }
    else { $Renode = (Get-Command renode -CommandType Application -ErrorAction SilentlyContinue).Source }
}
if (!$Renode) { throw 'Install Renode or pass -Renode <path-to-Renode.exe>.' }
$app = if ($DisplayDemo) { 'Display' } else { 'Snake' }
& (Join-Path $PSScriptRoot 'build.ps1') -App $app
$options = @((Join-Path $PSScriptRoot 'web/server.py'), '--renode', $Renode, '--port', $Port)
if ($DisplayDemo) { $options += '--display-demo' }
if ($SmokeTest) { $options += '--smoke-test' }
& python @options
if ($LASTEXITCODE -ne 0) { throw "Display simulator exited with code $LASTEXITCODE." }
