param([string]$Mode = 'shim', [int]$N = 1, [string]$Out = '', [string]$ShotPath = '')
$root = $PSScriptRoot
. "$root\gw.ps1"
. "$root\audio.ps1"
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
function Peak($label, $sec) {
  $m = 0.0; $n = 0
  for ($i = 0; $i -lt $sec * 4; $i++) { $v = [AudioPeek]::Peak([uint32]$script:game.Id); if ($v -gt $m) { $m = $v }; if ($v -gt 0.001) { $n++ }; Start-Sleep -Milliseconds 250 }
  "{0,-22} peak={1:N3} loud={2}/{3}" -f $label, $m, $n, ($sec*4)
}
function One($i) {
  $script:game = Start-Process "$gameDir\Imperialism.exe" -WorkingDirectory $gameDir -PassThru
  try {
    $t=0; while ((Mirror) -eq [IntPtr]::Zero -and $t -lt 60) { Start-Sleep -Milliseconds 500; $t++ }
    Peak 'title screen' 8
    Click 111 274;  Peak 'setup screen' 5
    Click 464 437;  Peak 'loading/news' 12
    Click 503 92;   Peak 'news dialog closed' 3
    Click 33 29;    Peak 'main map (early)' 6
    Click 444 75;   Peak 'map dialog closed' 6
    Peak 'map (later)' 10
  } finally {
    Stop-Process -Id $script:game.Id -Force -ErrorAction SilentlyContinue
    Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
  }
}
One 1
