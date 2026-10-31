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
  # -> $null, or @{ X; Y; W; H; Kind } in game pixels. Kind: 'construct' (320x320) or 'production' (276x149) or 'other'.
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
  $kind = if ($dlg.W -eq 320 -and $dlg.H -eq 320) { 'construct' } elseif ($dlg.W -eq 276 -and $dlg.H -eq 149) { 'production' } else { 'other' }
  @{ X = $dlg.L - $game.L; Y = $dlg.T - $game.T; W = $dlg.W; H = $dlg.H; Kind = $kind }
}

function Wait-Dialog([bool]$Present = $true, [double]$Max = 3) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $Max) { if ([bool](Get-Dialog) -eq $Present) { Start-Sleep -Milliseconds 150; return $true }; Start-Sleep -Milliseconds 100 }
  return $false
}

# control positions inside a dialog, in game pixels from the dialog's top-left (measured on the Steel Mill, Refinery and Power Plant dialogs)
$script:DLG = @{
  production = @{ close = @(262, 12); plus = @(241, 123); minus = @(77, 122); expand = @(229, 47) }
  construct  = @{ ok = @(273, 301); cancel = @(39, 301) }
}
function Dialog-Click([string]$Control) {
  $d = Get-Dialog; if (-not $d) { throw "no dialog open for '$Control'" }
  $pos = $script:DLG[$d.Kind][$Control]; if (-not $pos) { throw "dialog kind '$($d.Kind)' has no control '$Control'" }
  $mx = $script:MIR_X0 + ($d.X + $pos[0]) * $script:MIR_S; $my = $script:MIR_Y0 + ($d.Y + $pos[1]) * $script:MIR_S
  Click-Wait $mx $my
}
