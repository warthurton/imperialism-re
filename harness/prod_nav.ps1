# Launch the game, start a new game and stop on the in-game map. Leaves the game RUNNING (kill it with prod_kill.ps1).
$root = $PSScriptRoot
. "$root\gw.ps1"
. "$root\focus.ps1"
function MRect { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null; $r }
function Px($fx, $fy) { $r = MRect; @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { Ensure-Focus; $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Shot($name) { Start-Sleep -Milliseconds 1000; [GW]::Shot((Mirror), "$root\shots\$name.png"); "shot $name" }

$game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
"pid $($game.Id)"
$t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
Start-Sleep -Seconds 4
ClickAt 230 580; Start-Sleep -Seconds 4        # globe -> setup
ClickAt 936 905; Start-Sleep -Seconds 12       # Start Game
Shot 'p1_after_start'
ClickAt 1015 216; Start-Sleep -Seconds 3       # briefing dialog X
Shot 'p2_after_briefing_close'
