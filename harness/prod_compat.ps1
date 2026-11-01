# Test both standalone Compat music builds in the game; restore installed files/settings on every exit.
param([string]$Name = 'compat_live', [string]$CompatRoot = (Join-Path (Split-Path $PSScriptRoot) 'compat'))
$ErrorActionPreference = 'Stop'
if ($Name -notmatch '^compat_[A-Za-z0-9_-]+$') { throw 'Name must start with compat_ and use simple filename characters' }
$repository = Split-Path $PSScriptRoot
$gameDirectory = 'C:\GOG Games\Imperialism'
$backup = Join-Path $repository "results\trace_$Name"
if (-not (Test-Path -LiteralPath (Join-Path $CompatRoot 'build.py'))) { throw 'Initialize Compat with git submodule update --init compat, or pass -CompatRoot for another checkout' }
if (Test-Path -LiteralPath $backup) { throw 'Use a fresh Name; backup already exists' }
if (Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited }) { throw 'Close the running game before this test' }
$display = Join-Path $CompatRoot 'build\msvfw32.dll'
if (-not (Test-Path -LiteralPath $display)) { throw 'Build the standalone display DLL first' }
foreach ($variant in @('gog-codecs', 'current-codecs')) {
    if (-not (Test-Path -LiteralPath (Join-Path $CompatRoot "build\music\$variant\winmm.dll"))) { throw "Missing music build: $variant" }
}
$files = @('msvfw32.dll', 'winmm.dll', 'imperialism_shim.ini', 'winmm.ini')
$original = @{}
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($file in $files) {
    $path = Join-Path $gameDirectory $file
    $original[$file] = Test-Path -LiteralPath $path
    if ($original[$file]) { Copy-Item -LiteralPath $path -Destination (Join-Path $backup $file) }
}
$reports = @()
try {
    Push-Location $repository
    foreach ($variant in @('gog-codecs', 'current-codecs')) {
        Copy-Item -LiteralPath $display -Destination (Join-Path $gameDirectory 'msvfw32.dll') -Force
        Copy-Item -LiteralPath (Join-Path $CompatRoot "build\music\$variant\winmm.dll") -Destination (Join-Path $gameDirectory 'winmm.dll') -Force
        Copy-Item -LiteralPath (Join-Path $CompatRoot 'imperialism_shim.ini') -Destination (Join-Path $gameDirectory 'imperialism_shim.ini') -Force
        Copy-Item -LiteralPath (Join-Path $CompatRoot 'music\winmm.ini') -Destination (Join-Path $gameDirectory 'winmm.ini') -Force
        $label = "snapshot_${Name}_$($variant.Replace('-', '_'))"
        & "$PSScriptRoot\prod_snapshot.ps1" -Name $label
        if ($LASTEXITCODE -ne 0) { throw "Snapshot test failed: $variant" }
        $validation = Get-Content -Raw (Join-Path $repository "results\${label}_validation.json") | ConvertFrom-Json
        $reports += [PSCustomObject]@{ Variant = $variant; Checks = $validation.checks.Count; Status = $validation.status; TurnBefore = $validation.turn_before; TurnAfter = $validation.turn_after }
    }
}
finally {
    & "$PSScriptRoot\prod_end.ps1"
    foreach ($file in $files) {
        $path = Join-Path $gameDirectory $file
        if ($original[$file]) {
            Copy-Item -LiteralPath (Join-Path $backup $file) -Destination $path -Force
            if ((Get-FileHash -LiteralPath $path).Hash -ne (Get-FileHash -LiteralPath (Join-Path $backup $file)).Hash) { throw "Restore hash mismatch: $file" }
        } elseif (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path
        }
    }
    Pop-Location
    'Original DLLs and INI files restored; game stopped.'
}
$report = [PSCustomObject]@{ Status = 'ok'; Tests = $reports; Restored = $true }
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backup 'acceptance.json')
$report | ConvertTo-Json -Depth 5
