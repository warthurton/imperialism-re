$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function Frame { $g = Get-Game; foreach ($p in $g) { foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -like 'Afx:400000*' -and $w[2] -eq 'Imperialism') { return [IntPtr][int64]$w[0] } } }; [IntPtr]::Zero }
function Check($name) {
  Start-Sleep -Milliseconds 1500
  $m = Mirror; $f = Frame
  $fr = New-Object GW+RECT; [GW]::GetWindowRect($f, [ref]$fr) | Out-Null
  "=== $name"
  "mirror window : " + (Show-GameWindows | Where-Object { $_ -match 'ImperialismMirror' })
  "mirror client : " + [GW]::ClientScreenRect($m)
  "frame window  : ($($fr.L),$($fr.T) $($fr.R-$fr.L)x$($fr.B-$fr.T))"
  $c = New-Object GW+RECT; [GW]::GetClientRect($m, [ref]$c) | Out-Null
  $p = New-Object GW+POINT; [GW]::ClientToScreen($m, [ref]$p) | Out-Null
  $inside = ($fr.L -ge $p.X) -and ($fr.T -ge $p.Y) -and ($fr.R -le $p.X + $c.R) -and ($fr.B -le $p.Y + $c.B)
  "frame fully inside mirror client: $inside"
  [GW]::ShotMargin($m, "$shots\$name.png", 40)
}
$game = $null
try {
  $game = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
  $t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
  Start-Sleep -Seconds 4
  Check '60_default'
  $m = Mirror
  [GW]::SetWindowPos($m, [IntPtr]::Zero, 300, 200, 100, 100, 0x14) | Out-Null   # ask for tiny: should clamp to minimum
  Check '61_smallest_allowed'
  [GW]::SetWindowPos($m, [IntPtr]::Zero, 150, 100, 900, 700, 0x14) | Out-Null
  Check '62_900x700'
}
finally {
  if ($game) { Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue }
  Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  'cleanup done: game stopped'
}
