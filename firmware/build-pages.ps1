$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'build.ps1') -App SnakeMock

$web = Join-Path $PSScriptRoot 'web'
$output = Join-Path $PSScriptRoot 'build/pages'
New-Item -ItemType Directory -Path $output -Force | Out-Null

foreach ($asset in @('app.js', 'mock.js', 'style.css')) {
    Copy-Item -LiteralPath (Join-Path $web $asset) -Destination $output
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build/handheld-snake.wasm') `
    -Destination (Join-Path $output 'snake.wasm')

# The served page defaults to Renode. The static copy starts the mock.
$html = Get-Content -LiteralPath (Join-Path $web 'index.html') -Raw -Encoding utf8
if (-not $html.Contains('data-runtime="renode"')) {
    throw 'Expected the simulator page to declare its default runtime.'
}
$html.Replace('data-runtime="renode"', 'data-runtime="mock"') |
    Set-Content -LiteralPath (Join-Path $output 'index.html') -Encoding utf8NoBOM -NoNewline
Write-Host "Built static simulator in $output"
