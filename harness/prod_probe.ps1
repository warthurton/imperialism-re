# Click candidate points (1296x999 coords), each followed by closing any dialog with Escape-less method: we only read the title crop.
param([string]$points)   # "x,y;x,y;..."
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
Add-Type -AssemblyName System.Drawing
$crops = @(); $i = 0
foreach ($pt in $points.Split(';')) {
  $xy = $pt.Split(','); $fx = [double]$xy[0]; $fy = [double]$xy[1]
  Ensure-Focus
  $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds 2
  $f = "$root\shots\_probe$i.png"; [GW]::Shot((Mirror), $f)
  $b = [Drawing.Bitmap]::FromFile($f); $c = $b.Clone((New-Object Drawing.Rectangle(700, 35, [Math]::Min(540, $b.Width-700), 70)), $b.PixelFormat); $b.Dispose(); $crops += $c; $i++
}
$out = New-Object Drawing.Bitmap -ArgumentList 540, (70 * $crops.Count); $g = [Drawing.Graphics]::FromImage($out)
for ($k = 0; $k -lt $crops.Count; $k++) { $g.DrawImage($crops[$k], 0, 70 * $k) }
$out.Save("$root\shots\probe_titles.png"); "saved probe_titles.png ($($crops.Count) crops)"
