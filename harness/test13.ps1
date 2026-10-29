$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Cur($label, $fx, $fy) {
  $p = Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 700
  "{0,-30} cursor 0x{1:x}" -f $label, [GW]::CursorHandle()
}
function Shot($n) { Start-Sleep -Milliseconds 1500; [GW]::Shot((Mirror), "$shots\$n.png"); "shot $n" }
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  ClickAt 936 905; Start-Sleep -Seconds 12
  ClickAt 1015 216                       # close the briefing dialog with its X
  Shot '80_after_close_dialog'
  Cur 'newspaper center' 650 500
  ClickAt 650 500
  Shot '81_after_click_newspaper'
  Cur 'hover A' 300 400
  Cur 'hover B' 900 600
  Cur 'hover C' 600 200
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
