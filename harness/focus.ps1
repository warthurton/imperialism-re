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
function Ensure-Focus {
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
