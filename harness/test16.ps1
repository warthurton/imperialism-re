$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Hover($label, $fx, $fy) {
  $p = Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 800
  "{0,-30} cursor 0x{1:x}" -f $label, [GW]::CursorHandle()
}
$script:prev = $null
function Shot($n, $wait = 2200) {
  Start-Sleep -Milliseconds $wait; $p = "$shots\$n.png"; [GW]::Shot((Mirror), $p)
  $d = 'n/a'; if ($script:prev) { $d = [GW]::DiffImages($script:prev, $p) }
  "{0,-26} change vs previous: {1}" -f $n, $d; $script:prev = $p
}
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  ClickAt 936 905; Start-Sleep -Seconds 12
  ClickAt 1015 216; Start-Sleep -Seconds 2        # close newspaper dialog
  ClickAt 75 90;    Start-Sleep -Seconds 4        # newspaper exit arrow -> map
  ClickAt 897 182;  Start-Sleep -Seconds 2        # close the terrain briefing dialog
  Shot '110_map_baseline'
  "--- cursors on the map screen"
  Hover 'map terrain' 600 500
  Hover 'map terrain 2' 300 300
  Hover 'sidebar button (magnifier)' 1075 80
  Hover 'sidebar End Turn' 1170 955
  Hover 'minimap' 1160 195
  "--- mouse wheel over the map"
  $p = Px 600 500; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 500
  [GW]::Wheel(-360); [GW]::Wheel(-360); [GW]::Wheel(-360)
  Shot '111_after_wheel_down'
  [GW]::Wheel(360); [GW]::Wheel(360); [GW]::Wheel(360)
  Shot '112_after_wheel_up'
  "--- click on a sidebar button (magnifier)"
  ClickAt 1075 80
  Shot '113_after_magnifier_click'
  "--- click on the minimap"
  ClickAt 1200 215
  Shot '114_after_minimap_click'
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
