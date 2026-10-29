$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function MRect { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null; $r }
function Px($fx, $fy) {   # point given in a 1296x999 mirror -> screen coords
  $r = MRect; @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0))
}
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Shot($name) { Start-Sleep -Milliseconds 1200; $m = Mirror; if ($m -ne [IntPtr]::Zero) { [GW]::Shot($m, "$shots\$name.png"); "shot $name" } else { "shot $name : no visible mirror" } }
function Cur($label, $fx, $fy) {
  $p = Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 700
  "cursor @ $label : handle 0x{0:x}" -f [GW]::CursorHandle()
}
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  "##### CURSOR SHAPE (title screen)"
  Cur 'desk (not a hotspot)' 650 900
  Cur 'globe (hotspot?)' 230 580
  Cur 'doors' 650 400
  Cur 'globe again' 230 580

  "##### TYPING IN THE EDIT CONTROL"
  ClickAt 230 580; Start-Sleep -Seconds 4
  Shot '50_setup_before_typing'
  ClickAt 935 558                          # the Country name field
  Start-Sleep -Milliseconds 500
  [GW]::KeyDown(0x11); [GW]::Key(0x41); [GW]::KeyUp(0x11)   # Ctrl+A
  [GW]::Text('Testland')
  Shot '51_setup_after_typing'

  "##### START GAME, THEN DIALOG DRAG"
  ClickAt 936 905; Start-Sleep -Seconds 12
  Shot '52_ingame_dialog'
  $a = Px 520 215; $b = Px 760 440         # drag the dialog's title bar
  [GW]::Drag($a[0], $a[1], $b[0], $b[1])
  Shot '53_after_dialog_drag'

  "##### MOUSE WHEEL over the dialog's list"
  $w = Px 650 750; [GW]::SetCursorPos($w[0], $w[1]) | Out-Null; Start-Sleep -Milliseconds 400
  [GW]::Wheel(-360); [GW]::Wheel(-360); Shot '54_after_wheel'

  "##### F11 FULLSCREEN"
  $before = MRect
  "before: $($before.L),$($before.T) $($before.R-$before.L)x$($before.B-$before.T)"
  [GW]::Key(0x7A); Start-Sleep -Milliseconds 1500
  $f = MRect; "after F11: $($f.L),$($f.T) $($f.R-$f.L)x$($f.B-$f.T)"
  Shot '55_fullscreen'
  [GW]::Key(0x7A); Start-Sleep -Milliseconds 1500
  $f2 = MRect; "after F11 again: $($f2.L),$($f2.T) $($f2.R-$f2.L)x$($f2.B-$f2.T)"
  Shot '56_back_to_window'
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
