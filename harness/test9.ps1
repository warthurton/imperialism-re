$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Frame { $g = Get-Game; foreach ($p in $g) { foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -like 'Afx:400000*' -and $w[2] -eq 'Imperialism') { return [IntPtr][int64]$w[0] } } }; [IntPtr]::Zero }
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4              # globe -> setup screen
  $f = Frame
  "--- children of the frame on the setup screen:"
  [GW]::Children($f) | Where-Object { $_ -match ' Edit | AmbitGameWindow' }
  "--- focus before clicking the field:"
  [GW]::Focus([uint32]$game.Id)
  ClickAt 935 558; Start-Sleep -Milliseconds 800     # click the Country field
  "--- focus after clicking the field:"
  [GW]::Focus([uint32]$game.Id)
  "--- field text before: " + (([GW]::Children($f) | Where-Object { $_ -match ' Edit ' }) -join ' ; ')
  [GW]::Text('Xy')
  Start-Sleep -Milliseconds 800
  "--- field text after typing 'Xy': " + (([GW]::Children($f) | Where-Object { $_ -match ' Edit ' }) -join ' ; ')
  "--- focus after typing:"
  [GW]::Focus([uint32]$game.Id)
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
