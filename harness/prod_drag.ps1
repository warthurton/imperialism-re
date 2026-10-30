# usage: prod_drag.ps1 x0 y0 x1 y1 shotname   (1296x999 coords)
param([double]$x0,[double]$y0,[double]$x1,[double]$y1,[string]$name)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Ensure-Focus
$m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
$sx = ($r.R - $r.L) / 1296.0; $sy = ($r.B - $r.T) / 999.0
[GW]::Drag([int]($r.L + $x0*$sx), [int]($r.T + $y0*$sy), [int]($r.L + $x1*$sx), [int]($r.T + $y1*$sy))
Start-Sleep -Seconds 1
[GW]::Shot((Mirror), "$root\shots\$name.png"); "shot $name"
