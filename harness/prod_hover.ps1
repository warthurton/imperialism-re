# Hover over a grid of points on the current screen and record the hot text (top-right of the header) at each one.
# usage: prod_hover.ps1 [-Step 70]   Saves one crop per distinct hot text to shots\hover_<n>.png and prints "n x y" for the first point of each.
param([int]$Step = 70)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Add-Type -AssemblyName System.Drawing
Ensure-Focus
$m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
$sx = ($r.R - $r.L) / 1296.0; $sy = ($r.B - $r.T) / 999.0
$seen = @{}; $n = 0
for ($fy = 120; $fy -lt 960; $fy += $Step) {
  for ($fx = 130; $fx -lt 1190; $fx += $Step) {
    [GW]::SetCursorPos([int]($r.L + $fx * $sx), [int]($r.T + $fy * $sy)) | Out-Null
    Start-Sleep -Milliseconds 220
    [GW]::Shot($m, "$root\shots\_hover.png")
    $b = [Drawing.Bitmap]::FromFile("$root\shots\_hover.png"); $bx = $b.Width / 1296.0; $by = $b.Height / 999.0
    $x0 = [int](1000 * $bx); $x1 = [int](1200 * $bx); $y0 = [int](52 * $by); $y1 = [int](92 * $by)
    $sig = ''
    for ($y = $y0; $y -lt $y1; $y += 3) { for ($x = $x0; $x -lt $x1; $x += 3) { $c = $b.GetPixel($x, $y); if ($c.R -gt 200 -and $c.G -gt 190) { $sig += "$x,$y;" } } }
    if ($sig.Length -gt 40 -and -not $seen.ContainsKey($sig)) {
      $seen[$sig] = $n
      $crop = $b.Clone((New-Object Drawing.Rectangle($x0, $y0, ($x1 - $x0), ($y1 - $y0))), $b.PixelFormat)
      $crop.Save("$root\shots\hover_$n.png"); $crop.Dispose()
      "$n $fx $fy"; $n++
    }
    $b.Dispose()
  }
}
"distinct hot texts: $n"
