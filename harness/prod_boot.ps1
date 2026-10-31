# Launch the game and load a saved-game fixture straight from the title screen (no new game, no preference clicking).
# usage: prod_boot.ps1 [-Fixture oil_t0] [-Volumes test|sound|normal] [-Restart]
#   Registry settings (volumes, minister warnings/briefings off) are written first; the game reads them at launch and a loaded
#   save keeps them (a NEW game resets briefings to On, which is why prod_nav.ps1 has to click them off).
#   Title screen (mirror units): Ship in the Bottle = Load Saved Game (240,340); on that screen slot 0 = (370,627), Load Game (1150,472).
param([string]$Fixture = 'oil_t0', [ValidateSet('test','sound','normal')][string]$Volumes = 'test', [switch]$Restart)
$root = $PSScriptRoot
$src = Join-Path (Split-Path $root) "saves\$Fixture.imp"
if (-not (Test-Path $src)) { throw "no such fixture: $src" }
if ($Restart) { Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2 }
if (Get-Process Imperialism -ErrorAction SilentlyContinue) { throw 'the game is already running: use -Restart (loading from the title screen needs a fresh launch)' }
& "$root\prod_vol.ps1" -Mode $Volumes
# Windows' compatibility assistant adds 'IgnoreFreeLibrary' to the exe after a crash, which makes it load the SYSTEM winmm (no music).
$layerKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'; $exePath = 'C:\GOG Games\Imperialism\Imperialism.exe'
if (((Get-ItemProperty $layerKey -ErrorAction SilentlyContinue).$exePath) -match 'IgnoreFreeLibrary') { Set-ItemProperty -Path $layerKey -Name $exePath -Value 'HIGHDPIAWARE'; Write-Host 'removed IgnoreFreeLibrary compat layer' }
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
Copy-Item $src 'C:\GOG Games\Imperialism\Save\slot0.imp' -Force
# The shim can log every string the game draws (imperialism_text.log); switch that on so tests can READ screens (tools/readtext.py, prod_do "mark" / "txt").
$ini = 'C:\GOG Games\Imperialism\imperialism_shim.ini'
if (-not (Test-Path $ini) -or -not (Select-String -Path $ini -Pattern '^\[text_log\]' -Quiet)) { Add-Content -Path $ini -Value "`r`n[text_log]`r`nenabled=1" }
$sw = [Diagnostics.Stopwatch]::StartNew()
$game = Start-Process $exePath -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
$t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 60) { Start-Sleep -Milliseconds 500; $t++ }
Start-Sleep -Seconds 3; Wait-Stable -Max 12
Click-Wait 240 340                    # Ship in the Bottle -> Load Saved Game screen
Click-Wait 370 627                    # slot 0 (the fixture was just copied into it)
Click-Wait 1150 472 15                # Load Game
$py = (Get-Command python).Source
for ($i = 0; $i -lt 40; $i++) { $id = & $py -I (Join-Path (Split-Path $root) 'tools\readview.py') id 2>$null; if ($id -eq '2013') { break }; Start-Sleep -Milliseconds 500 }
if ($id -ne '2013') { throw "the map did not come up (screen id '$id')" }
"booted '$Fixture' in $([int]$sw.Elapsed.TotalSeconds) s (pid $($game.Id)); screen id $id = terrain map"
& "$root\prod_music.ps1"
