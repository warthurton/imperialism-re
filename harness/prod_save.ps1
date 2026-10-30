# Save the running game into slot 0 and copy it to saves\<name>.imp. usage: prod_save.ps1 <name>   (from the terrain map)
param([Parameter(Mandatory)][string]$name)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
function Click1($fx, $fy, $wait = 2) { Ensure-Focus; $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds $wait }
Click1 1190 80 2; Click1 603 315 3; Click1 370 627 1; Click1 1150 472 3
Copy-Item 'C:\GOG Games\Imperialism\Save\slot0.imp' (Join-Path (Split-Path $root) "saves\$name.imp") -Force
"saved saves\$name.imp (add a line for it to saves\README.md)"
