# Background watcher for the test window:
#  * shrink to the top-right corner after 10 s without harness input (idle),
#  * restore the large size when signalled (named event Global\ImperialismWake, sent by Wake-Game), when the game GAINS focus,
#    or when the harness stamps shots\.last_input (Ensure-Focus). Exits when the game does.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
$stamp = "$root\shots\.last_input"
$mutex = New-Object Threading.Mutex($false, 'Global\ImperialismIdleDock'); if (-not $mutex.WaitOne(0)) { return }
$wake = New-Object Threading.EventWaitHandle($false, [Threading.EventResetMode]::AutoReset, 'Global\ImperialismWake')   # Wake-Game signals this
$wasFg = Test-GameForeground
$lastStamp = if (Test-Path $stamp) { (Get-Item $stamp).LastWriteTime } else { [datetime]::MinValue }
while (Get-Process Imperialism -ErrorAction SilentlyContinue) {
  $woken = $wake.WaitOne(400)
  if ((Mirror) -eq [IntPtr]::Zero) { continue }
  $fg = Test-GameForeground
  $r = Get-GameRect; $small = (($r.R - $r.L) -lt 1200)
  $stampTime = if (Test-Path $stamp) { (Get-Item $stamp).LastWriteTime } else { [datetime]::MinValue }
  if ($small -and ($woken -or (-not $wasFg -and $fg) -or $stampTime -gt $lastStamp)) { Dock-Large; $r = Get-GameRect; $small = $false }   # focus gained / input requested
  if ($stampTime -gt $lastStamp) { $lastStamp = $stampTime }
  if (-not $small -and $stampTime -ne [datetime]::MinValue -and ((Get-Date) - $stampTime).TotalSeconds -ge 10) { Dock-Small; $fg = Test-GameForeground }
  $wasFg = $fg
}
