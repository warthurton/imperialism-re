# Send a focus event to the game: brings it to the foreground, and the idle watcher restores the large size. Use before any manual interaction.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Ensure-Focus
$r = Get-GameRect; "game focused, window {0},{1} {2}x{3}" -f $r.L, $r.T, ($r.R - $r.L), ($r.B - $r.T)
