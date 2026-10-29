$root = $PSScriptRoot
. "$root\gw.ps1"
function Frame { $g = Get-Game; foreach ($p in $g) { foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -like 'Afx:400000*' -and $w[2] -eq 'Imperialism') { return [IntPtr][int64]$w[0] } } }; [IntPtr]::Zero }
function Px($fx, $fy) { $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)) }
function ClickAt($fx, $fy) { $p = Px $fx $fy; [GW]::Click($p[0], $p[1]) }
function EditInfo($f) { $c = [GW]::Children($f) | Where-Object { $_ -match ' Edit ' }; $c }
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  ClickAt 230 580; Start-Sleep -Seconds 4
  $f = Frame
  $line = EditInfo $f; $edit = [IntPtr][int64](($line -split ' ')[0])
  "edit hwnd=$edit  " + [GW]::StyleOf($edit) + "   (ES_READONLY = 0x800)"
  ClickAt 935 558; Start-Sleep -Milliseconds 600
  "--- A) real keystrokes via keybd_event, 'Xy':"
  [GW]::Text('Xy'); Start-Sleep -Milliseconds 600
  "    text now: '" + [GW]::TextOf($edit) + "'"
  "--- B) WM_CHAR posted straight to the Edit, 'Z':"
  [GW]::PostMessage($edit, 0x0102, [IntPtr][int][char]'Z', [IntPtr]1) | Out-Null; Start-Sleep -Milliseconds 600
  "    text now: '" + [GW]::TextOf($edit) + "'"
  "--- C) WM_SETTEXT 'Testland' (programmatic, not typing):"
  [GW]::SendMessage($edit, 0x000C, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
  "    (skipped: needs string marshalling; B decides it)"
  "--- D) Backspace key x3:"
  [GW]::Key(0x08); [GW]::Key(0x08); [GW]::Key(0x08); Start-Sleep -Milliseconds 600
  "    text now: '" + [GW]::TextOf($edit) + "'"
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
