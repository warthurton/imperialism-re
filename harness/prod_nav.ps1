# Launch the game, start a new game and stop on the in-game map. Leaves the game RUNNING (kill it with prod_end.ps1).
param([ValidateSet('test','sound','normal')][string]$Volumes = 'test')
$root = $PSScriptRoot
& "$root\prod_vol.ps1" -Mode $Volumes
# Windows' compatibility assistant adds 'IgnoreFreeLibrary' to the exe after a crash, which makes it load the SYSTEM winmm (no music).
$layerKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'; $exePath = 'C:\GOG Games\Imperialism\Imperialism.exe'
if (((Get-ItemProperty $layerKey -ErrorAction SilentlyContinue).$exePath) -match 'IgnoreFreeLibrary') { Set-ItemProperty -Path $layerKey -Name $exePath -Value 'HIGHDPIAWARE'; Write-Host 'removed IgnoreFreeLibrary compat layer (it disables the music player)' }
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
ClickAt 75 90; Start-Sleep -Seconds 3         # leave the newspaper -> map
ClickAt 893 184; Start-Sleep -Seconds 2       # close the first map briefing (new games start with briefings On)
& "$root\start_idle_dock.ps1"
& "$root\prod_prefs.ps1"
& "$root\prod_music.ps1"
