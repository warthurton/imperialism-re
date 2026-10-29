$root = $PSScriptRoot
. "$root\gw.ps1"
Add-Type -AssemblyName System.Windows.Forms
$shots = "$root\shots"
$m = Mirror
$r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
[GW]::SetForegroundWindow($m) | Out-Null
Start-Sleep -Milliseconds 500
# click in the middle of the picture (the doors)
[GW]::Click($r.L + 700, $r.T + 500)
Start-Sleep -Seconds 3
[GW]::Shot($m, "$shots\12_after_click_center.png"); 'shot 12'
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Seconds 3
[GW]::Shot($m, "$shots\13_after_enter.png"); 'shot 13'
Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
