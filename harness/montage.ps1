# usage: montage.ps1 <prefix> <count> <out.png>   -- stack shots\<prefix>_0..N-1.png vertically, labelled with their index, scaled 2x
param([string]$prefix, [int]$count, [string]$out)
Add-Type -AssemblyName System.Drawing
$imgs = 0..($count - 1) | ForEach-Object { [Drawing.Bitmap]::FromFile("$PSScriptRoot\shots\${prefix}_$_.png") }
$w = ($imgs | Measure-Object Width -Maximum).Maximum; $h = ($imgs | Measure-Object Height -Sum).Sum
$bmp = New-Object Drawing.Bitmap(($w + 40), $h); $g = [Drawing.Graphics]::FromImage($bmp); $g.Clear([Drawing.Color]::White)
$y = 0; $i = 0; $font = New-Object Drawing.Font('Arial', 12)
foreach ($im in $imgs) { $g.DrawString("$i", $font, [Drawing.Brushes]::Black, 2, $y + 10); $g.DrawImage($im, 40, $y); $y += $im.Height; $i++ }
$big = New-Object Drawing.Bitmap(($bmp.Width * 2), ($bmp.Height * 2)); $g2 = [Drawing.Graphics]::FromImage($big); $g2.DrawImage($bmp, 0, 0, $big.Width, $big.Height)
$big.Save("$PSScriptRoot\shots\$out"); "saved $out"
