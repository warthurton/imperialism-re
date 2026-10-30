# Reject trade offers with the Esc hot key for as long as the red REJECT seal is on screen.
$root = $PSScriptRoot
. "$root\gw.ps1"
. "$root\focus.ps1"
Add-Type -AssemblyName System.Drawing
function Seal {
  [GW]::Shot((Mirror), "$root\shots\_seal.png")
  $b = [Drawing.Bitmap]::FromFile("$root\shots\_seal.png")
  $x0 = [int]($b.Width * 155 / 1251); $x1 = [int]($b.Width * 235 / 1251); $y0 = [int]($b.Height * 765 / 956); $y1 = [int]($b.Height * 835 / 956)
  $r = 0; $g = 0; $bl = 0; $k = 0
  for ($y = $y0; $y -lt $y1; $y += 3) { for ($x = $x0; $x -lt $x1; $x += 3) { $c = $b.GetPixel($x, $y); $r += $c.R; $g += $c.G; $bl += $c.B; $k++ } }
  $b.Dispose()
  return ((($r - ($g + $bl) / 2) / $k) -gt 45)
}
function Click1($ix, $iy) {   # image coords in a 1251x956 screenshot
  Ensure-Focus
  $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $ix / 1251.0 * ($r.R - $r.L)), [int]($r.T + $iy / 956.0 * ($r.B - $r.T)))
}
$n = 0
while ($n -lt 25 -and (Seal)) {
  Ensure-Focus
  [GW]::Key(0x1B); Start-Sleep -Seconds 2        # Esc = Reject (readme hot keys: Esc rejects offers, Return accepts)
  $n++
}
"rejected $n offers"
[GW]::Shot((Mirror), "$root\shots\p14_after_offers.png")
