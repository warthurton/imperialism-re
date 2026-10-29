param([string]$Mode = 'shim', [int]$N = 6, [string]$Out = '', [string]$ShotPath = '')
$root = $PSScriptRoot
. "$root\gw.ps1"
$gameDir = 'C:\GOG Games\Imperialism'
$shim = "$gameDir\msvfw32.dll"; $shimOff = "$gameDir\msvfw32.dll.off"
$script:game = $null

function FrameWnd { foreach ($p in (Get-Game)) { foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -like 'Afx:400000*' -and $w[2] -eq 'Imperialism' -and $w[3] -eq 'vis') { return [IntPtr][int64]$w[0] } } }; [IntPtr]::Zero }
function V2S($vx, $vy) {     # game-view coords (640x480) -> screen coords
  if ($Mode -eq 'shim') {
    $m = Mirror; $r = New-Object GW+RECT; $p = New-Object GW+POINT
    [GW]::GetClientRect($m, [ref]$r) | Out-Null; [GW]::ClientToScreen($m, [ref]$p) | Out-Null
    $s = $r.R / 640.0
    return @([int]($p.X + $vx * $s), [int]($p.Y + $vy * $s))
  }
  $f = FrameWnd
  $c = [GW]::Children($f) | Where-Object { $_ -match 'AmbitGameWindow' } | Select-Object -First 1
  if ($c -match '\((-?\d+),(-?\d+) (\d+)x(\d+)\)') { return @([int]([int]$Matches[1] + $vx), [int]([int]$Matches[2] + $vy)) }
  throw 'no AmbitGameWindow'
}
function Click($vx, $vy) { $p = V2S $vx $vy; [GW]::Click($p[0], $p[1]) }
function MoveTo($vx, $vy)  { $p = V2S $vx $vy; [GW]::SetCursorPos($p[0], $p[1]) | Out-Null }
function Dead { $script:game.HasExited }
function Wait-Ready {
  $t = 0
  while ($t -lt 60) {
    if ($Mode -eq 'shim') { if ((Mirror) -ne [IntPtr]::Zero) { break } } else { if ((FrameWnd) -ne [IntPtr]::Zero) { break } }
    Start-Sleep -Milliseconds 500; $t++
  }
  Start-Sleep -Seconds 4
}
function One($i) {
  $start = Get-Date
  $script:game = Start-Process "$gameDir\Imperialism.exe" -WorkingDirectory $gameDir -PassThru
  $phase = 'launch'
  try {
    Wait-Ready;                               if (Dead) { throw 'died' }
    $phase = 'title->setup'; Click 111 274;   Start-Sleep -Seconds 4;  if (Dead) { throw 'died' }
    $phase = 'setup->game';  Click 464 437;   Start-Sleep -Seconds 12; if (Dead) { throw 'died' }
    $phase = 'close news dlg'; Click 503 92;  Start-Sleep -Seconds 2;  if (Dead) { throw 'died' }
    $phase = 'news->map';    Click 33 29;     Start-Sleep -Seconds 5;  if (Dead) { throw 'died' }
    $phase = 'close map dlg'; Click 444 75;   Start-Sleep -Seconds 3;  if (Dead) { throw 'died' }
    if ($ShotPath) {   # verification aid: prove the run really reached the map
      $win = if ($Mode -eq 'shim') { Mirror } else { FrameWnd }
      [GW]::Shot($win, "$ShotPath-$Mode-before-stress.png")
    }
    $rnd = New-Object System.Random 42
    for ($k = 1; $k -le 70; $k++) {
      $phase = "stress op $k"
      $op = $rnd.Next(100)
      if ($op -lt 55)      { MoveTo ($rnd.Next(10, 510)) ($rnd.Next(45, 470)); Start-Sleep -Milliseconds 120 }
      elseif ($op -lt 75)  { Click ($rnd.Next(10, 510)) ($rnd.Next(45, 470)); Start-Sleep -Milliseconds 400 }
      elseif ($op -lt 90)  { [GW]::Wheel(-120); [GW]::Wheel(120); [GW]::Wheel(-120); Start-Sleep -Milliseconds 100 }
      else                 { MoveTo ($rnd.Next(520, 630)) ($rnd.Next(40, 400)); Start-Sleep -Milliseconds 150 }
      if ($k % 5 -eq 0 -and (Dead)) { throw 'died' }
    }
    Start-Sleep -Seconds 2
    $phase = 'end'; if (Dead) { throw 'died' }
    return "run ${i}: OK (survived to the end)"
  } catch {
    $code = if ($script:game.HasExited) { '0x{0:x}' -f $script:game.ExitCode } else { 'running' }
    return "run ${i}: CRASH/EXIT during '$phase' (exit code $code)"
  } finally {
    if ($script:game -and -not $script:game.HasExited) { Stop-Process -Id $script:game.Id -Force -ErrorAction SilentlyContinue }
    Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    $script:wer = (Get-WinEvent -FilterHashtable @{LogName = 'Application'; Id = 1000; StartTime = $start} -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'Imperialism' }).Count
    $script:wm = ''
    if ($Mode -eq 'shim') {
      $l = Select-String -Path "$gameDir\imperialism_gdi_log.txt" -Pattern '^winmm patch:' -ErrorAction SilentlyContinue | Select-Object -Last 1
      if ($l) { $script:wm = ($l.Line -replace 'winmm patch: ', '') }
    }
  }
}

$results = @()
try {
  if ($Mode -eq 'noshim') { Move-Item $shim $shimOff -Force }
  for ($i = 1; $i -le $N; $i++) {
    $r = One $i
    $line = "$r   [WER crash events: $script:wer]   [winmm: $script:wm]"
    $line; $results += $line
    if ($Out) { Add-Content -Path $Out -Value "[$Mode] $line" }
  }
}
finally {
  if ($Mode -eq 'noshim' -and (Test-Path $shimOff)) { Move-Item $shimOff $shim -Force }
  "restored shim present: " + (Test-Path $shim)
}
$crashes = ($results | Where-Object { $_ -match 'CRASH' }).Count
"SUMMARY [$Mode]: $crashes crashes in $N runs"
if ($Out) { Add-Content -Path $Out -Value "SUMMARY [$Mode]: $crashes crashes in $N runs" }
