$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function State($name) {
  Start-Sleep -Milliseconds 1500
  "=== $name"
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
  $m = Mirror
  if ($m -ne [IntPtr]::Zero) { [GW]::Shot($m, "$shots\$name.png") }
}
$p = Start-Process 'C:\GOG Games\Imperialism\Imperialism.exe' -WorkingDirectory 'C:\GOG Games\Imperialism' -PassThru
$t = 0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 40) { Start-Sleep -Milliseconds 500; $t++ }
Start-Sleep -Seconds 4
State '20_start'
$m = Mirror
$r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
"mirror at $($r.L),$($r.T) $($r.R-$r.L)x$($r.B-$r.T)"
# globe is at about (230,580) inside a 1400x1000 mirror; scale click to actual size
$sx = ($r.R - $r.L) / 1400.0; $sy = ($r.B - $r.T) / 1000.0
[GW]::Click([int]($r.L + 230 * $sx), [int]($r.T + 580 * $sy))
State '21_after_globe_click'
Start-Sleep -Seconds 4
State '22_four_seconds_later'
