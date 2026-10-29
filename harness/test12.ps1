$root = $PSScriptRoot
. "$root\gw.ps1"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Cur($label, $fx, $fy) {
  $p = Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 800
  "{0,-34} handle 0x{1:x}" -f $label, [GW]::CursorHandle()
}
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  ClickAt 936 905; Start-Sleep -Seconds 12
  "in-game; dialog at its original position:"
  Cur 'newspaper background'           100 500
  Cur 'dialog help link'               405 633
  Cur 'dialog help link 2'             410 700
  Cur 'dialog text area (no link)'     650 800
  Cur 'dialog close X'                1015 216
  Cur 'dialog title bar'               500 215
  Cur 'dialog portrait'                365 380
  Cur 'newspaper question mark (?)'   1210 90
  Cur 'newspaper 7 (top-left)'          75 90
  Cur 'newspaper background again'     100 500
  "(for reference, the plain arrow here is 0x10003)"
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
