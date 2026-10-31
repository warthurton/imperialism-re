# usage: shot.ps1 <name>   -- screenshot the game window (mirror) to shots\<name>.png
param([string]$name = 'now')
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; Ensure-Focus; Start-Sleep -Milliseconds 800
[GW]::Shot((Mirror), "$root\shots\$name.png"); "shot $name"
