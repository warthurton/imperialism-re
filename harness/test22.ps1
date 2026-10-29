$root = $PSScriptRoot
. "$root\gw.ps1"
Add-Type -AssemblyName System.Drawing
function Analyze($path) {
  $b = [Drawing.Bitmap]::FromFile($path); $w=$b.Width; $h=$b.Height
  $brown = 0; $tot = 0; $minX=$w; $maxX=0; $minY=$h; $maxY=0
  for ($y=0; $y -lt $h; $y+=4) { for ($x=0; $x -lt $w; $x+=4) {
    $c=$b.GetPixel($x,$y); $tot++
    if ($c.R -eq 84 -and $c.G -eq 46 -and $c.B -eq 8) { $brown++ } else { if($x -lt $minX){$minX=$x}; if($x -gt $maxX){$maxX=$x}; if($y -lt $minY){$minY=$y}; if($y -gt $maxY){$maxY=$y} }
  } }
  $b.Dispose()
  "{0}: {1}x{2}  brown={3:P0}  picture bbox x {4}-{5} ({6} wide), y {7}-{8} ({9} high)" -f (Split-Path $path -Leaf),$w,$h,($brown/$tot),$minX,$maxX,($maxX-$minX+4),$minY,$maxY,($maxY-$minY+4)
}
$game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
try {
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  [GW]::Shot((Mirror), "$root\shots\160_windowed.png"); Analyze "$root\shots\160_windowed.png"
  [GW]::Key(0x7A); Start-Sleep -Seconds 2
  [GW]::Shot((Mirror), "$root\shots\161_fullscreen.png"); Analyze "$root\shots\161_fullscreen.png"
  [GW]::Key(0x7A); Start-Sleep -Seconds 2
  [GW]::Shot((Mirror), "$root\shots\162_back.png"); Analyze "$root\shots\162_back.png"
} finally { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue; Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force }
