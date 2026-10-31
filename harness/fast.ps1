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
