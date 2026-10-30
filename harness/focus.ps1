# Ensure-Focus: make sure the game (mirror window) is the foreground window before any automated click or key.
# Restores focus if it was lost; throws if it cannot, so a test never sends input to the wrong window.
Add-Type -Namespace FG -Name Api -MemberDefinition @'
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
[DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
'@
function Test-GameForeground {
  $pid_ = (Get-Process Imperialism -ErrorAction SilentlyContinue | Select-Object -First 1).Id
  $p = 0; [FG.Api]::GetWindowThreadProcessId([FG.Api]::GetForegroundWindow(), [ref]$p) | Out-Null
  return ($pid_ -and $p -eq $pid_)
}
# Wake-Game: tell the idle watcher "I am about to interact" (named event), then wait until the window is large.
# If no watcher is running, restore the size directly.
function Wake-Game {
  try { $ev = [Threading.EventWaitHandle]::OpenExisting('Global\ImperialismWake'); $ev.Set() | Out-Null; $ev.Dispose() } catch {}
  for ($i = 0; $i -lt 10; $i++) {
    $r = Get-GameRect; if (($r.R - $r.L) -ge 1200) { return }
    Start-Sleep -Milliseconds 200
  }
  Dock-Large
}

function Ensure-Focus {
  Set-Content -Path "$PSScriptRoot\shots\.last_input" -Value (Get-Date).Ticks
  Wake-Game
  if (Test-GameForeground) { return }
  Write-Host 'focus lost -> restoring'
  $m = Mirror
  for ($i = 0; $i -lt 5; $i++) {
    if ([FG.Api]::IsIconic($m)) { [FG.Api]::ShowWindow($m, 9) | Out-Null }
    [FG.Api]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [FG.Api]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)  # Alt tap lets SetForegroundWindow through
    [FG.Api]::SetForegroundWindow($m) | Out-Null
    Start-Sleep -Milliseconds 400
    if (Test-GameForeground) { Write-Host 'focus restored'; return }
  }
  throw 'could not give the game focus; not sending input'
}

# Docking: tests click in the large window (the 1296x999-ish layout all click coordinates are calibrated for); when idle the
# window sits small in the top-right corner so it stays out of the user's way. The shim keeps the picture's aspect ratio and
# will not go below its minimum (672x578 here), so "small" is that minimum.
function Get-GameRect { $r = New-Object GW+RECT; [GW]::GetWindowRect((Mirror), [ref]$r) | Out-Null; $r }
function Dock-Large {
  Add-Type -AssemblyName System.Windows.Forms
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $r = Get-GameRect
  if (($r.R - $r.L) -ge 1200) { return }
  $w = 1296; $h = [Math]::Min(999, $b.Height - 40)
  [GW]::SetWindowPos((Mirror), [IntPtr]::Zero, [int](($b.Width - $w) / 2), [int](($b.Height - $h) / 2), $w, $h, 0x0004) | Out-Null
  Start-Sleep -Milliseconds 1200
}
function Dock-Small {
  Add-Type -AssemblyName System.Windows.Forms
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $m = Mirror
  [GW]::SetWindowPos($m, [IntPtr]::Zero, $b.Right - 672, $b.Top, 672, 578, 0x0004) | Out-Null
  Start-Sleep -Milliseconds 800
  $r = Get-GameRect
  [GW]::SetWindowPos($m, [IntPtr]::Zero, $b.Right - ($r.R - $r.L), $b.Top, 0, 0, 0x0005) | Out-Null   # NOSIZE: anchor to the right edge
  Start-Sleep -Milliseconds 400
}
function Place-GameWindow { Dock-Small }
