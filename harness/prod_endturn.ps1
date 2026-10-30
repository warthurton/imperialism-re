# End the turn from the terrain map and play through to the next turn's map:
# End Turn -> reject a diplomacy alliance offer if one appears -> reject trade offers with Esc -> trade summary -> newspaper -> map.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Add-Type -AssemblyName System.Drawing
function Click1($fx, $fy, $wait = 2) { Ensure-Focus; $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds $wait }
function Redness($x0, $y0, $x1, $y1) {   # how red a region (1296x999 coords) is, from a fresh screenshot
  [GW]::Shot((Mirror), "$root\shots\_red.png"); $b = [Drawing.Bitmap]::FromFile("$root\shots\_red.png"); $sx = $b.Width / 1296.0; $sy = $b.Height / 999.0
  $s = 0; $n = 0; for ($y = [int]($y0*$sy); $y -lt [int]($y1*$sy); $y += 3) { for ($x = [int]($x0*$sx); $x -lt [int]($x1*$sx); $x += 3) { $c = $b.GetPixel($x,$y); $s += $c.R - ($c.G + $c.B) / 2; $n++ } }
  $b.Dispose(); return $s / $n }
Ensure-Focus; [GW]::Key(0x1B); Start-Sleep -Seconds 2        # Esc: from an industry/trade/... screen back to the map
Click1 1160 955 5                                            # End Turn
for ($i = 0; $i -lt 4 -and (Redness 170 820 300 900) -gt 40; $i++) { Click1 235 855 3 }   # diplomacy offers: Reject
& "$root\prod_reject.ps1"
Click1 62 136 4                                              # trade summary -> next
Click1 75 90 3                                               # newspaper -> map
Ensure-Focus; [GW]::Shot((Mirror), "$root\shots\endturn_done.png"); 'turn ended'
