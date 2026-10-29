$root = $PSScriptRoot
. "$root\gw.ps1"
$shots = "$root\shots"
function State($name, $wait = 1500) {
  Start-Sleep -Milliseconds $wait
  "=== $name"
  Show-GameWindows | Where-Object { $_ -notmatch 'IME' }
  $m = Mirror
  if ($m -ne [IntPtr]::Zero) { [GW]::Shot($m, "$shots\$name.png") }
}
$m = Mirror
$r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
$w = $r.R - $r.L; $h = $r.B - $r.T
"mirror $($r.L),$($r.T) ${w}x${h}"
# Start Game button is at (936,905) in a 1296x999 mirror
[GW]::Click([int]($r.L + 936 * $w / 1296.0), [int]($r.T + 905 * $h / 999.0))
State '30_after_start_game' 9000
