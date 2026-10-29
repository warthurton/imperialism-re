# usage: prod_click.ps1 <fx> <fy> <shotname> [wait]   -- click a point given in 1296x999 mirror coords, then screenshot
param([double]$fx, [double]$fy, [string]$name, [int]$wait = 2)
$root = $PSScriptRoot
. "$root\gw.ps1"
. "$root\focus.ps1"
Ensure-Focus
$m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
[GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0))
Start-Sleep -Seconds $wait
[GW]::Shot((Mirror), "$root\shots\$name.png"); "shot $name"
