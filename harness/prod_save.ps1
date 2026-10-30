# Save the running game into slot 0 with a name and copy it to saves\<file>.imp.
# usage: prod_save.ps1 <file> ["slot name"]   (from the terrain map; slot name max 31 chars, default = the file name)
param([Parameter(Mandatory)][string]$file, [string]$slotName = $file)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
function Click1($fx, $fy, $wait = 2) { Ensure-Focus; $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  [GW]::Click([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0)); Start-Sleep -Seconds $wait }
Click1 1190 80 2; Click1 603 315 3
Click1 200 627 2                                   # the slot: its name becomes an edit box
Ensure-Focus; [GW]::Key(0x23); 1..32 | ForEach-Object { [GW]::Key(0x08) }   # End, then clear with Backspace
[GW]::Text($slotName); Start-Sleep -Milliseconds 500
Click1 1150 472 3                                  # Save Game
Copy-Item 'C:\GOG Games\Imperialism\Save\slot0.imp' (Join-Path (Split-Path $root) "saves\$file.imp") -Force
"saved saves\$file.imp as '$slotName' (add a line for it to saves\README.md)"
