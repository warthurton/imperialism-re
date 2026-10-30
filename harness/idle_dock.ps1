# Background watcher: shrink the game to the top-right corner once the harness has been idle for 10 seconds.
# Every harness input (Ensure-Focus) stamps shots\.last_input and docks the window large again. Exits when the game does.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
$stamp = "$root\shots\.last_input"
$mutex = New-Object Threading.Mutex($false, 'Global\ImperialismIdleDock'); if (-not $mutex.WaitOne(0)) { return }
while (Get-Process Imperialism -ErrorAction SilentlyContinue) {
  Start-Sleep -Seconds 1
  if ((Mirror) -eq [IntPtr]::Zero -or -not (Test-Path $stamp)) { continue }
  $age = ((Get-Date) - (Get-Item $stamp).LastWriteTime).TotalSeconds
  $r = Get-GameRect
  if ($age -ge 10 -and ($r.R - $r.L) -ge 1200) { Dock-Small }
}
