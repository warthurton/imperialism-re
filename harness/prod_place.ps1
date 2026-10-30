# usage: prod_place.ps1 [large|small]
param([string]$mode = 'small')
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
if ($mode -eq 'large') { Dock-Large } else { Dock-Small }
$r = Get-GameRect; "window {0},{1} {2}x{3}" -f $r.L, $r.T, ($r.R - $r.L), ($r.B - $r.T)
