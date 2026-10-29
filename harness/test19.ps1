$root = $PSScriptRoot
. "$root\gw.ps1"
$dir = 'C:\GOG Games\Imperialism'
$log = "$dir\imperialism_gdi_log.txt"
$ini = "$dir\imperialism_shim.ini"
$dll = "$dir\winmm.dll"; $dllOff = "$dir\winmm.dll.off"

function Launch-And-Report($label) {
  $g = Start-Process "$dir\Imperialism.exe" -WorkingDirectory $dir -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 6
  "=== $label"
  Select-String -Path $log -Pattern 'winmm patch|shim loaded' | Select-Object -First 3 | ForEach-Object { '   ' + $_.Line.Trim() }
  "   game responding: " + (-not $g.HasExited)
  Stop-Process -Id $g.Id -Force -ErrorAction SilentlyContinue
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 2
}

try {
  Launch-And-Report 'A) normal: GOG winmm.dll present, patch enabled'

  Move-Item $dll $dllOff -Force
  Launch-And-Report 'B) GOG winmm.dll removed from the game folder'
  Move-Item $dllOff $dll -Force

  Set-Content -Path $ini -Value "[winmm_patch]`r`nenabled=0`r`n"
  Launch-And-Report 'C) INI says enabled=0'
  Move-Item $ini "$ini.bak" -Force
}
finally {
  if (Test-Path $dllOff) { Move-Item $dllOff $dll -Force }
  if (Test-Path $ini) { Move-Item $ini "$ini.bak" -Force }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  "restored: winmm.dll present=" + (Test-Path $dll) + ", ini present=" + (Test-Path $ini)
}
