$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"; New-Item -ItemType Directory -Force -Path $shots | Out-Null

function Step($name) {
  Start-Sleep -Milliseconds 1500
  "=== $name"
  Show-GameWindows | Where-Object { $_ -match 'ImperialismMirror|Afx:400000' -and $_ -match '\| vis \|' -or $_ -match 'iconic' }
  $m = Mirror
  if ($m -ne [IntPtr]::Zero) { [GW]::Shot($m, "$shots\$name.png"); "shot: $name.png" } else { "no visible mirror" }
}

$p = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
"launched pid $($p.Id)"
$t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
Start-Sleep -Seconds 4
Step '01_start'

$m = Mirror
# resize smaller then larger via SetWindowPos (SWP_NOZORDER|NOACTIVATE = 0x14)
[GW]::SetWindowPos($m, [IntPtr]::Zero, 200, 100, 800, 640, 0x14) | Out-Null
Step '02_resized_800x640'
[GW]::SetWindowPos($m, [IntPtr]::Zero, 100, 50, 1400, 1000, 0x14) | Out-Null
Step '03_resized_1400x1000'

[GW]::SendMessage($m, 0x112, [IntPtr]0xF030, [IntPtr]0) | Out-Null   # SC_MAXIMIZE
Step '04_maximized'
[GW]::SendMessage($m, 0x112, [IntPtr]0xF120, [IntPtr]0) | Out-Null   # SC_RESTORE
Step '05_restored_from_max'

[GW]::SendMessage($m, 0x112, [IntPtr]0xF020, [IntPtr]0) | Out-Null   # SC_MINIMIZE
Step '06_minimized'
# restore the frame the way a taskbar click would
$frame = $null
foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -like 'Afx:400000*' -and $w[2] -eq 'Imperialism') { $frame = [IntPtr][int64]$w[0] } }
"frame hwnd: $frame"
[GW]::SendMessage($frame, 0x112, [IntPtr]0xF120, [IntPtr]0) | Out-Null   # SC_RESTORE on the frame
Step '07_restored_from_min'
"--- all windows after restore:"
Show-GameWindows

$m = Mirror
[GW]::SendMessage($m, 0x112, [IntPtr]0xF030, [IntPtr]0) | Out-Null
Step '08_maximize_again'
[GW]::SendMessage($m, 0x112, [IntPtr]0xF120, [IntPtr]0) | Out-Null
Step '09_restore_again'
"done; game left running pid $($p.Id)"
