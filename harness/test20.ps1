param([string]$Label = 'patched', [int]$Seconds = 14)
$root = $PSScriptRoot
. "$root\gw.ps1"
. "$root\audio.ps1"
$dir = 'C:\GOG Games\Imperialism'
$g = Start-Process "$dir\Imperialism.exe" -WorkingDirectory $dir -PassThru
try {
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 2
  $peaks = @()
  for ($i = 0; $i -lt $Seconds * 4; $i++) { $peaks += [AudioPeek]::Peak([uint32]$g.Id); Start-Sleep -Milliseconds 250 }
  $valid = $peaks | Where-Object { $_ -ge 0 }
  $max = if ($valid) { ($valid | Measure-Object -Maximum).Maximum } else { -1 }
  $loud = ($valid | Where-Object { $_ -gt 0.001 }).Count
  "[$Label] samples=$($peaks.Count) sessionSeen=$($valid.Count) maxPeak={0:N4} samplesWithSound={1}" -f $max, $loud
  Select-String -Path "$dir\imperialism_gdi_log.txt" -Pattern '^winmm patch:' | Select-Object -Last 1 | ForEach-Object { '   ' + $_.Line }
}
finally {
  Stop-Process -Id $g.Id -Force -ErrorAction SilentlyContinue
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
}
