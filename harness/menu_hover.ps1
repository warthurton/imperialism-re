# Hover named spots on the TITLE screen and save the hot-text strip (the paper at the bottom) for each.
# usage: menu_hover.ps1 "bottle:240,340 globe:170,580 ..."   -> shots\mh_<name>.png (crop of the strip), mirror units
param([Parameter(Mandatory = $true)][string]$Spots)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
Ensure-Focus; $m = Mirror
foreach ($s in $Spots.Split(' ', [StringSplitOptions]::RemoveEmptyEntries)) {
  $name, $xy = $s.Split(':'); $x, $y = $xy.Split(',')
  $p = Mirror-Px ([double]$x) ([double]$y); [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 700
  [GW]::Shot($m, "$root\shots\_mh.png")
  $b = [Drawing.Bitmap]::FromFile("$root\shots\_mh.png"); $bx = $b.Width / 1296.0; $by = $b.Height / 999.0
  $r = New-Object Drawing.Rectangle([int](380 * $bx), [int](905 * $by), [int](520 * $bx), [int](55 * $by))
  $c = $b.Clone($r, $b.PixelFormat); $c.Save("$root\shots\mh_$name.png"); $c.Dispose(); $b.Dispose(); "saved mh_$name"
}
