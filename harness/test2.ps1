$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
$m = Mirror
if ($m -eq [IntPtr]::Zero) { 'no mirror'; return }
[GW]::SetWindowPos($m, [IntPtr]::Zero, 100, 50, 1400, 1000, 0x14) | Out-Null
[GW]::SetForegroundWindow($m) | Out-Null
Start-Sleep -Seconds 1
$r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
"mirror rect: $($r.L),$($r.T) $($r.R-$r.L)x$($r.B-$r.T)"
# hover the globe, then click it
$gx = $r.L + 230; $gy = $r.T + 580
[GW]::SetCursorPos($gx, $gy) | Out-Null
Start-Sleep -Milliseconds 800
[GW]::Shot($m, "$shots\10_hover_globe.png"); 'shot 10_hover_globe'
[GW]::Click($gx, $gy)
Start-Sleep -Seconds 3
[GW]::Shot($m, "$shots\11_after_click_globe.png"); 'shot 11_after_click_globe'
Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
