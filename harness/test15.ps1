$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Hover($label, $fx, $fy) {
  $p = Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 900
  "{0,-34} cursor 0x{1:x}" -f $label, [GW]::CursorHandle()
}
function Shot($n, $wait = 2500) { Start-Sleep -Milliseconds $wait; [GW]::Shot((Mirror), "$shots\$n.png"); "shot $n" }
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  ClickAt 936 905; Start-Sleep -Seconds 12
  ClickAt 1015 216; Start-Sleep -Seconds 2        # close the dialog
  Hover 'top-left arrow (before click)' 75 90
  Shot '100_hover_arrow' 800
  ClickAt 75 90
  Shot '101_after_arrow_click'
  Hover 'after arrow: spot 1' 650 500
  Hover 'after arrow: spot 2' 300 300
  Hover 'after arrow: spot 3' 1000 700
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
