$root = $PSScriptRoot
. "$root\gw.ps1"
Add-Type -AssemblyName System.Drawing
$shots = "$root\shots"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function Diff($a, $b) {
  $x = New-Object System.Drawing.Bitmap $a; $y = New-Object System.Drawing.Bitmap $b
  $sum = 0; $n = 0
  for ($i = 0; $i -lt [Math]::Min($x.Width, $y.Width); $i += 16) { for ($j = 0; $j -lt [Math]::Min($x.Height, $y.Height); $j += 16) {
    $p = $x.GetPixel($i, $j); $q = $y.GetPixel($i, $j); $sum += [Math]::Abs($p.R - $q.R) + [Math]::Abs($p.G - $q.G) + [Math]::Abs($p.B - $q.B); $n++ } }
  $x.Dispose(); $y.Dispose(); [Math]::Round($sum / $n, 1)
}
$script:prev = $null
function Act($name, [scriptblock]$do) {
  & $do
  Start-Sleep -Milliseconds 2500
  $path = "$shots\$name.png"; [GW]::Shot((Mirror), $path)
  $d = 'n/a'; if ($script:prev) { $d = [GW]::DiffImages($script:prev, $path) }
  "{0,-28} change vs previous: {1}" -f $name, $d
  $script:prev = $path
}
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  ClickAt 936 905; Start-Sleep -Seconds 12
  Act '90_newspaper_with_dialog' { }
  Act '91_dialog_closed'          { ClickAt 1015 216 }
  Act '92_click_paper_bottom'     { ClickAt 650 975 }
  Act '93_press_enter'            { [GW]::Key(0x0D) }
  Act '94_press_space'            { [GW]::Key(0x20) }
  Act '95_press_escape'           { [GW]::Key(0x1B) }
  Act '96_click_question_mark'    { ClickAt 1210 90 }
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
