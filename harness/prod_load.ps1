# Load a named test save from saves\<name>.imp into the running game (copies it to Save\slot0.imp first).
# usage: prod_load.ps1 start_turn0     Path: Game Controls -> Load Game -> slot 0 -> Load Game -> OK.
param([string]$name = 'start_turn0')
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
$src = Join-Path (Split-Path $root) "saves\$name.imp"
if (-not (Test-Path $src)) { throw "no such fixture: $src" }
Copy-Item $src 'C:\GOG Games\Imperialism\Save\slot0.imp' -Force
function Click1($fx, $fy, $wait = 2) { Ensure-Focus; $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds $wait }
Click1 1190 80 2          # Game Controls (from the terrain map)
Click1 367 547 3          # Load Game
Click1 370 627 2          # slot 0
Click1 1150 472 3         # Load Game button
Click1 938 793 8          # OK to "step down from the current game?"
"loaded $name"
