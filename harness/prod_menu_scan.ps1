# Hover over a grid on the TITLE screen and record the hot text shown on the paper at the bottom.
# usage: prod_menu_scan.ps1 [-Step 60]   Saves a crop per distinct text to shots\menu_<n>.png and prints "n x y" (mirror coords) of its first hit.
# The text is tan on a light paper, so a crop is compared with a baseline taken with the mouse over an empty spot.
param([int]$Step = 60)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
Ensure-Focus
$rx0 = 380; $ry0 = 905; $rx1 = 900; $ry1 = 960          # the paper strip, mirror units
function Crop-Sig($m, [string]$save) {
  [GW]::Shot($m, "$root\shots\_menu.png")
  $b = [Drawing.Bitmap]::FromFile("$root\shots\_menu.png"); $bx = $b.Width / 1296.0; $by = $b.Height / 999.0
  $x0 = [int]($rx0 * $bx); $x1 = [int]($rx1 * $bx); $y0 = [int]($ry0 * $by); $y1 = [int]($ry1 * $by)
  $px = @{}
  for ($y = $y0; $y -lt $y1; $y += 2) { for ($x = $x0; $x -lt $x1; $x += 2) { $c = $b.GetPixel($x, $y); $px["$x,$y"] = $c.R + $c.G + $c.B } }
  if ($save) { $crop = $b.Clone((New-Object Drawing.Rectangle($x0, $y0, ($x1 - $x0), ($y1 - $y0))), $b.PixelFormat); $crop.Save($save); $crop.Dispose() }
  $b.Dispose(); return $px
}
$m = Mirror
$p = Mirror-Px 650 400; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 500
$base = Crop-Sig $m ''
$seen = @{}; $n = 0
for ($fy = 60; $fy -lt 990; $fy += $Step) {
  for ($fx = 20; $fx -lt 1290; $fx += $Step) {
    $p = Mirror-Px $fx $fy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null; Start-Sleep -Milliseconds 250
    $cur = Crop-Sig $m ''
    $sig = ''; foreach ($k in ($cur.Keys | Sort-Object)) { if ([math]::Abs($cur[$k] - $base[$k]) -gt 60) { $sig += "$k;" } }
    if ($sig.Length -gt 60 -and -not $seen.ContainsKey($sig)) { $seen[$sig] = $n; Crop-Sig $m "$root\shots\menu_$n.png" | Out-Null; "$n $fx $fy"; $n++ }
  }
}
"distinct hot texts: $n"
