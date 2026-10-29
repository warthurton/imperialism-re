$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
$script:game = $null
function Alive($label) {
  Start-Sleep -Milliseconds 1200
  $alive = -not $script:game.HasExited
  $wins = if ($alive) { ([GW]::Windows([uint32]$script:game.Id) | Where-Object { $_[1] -eq 'AmbitMcWindow' -and $_[3] -eq 'vis' }).Count } else { 0 }
  "{0,-40} alive={1}  visible dialogs={2}" -f $label, $alive, $wins
  if (-not $alive) { "  >>> game exited, exit code 0x{0:x}" -f $script:game.ExitCode; throw 'game died' }
}
try {
  $script:game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4;  Alive 'title screen'
  ClickAt 230 580; Start-Sleep -Seconds 4;  Alive 'setup screen'
  ClickAt 936 905; Start-Sleep -Seconds 12; Alive 'newspaper + briefing dialog'
  ClickAt 1015 216; Start-Sleep -Seconds 2; Alive 'closed newspaper dialog (X)'
  ClickAt 75 90;   Start-Sleep -Seconds 5;  Alive 'clicked newspaper exit arrow -> map'
  [GW]::Shot((Mirror), "$shots\120_map_with_dialog.png")
  ClickAt 897 182; Start-Sleep -Seconds 3;  Alive 'closed terrain briefing dialog (X)'
  [GW]::Shot((Mirror), "$shots\121_map_after_close.png")
  $p = Px 600 500; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null
  Start-Sleep -Milliseconds 800;           Alive 'cursor moved over the map'
  [GW]::Wheel(-120);                        Alive 'wheel x1 (down)'
  [GW]::Wheel(-120);                        Alive 'wheel x2'
  [GW]::Wheel(120);                         Alive 'wheel x3 (up)'
  [GW]::Shot((Mirror), "$shots\122_after_wheel.png")
}
catch { "stopped: $_" }
finally {
  if ($script:game) { Stop-Process -Id $script:game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
