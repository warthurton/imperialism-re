# Trace the city task producer/consumer entries during one End Turn; caller owns game cleanup.
param([Parameter(Mandatory)][ValidatePattern('^trace_[A-Za-z0-9_-]+$')][string]$Name)
$ErrorActionPreference = 'Stop'
$repository = Split-Path $PSScriptRoot
$prefix = Join-Path $repository "results\$Name"
$executable = Join-Path $repository 'results\trace_calls.exe'
if (-not (Test-Path $executable)) { throw 'Build results/trace_calls.exe first (docs/tracer.md)' }
if (Test-Path "$prefix.log") { throw "trace output exists: $prefix.log" }
$games = @(Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited })
if ($games.Count -ne 1) { throw 'expected one live game to trace' }
$list = Join-Path $repository 'tools\tracer\city_planning.txt'
$arguments = "$($games[0].Id) `"$list`" `"$prefix`" --seconds 120 --cap 60"
$tracer = Start-Process -FilePath $executable -ArgumentList $arguments -WindowStyle Hidden `
    -RedirectStandardOutput "$prefix.log" -RedirectStandardError "$prefix.err" -PassThru
# Retain the process handle before it exits so Windows PowerShell can retrieve ExitCode.
$null = $tracer.Handle
try {
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $ready = $false
    while ($watch.Elapsed.TotalSeconds -lt 30) {
        if ((Get-Content "$prefix.log" -ErrorAction SilentlyContinue) -match 'breakpoints planted') { $ready = $true; break }
        if ($tracer.HasExited) { throw 'tracer exited before attaching' }
        Start-Sleep -Milliseconds 200
    }
    if (-not $ready) { throw 'tracer attachment timed out' }
    & "$PSScriptRoot\prod_endturn.ps1" -Log
}
finally {
    Set-Content -LiteralPath "$prefix.stop" -Value 'stop'
    if (-not $tracer.WaitForExit(30000)) { throw 'tracer did not detach; caller must stop the game' }
}
if ($tracer.ExitCode -ne 0) { throw "tracer failed ($($tracer.ExitCode)); see $prefix.err" }
Get-Content "$prefix.log" | Select-Object -Last 2
Get-Content -LiteralPath "${prefix}_funcs.tsv"
