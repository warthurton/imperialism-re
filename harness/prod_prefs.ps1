# After a new game starts: turn Minister Briefings off through the real Preferences screen (a new game resets them to On).
# Game Controls (top bar icon) -> Set Preferences -> [close the Preferences Briefing popup if it is showing] -> toggle
# Briefings only if its picture is still bright (On; Off dims it) -> verify -> back to the map. Works from the map screen.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Add-Type -AssemblyName System.Drawing
function Click1($fx, $fy, $wait = 2) { Ensure-Focus; $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds $wait }
function Bright($x0, $y0, $x1, $y1) {   # mean brightness of a region given in 1296x999 coords, from a fresh screenshot
  Ensure-Focus; [GW]::Shot((Mirror), "$root\shots\_prefs.png")
  $b = [Drawing.Bitmap]::FromFile("$root\shots\_prefs.png"); $sx = $b.Width / 1296.0; $sy = $b.Height / 999.0
  $sum = 0; $n = 0
  for ($y = [int]($y0 * $sy); $y -lt [int]($y1 * $sy); $y += 4) { for ($x = [int]($x0 * $sx); $x -lt [int]($x1 * $sx); $x += 4) { $c = $b.GetPixel($x, $y); $sum += ($c.R + $c.G + $c.B) / 3; $n++ } }
  $b.Dispose(); return $sum / $n
}
Click1 1190 80 2
Click1 367 623 3
# the briefing popup's parchment body covers (300..880, 560..700); without it that part of the screen is dark wood (~90)
for ($i = 0; $i -lt 2 -and (Bright 300 560 880 700) -gt 170; $i++) { Click1 897 182 2; Click1 1015 216 2 }   # close it (X is at one of two places)
$on = (Bright 405 625 590 795)                                              # the Briefings picture
if ($on -gt 140) { Click1 497 770 2; $after = (Bright 405 625 590 795); "briefings picture brightness $([int]$on) -> $([int]$after) (On ~165, Off ~117)"; if ($after -gt 140) { Write-Warning 'briefings still On' } } else { "briefings already Off ($([int]$on))" }
Click1 50 135 3
[GW]::Shot((Mirror), "$root\shots\prefs_done.png")
