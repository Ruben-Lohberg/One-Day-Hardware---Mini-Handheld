[CmdletBinding()]
param(
    [switch]$Once,
    [string]$Board = (Join-Path $PSScriptRoot '../mini_handheld/mini_handheld.kicad_pcb'),
    [string]$Output = (Join-Path $PSScriptRoot 'mini_handheld.step'),
    [string]$KiCadCli
)

$ErrorActionPreference = 'Stop'
$Board = (Resolve-Path -LiteralPath $Board).ProviderPath
$Output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
if ([IO.Path]::GetExtension($Output) -notin '.step', '.stp') {
    throw 'Output must end in .step or .stp.'
}
if (-not $KiCadCli) {
    $command = Get-Command kicad-cli.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($command) {
        $KiCadCli = $command.Source
    } else {
        $KiCadCli = @(
            (Join-Path $env:ProgramFiles 'KiCad/10.0/bin/kicad-cli.exe')
        ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    }
}
if (-not $KiCadCli) { throw 'kicad-cli.exe not found. Pass its path with -KiCadCli.' }
$KiCadCli = (Resolve-Path -LiteralPath $KiCadCli).ProviderPath
$outDir = [IO.Path]::GetDirectoryName($Output)
[IO.Directory]::CreateDirectory($outDir) | Out-Null

function Get-BoardHash {
    (Get-FileHash -LiteralPath $Board -Algorithm SHA256).Hash
}

function Export-Board([string]$ExpectedHash) {
    $tempStep = Join-Path $outDir ('.pcb-export-' + [guid]::NewGuid() + '.step')
    try {
        & $KiCadCli pcb export step --subst-models --no-dnp --user-origin '100x134mm' -o $tempStep $Board |
            Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $tempStep -PathType Leaf)) {
            throw "KiCad STEP export failed (exit $LASTEXITCODE)."
        }
        if ((Get-BoardHash) -ne $ExpectedHash) {
            throw 'Board changed during export. Waiting for the next stable version.'
        }
        # Publish only a completed export; retain the previous file on failure.
        if ([IO.File]::Exists($Output)) {
            [IO.File]::Replace($tempStep, $Output, [NullString]::Value)
        } else {
            [IO.File]::Move($tempStep, $Output)
        }
        Write-Host "[$(Get-Date -Format HH:mm:ss)] Exported $Output"
    } finally {
        if (Test-Path -LiteralPath $tempStep) { Remove-Item -LiteralPath $tempStep -Force }
    }
}

if ($Once) {
    Export-Board (Get-BoardHash)
    return
}

Write-Host "Watching $Board. Press Ctrl+C to stop."
$exported = $null
$previous = $null
while ($true) {
    try {
        $hash = Get-BoardHash
        # Wait for two identical reads so a save or rename can finish.
        if ($hash -eq $previous -and ($hash -ne $exported -or -not [IO.File]::Exists($Output))) {
            Export-Board $hash
            $exported = $hash
        }
        $previous = $hash
    } catch {
        Write-Warning $_.Exception.Message
        $previous = $null
        Start-Sleep -Seconds 2
    }
    Start-Sleep -Milliseconds 500
}
