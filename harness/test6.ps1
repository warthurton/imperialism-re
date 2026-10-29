$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function State($name, $wait = 1500) {
  Start-Sleep -Milliseconds $wait
  "=== $name"
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
  $m = Mirror
  if ($m -ne [IntPtr]::Zero) { [GW]::Shot($m, "$shots\$name.png") } else { "(no visible mirror)" }
}
function ClickAt($fx, $fy) {   # fx,fy in a 1296x999 mirror
  $m = Mirror
  $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0))
}
$game = $null; $np = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  State '40_start'
  ClickAt 230 580           # globe -> new game setup
  State '41_setup' 3500
  ClickAt 936 905           # Start Game
  State '42_after_start' 12000
  "--- stealing focus with Notepad for 4s"
  $np = Start-Process notepad.exe -PassThru
  State '43_during_notepad' 4000
  if ($np) { Stop-Process -Id $np.Id -Force -ErrorAction SilentlyContinue }
  State '44_after_notepad' 2000
}
finally {
  if ($np) { Stop-Process -Id $np.Id -Force -ErrorAction SilentlyContinue }
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game and notepad stopped'
}
