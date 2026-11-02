# Click the game by window messages: no focus, no mirror scaling, no cursor movement; works with the game minimized.
# usage: msgclick.ps1 "g 563 131; w 1; id; d 242 188; dclose; g 23 50"      (steps separated by ;)
#   g X Y     click the game window at game pixel X,Y (the 640x480 AmbitGameWindow; map, toolbar, screens)
#   d X Y     click inside the open dialog at X,Y measured from the dialog WINDOW's top-left (the same numbers as
#             $script:DLG in fast.ps1); the client-area offset (3,26) is subtracted here
#   dclose    close the open dialog (WM_SYSCOMMAND SC_CLOSE, as the shim does for the title-bar X)
#   w SEC     wait      id   print the screen id      dlg   print the open dialog
# Why it works (found in the spike, see docs/screens.md): the shim relays real clicks with SendMessage to the deepest child window under
# the pointer, in that child's CLIENT coordinates. Posting to the 640x480 game window with game pixels works as is; dialogs are
# AmbitMcWindow children of the frame whose window rect includes a 3 px border and a 26 px caption, so subtract (3,26).
# Pick the dialog by SIZE (Get-Dialog), not by enumeration order: a second visible AmbitMcWindow (a side panel) can come first.
param([Parameter(Mandatory = $true)][string]$Steps)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\fast.ps1"
$pid_ = (Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id
if (-not $pid_) { throw 'the game is not running' }
$frame = [GW]::Windows([uint32]$pid_) | Where-Object { $_[1] -like 'Afx:*' } | Select-Object -First 1
$fh = [IntPtr][int64]$frame[0]
function Handle-Of($line) { [IntPtr][int64](($line -split ' ')[0]) }
function Lparam([int]$x, [int]$y) { [IntPtr](($y -shl 16) -bor ($x -band 0xFFFF)) }
function Send-Click([IntPtr]$h, [int]$x, [int]$y) {      # move, press, release, with the button flag the game expects while pressed
  [GW]::SendMessage($h, 0x0200, [IntPtr]0, (Lparam $x $y)) | Out-Null; Start-Sleep -Milliseconds 80
  [GW]::SendMessage($h, 0x0201, [IntPtr]1, (Lparam $x $y)) | Out-Null; Start-Sleep -Milliseconds 80
  [GW]::SendMessage($h, 0x0202, [IntPtr]0, (Lparam $x $y)) | Out-Null; Start-Sleep -Milliseconds 350
}
function Game-Handle { Handle-Of ([GW]::Children($fh) | Where-Object { $_ -match 'AmbitGameWindow' } | Select-Object -First 1) }
function Dialog-Handle {
  $d = Get-Dialog; if (-not $d) { throw 'no dialog open' }
  Handle-Of ([GW]::Children($fh) | Where-Object { $_ -match 'AmbitMcWindow vis=True' -and $_ -match "$($d.W)x$($d.H)" } | Select-Object -First 1)
}
foreach ($raw in $Steps.Split(';')) {
  $t = $raw.Trim().Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
  if (-not $t) { continue }
  switch ($t[0]) {
    'g'      { Send-Click (Game-Handle) ([int]$t[1]) ([int]$t[2]) }
    'd'      { Send-Click (Dialog-Handle) ([int]$t[1] - 3) ([int]$t[2] - 26) }
    'dclose' { [GW]::PostMessage((Dialog-Handle), 0x0112, [IntPtr]0xF060, [IntPtr]0) | Out-Null; Start-Sleep -Milliseconds 600 }
    'w'      { Start-Sleep -Milliseconds ([int]([double]$t[1] * 1000)) }
    'id'     { "screen id " + (Get-ScreenId) }
    'dlg'    { $d = Get-Dialog; if ($d) { "dialog $($d.Kind) at ($($d.X),$($d.Y)) $($d.W)x$($d.H)" } else { 'no dialog' } }
    default  { throw "unknown step '$($t[0])'" }
  }
}
