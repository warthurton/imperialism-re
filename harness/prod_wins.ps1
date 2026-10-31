# List the game's windows and every child window (class, visibility, rect), so what is on screen can be read without a screenshot.
# usage: prod_wins.ps1 [-Visible]    (-Visible hides invisible windows)
param([switch]$Visible)
$root = $PSScriptRoot
. "$root\gw.ps1"
$pid_ = (Get-Process Imperialism | Where-Object { -not $_.HasExited } | Select-Object -First 1).Id
foreach ($w in [GW]::Windows([uint32]$pid_)) {
  if ($Visible -and $w[3] -ne 'vis') { continue }
  "TOP $($w[0]) $($w[1]) '$($w[2])' $($w[3]) $($w[6])"
  foreach ($c in [GW]::Children([IntPtr][int64]$w[0])) { if (-not $Visible -or $c -match 'vis=True') { "   $c" } }
}
