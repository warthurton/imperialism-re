# Faster input helpers: instead of a fixed sleep after every click, wait until the screen stops changing.
# Dot-source after gw.ps1 and focus.ps1:   . "$root\fast.ps1"
# Coordinates are in 1296x999 "mirror" units, like the rest of the harness.
Add-Type -AssemblyName System.Drawing

function Wait-Stable([double]$Min = 0.35, [double]$Max = 6, [double]$Tol = 0.6, [string]$Before = '', [double]$Start = 1.5) {
  # $Before = a screenshot taken just before the click: first wait (up to $Start s) for the screen to differ from it, so a slow
  # transition that has not begun yet is not mistaken for "settled".
  if ($Before) {
    $sw0 = [Diagnostics.Stopwatch]::StartNew(); $probe = "$PSScriptRoot\shots\_w0.png"
    while ($sw0.Elapsed.TotalSeconds -lt $Start) { [GW]::Shot((Mirror), $probe); if ([GW]::DiffImages($Before, $probe) -ge $Tol) { break }; Start-Sleep -Milliseconds 100 }
  }
  # Poll a screenshot every ~150 ms; done after two consecutive polls differ by less than $Tol (mean |RGB| difference of a sparse
  # pixel sample; idle ambient animation, e.g. grazing cows, stays below that). Never returns before $Min or after $Max seconds.
  $sw = [Diagnostics.Stopwatch]::StartNew(); $a = "$PSScriptRoot\shots\_w1.png"; $b = "$PSScriptRoot\shots\_w2.png"; $calm = 0
  [GW]::Shot((Mirror), $a)
  while ($sw.Elapsed.TotalSeconds -lt $Max) {
    Start-Sleep -Milliseconds 120
    [GW]::Shot((Mirror), $b)
    $d = [GW]::DiffImages($a, $b); Copy-Item $b $a -Force
    if ($d -lt $Tol) { $calm++ } else { $calm = 0 }
    if ($calm -ge 2 -and $sw.Elapsed.TotalSeconds -ge $Min) { break }
  }
}

function Mirror-Px($fx, $fy) {
  $m = Mirror; $r = New-Object GW+RECT; [GW]::GetWindowRect($m, [ref]$r) | Out-Null
  @([int]($r.L + $fx * ($r.R - $r.L) / 1296.0), [int]($r.T + $fy * ($r.B - $r.T) / 999.0))
}

function Click-Wait($fx, $fy, [double]$Max = 6) {
  Ensure-Focus; $before = "$PSScriptRoot\shots\_wb.png"; [GW]::Shot((Mirror), $before)
  $p = Mirror-Px $fx $fy; [GW]::Click($p[0], $p[1]); Wait-Stable -Max $Max -Before $before
}

function Snap([string]$name) { [GW]::Shot((Mirror), "$PSScriptRoot\shots\$name.png"); "shot $name" }

# ---- dialogs, read from Windows instead of screenshots ------------------------------------------------------------------
# Every dialog is an "AmbitMcWindow" child of the game frame. Its screen rect, taken relative to the 640x480 "AmbitGameWindow",
# gives its position in game pixels; the mirror shows the game at 1.993x with the 640x480 area starting at (10.4, 34.5) in the
# 1296x999 mirror units used everywhere in the harness (calibrated on the Steel Mill dialog; see docs/production_playtest.md).
$script:MIR_S = 1.993; $script:MIR_X0 = 10.4; $script:MIR_Y0 = 34.5

function Get-Dialog {
  # -> $null, or @{ X; Y; W; H; Kind } in game pixels. Kind: 'construct' (320x320), 'production' (276x149), 'unit' (University etc., 376x439) or 'other'.
  $pid_ = (Get-Process Imperialism -ErrorAction SilentlyContinue | Select-Object -First 1).Id
  if (-not $pid_) { return $null }
  $frame = [GW]::Windows([uint32]$pid_) | Where-Object { $_[1] -like 'Afx:*' -and $_[3] -eq 'vis' } | Select-Object -First 1
  if (-not $frame) { return $null }
  $game = $null; $dlg = $null
  foreach ($c in [GW]::Children([IntPtr][int64]$frame[0])) {
    if ($c -notmatch '^(\d+) (\S+) vis=(\w+) \((-?\d+),(-?\d+) (\d+)x(\d+)\)') { continue }
    $o = @{ Class = $Matches[2]; Vis = ($Matches[3] -eq 'True'); L = [int]$Matches[4]; T = [int]$Matches[5]; W = [int]$Matches[6]; H = [int]$Matches[7] }
    if ($o.Class -eq 'AmbitGameWindow') { $game = $o } elseif ($o.Class -eq 'AmbitMcWindow' -and $o.Vis) { $dlg = $o }
  }
  if (-not $game -or -not $dlg) { return $null }
  $kind = if ($dlg.W -eq 320 -and $dlg.H -eq 320) { 'construct' } elseif ($dlg.W -eq 276 -and $dlg.H -eq 149) { 'production' } elseif ($dlg.W -eq 376 -and $dlg.H -eq 439) { 'unit' } else { 'other' }
  @{ X = $dlg.L - $game.L; Y = $dlg.T - $game.T; W = $dlg.W; H = $dlg.H; Kind = $kind }
}

function Wait-Dialog([bool]$Present = $true, [double]$Max = 3) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $Max) { if ([bool](Get-Dialog) -eq $Present) { Start-Sleep -Milliseconds 150; return $true }; Start-Sleep -Milliseconds 100 }
  return $false
}

# control positions inside a dialog, in game pixels from the dialog's top-left (measured on the Steel Mill, Refinery and Power Plant dialogs)
$script:DLG = @{
  production = @{ close = @(262, 12); plus = @(241, 123); minus = @(77, 122); expand = @(229, 47); knob = @(76, 123); end = @(236, 123) }
  construct  = @{ ok = @(273, 301); cancel = @(39, 301) }
  # unit centres (University; the Armory and Shipyard are expected to match): picture N = select, add N / sub N = its arrows, 2x2 grid (column 1 = rows 1-3, column 2 = row 1)
  unit       = @{ close = @(361, 12); pic1 = @(248, 111); add1 = @(268, 151); sub1 = @(228, 151); pic2 = @(327, 111); add2 = @(347, 151); sub2 = @(307, 151); pic3 = @(248, 193); add3 = @(268, 235); sub3 = @(228, 235); pic4 = @(248, 278); add4 = @(268, 318); sub4 = @(228, 318); a1 = @(248, 111); aa1 = @(268, 151); as1 = @(228, 151); a2 = @(327, 111); aa2 = @(347, 151); as2 = @(307, 151); a3 = @(248, 195); aa3 = @(268, 235); as3 = @(228, 235); a4 = @(327, 195); aa4 = @(347, 235); as4 = @(307, 235); a5 = @(248, 278); aa5 = @(268, 318); as5 = @(228, 318); a6 = @(327, 278); aa6 = @(347, 318); as6 = @(307, 318); a7 = @(248, 362); aa7 = @(268, 402); as7 = @(228, 402); a8 = @(327, 362); aa8 = @(347, 402); as8 = @(307, 402) }
}
function Dialog-Click([string]$Control) {
  $d = Get-Dialog; if (-not $d) { throw "no dialog open for '$Control'" }
  $pos = $script:DLG[$d.Kind][$Control]; if (-not $pos) { throw "dialog kind '$($d.Kind)' has no control '$Control'" }
  $mx = $script:MIR_X0 + ($d.X + $pos[0]) * $script:MIR_S; $my = $script:MIR_Y0 + ($d.Y + $pos[1]) * $script:MIR_S
  Click-Wait $mx $my
}

# ---- keys, sent as window messages (no dependence on which window has focus; a global keybd_event press stopped reaching the game) ----
function Post-Key([int]$Vk) {
  $pid_ = (Get-Process Imperialism -ErrorAction SilentlyContinue | Select-Object -First 1).Id
  $f = [GW]::Windows([uint32]$pid_) | Where-Object { $_[1] -like 'Afx:*' } | Select-Object -First 1
  if (-not $f) { throw 'game frame window not found' }
  $g = [GW]::Children([IntPtr][int64]$f[0]) | Where-Object { $_ -match 'AmbitGameWindow' } | Select-Object -First 1
  foreach ($h in @([IntPtr][int64]$f[0], [IntPtr][int64](($g -split ' ')[0]))) {
    [GW]::PostMessage($h, 0x100, [IntPtr]$Vk, [IntPtr]0x40001) | Out-Null; Start-Sleep -Milliseconds 50
    [GW]::PostMessage($h, 0x101, [IntPtr]$Vk, [IntPtr]([int64]0xC0040001)) | Out-Null
  }
}

# ---- current screen id, read straight from the game's memory in-process (view manager at global 0x6a21bc, short at +4) ----
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class GMem {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint a, bool i, int pid);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, int n, out int got);
  static IntPtr h; static int pid;
  public static int Read(int p, uint addr, int n) {
    if (pid != p || h == IntPtr.Zero) { h = OpenProcess(0x0010 | 0x0400, false, p); pid = p; }
    var b = new byte[4]; int got;
    if (!ReadProcessMemory(h, (IntPtr)addr, b, n, out got) || got != n) return -1;
    return n == 2 ? BitConverter.ToUInt16(b, 0) : BitConverter.ToInt32(b, 0);
  }
}
'@ -ErrorAction SilentlyContinue
function Get-ScreenId {
  $pid_ = (Get-Process Imperialism -ErrorAction SilentlyContinue | Select-Object -First 1).Id
  if (-not $pid_) { return -1 }
  $mgr = [GMem]::Read($pid_, 0x6a21bc, 4); if ($mgr -le 0) { return -1 }
  return [GMem]::Read($pid_, [uint32]($mgr + 4), 2)
}

function Close-DialogIfAny { $d = Get-Dialog; if ($d) { if ($d.Kind -eq 'construct') { Dialog-Click 'cancel' } else { Dialog-Click 'close' }; Wait-Dialog $false | Out-Null } }

function Dialog-Drag([string]$From, [string]$To) {   # drag between two named controls of the open dialog (e.g. the slider knob to its end)
  $d = Get-Dialog; if (-not $d) { throw 'no dialog open' }
  $a = $script:DLG[$d.Kind][$From]; $b = $script:DLG[$d.Kind][$To]
  Ensure-Focus
  $p0 = Mirror-Px ($script:MIR_X0 + ($d.X + $a[0]) * $script:MIR_S) ($script:MIR_Y0 + ($d.Y + $a[1]) * $script:MIR_S)
  $p1 = Mirror-Px ($script:MIR_X0 + ($d.X + $b[0]) * $script:MIR_S) ($script:MIR_Y0 + ($d.Y + $b[1]) * $script:MIR_S)
  [GW]::Drag($p0[0], $p0[1], $p1[0], $p1[1]); Wait-Stable -Max 3
}

# ---- text the game draws, read from the shim's text log (see tools/readtext.py) ----
$script:TEXTLOG = 'C:\GOG Games\Imperialism\imperialism_text.log'
function Text-Mark { if (Test-Path $script:TEXTLOG) { (Get-Item $script:TEXTLOG).Length } else { 0 } }
function Text-Since([long]$Mark) {
  # strings drawn since $Mark, one "x,y text" per line (shadow copies and repeats collapsed)
  $py = Join-Path (Split-Path $PSScriptRoot) 'tools\readtext.py'
  & python -I $py since $Mark
}
