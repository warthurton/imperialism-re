# Trace one End Turn: attach tools/tracer's trace_calls.exe to the running game, end the turn, detach, write results\<name>_funcs.tsv / _edges.tsv.
# usage: trace_endturn.ps1 -Name trace4 [-Cap 60] [-StopAfterSeconds N]
#   the game must already be running from a fixture (prod_boot.ps1 -Fixture oil_plant_built -Restart).
#   -StopAfterSeconds N detaches N seconds after the End Turn starts (a stress test of the detach); default: after the turn has finished.
# Build the tracer first: i686-w64-mingw32-clang -O2 -static -o results\trace_calls.exe tools\tracer\trace_calls.c ; list: python -I tools\tracer\make_funclist.py
param([Parameter(Mandatory = $true)][string]$Name, [int]$Cap = 60, [int]$StopAfterSeconds = 0)
$root = Split-Path -Parent $PSScriptRoot
$game = Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited } | Select-Object -First 1
if (-not $game) { throw 'the game is not running' }
$prefix = Join-Path $root "results\$Name"
$p = Start-Process -FilePath (Join-Path $root 'results\trace_calls.exe') -ArgumentList "$($game.Id) `"$(Join-Path $root 'results\funclist.txt')`" `"$prefix`" --seconds 600 --cap $Cap" `
    -RedirectStandardOutput "$prefix.log" -RedirectStandardError "$prefix.err" -PassThru -NoNewWindow
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt 30) { if ((Get-Content "$prefix.log" -ErrorAction SilentlyContinue) -match 'breakpoints planted') { break }; Start-Sleep -Milliseconds 300 }
if ($StopAfterSeconds -gt 0) {
    $job = Start-Job -ScriptBlock { param($r) & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $r 'harness\prod_endturn.ps1') } -ArgumentList $root
    Start-Sleep -Seconds $StopAfterSeconds
    Set-Content -Path "$prefix.stop" -Value 'stop'
    Wait-Job $job -Timeout 120 | Out-Null
    Receive-Job $job | Select-Object -Last 2
} else {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'harness\prod_endturn.ps1') | Select-Object -Last 2
    Set-Content -Path "$prefix.stop" -Value 'stop'
}
$p.WaitForExit(30000) | Out-Null
Get-Content "$prefix.log" | Select-Object -Last 2
$g = Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited } | Select-Object -First 1
if ($g) { "game still running, responding: $($g.Responding)" } else { 'GAME IS GONE' }
