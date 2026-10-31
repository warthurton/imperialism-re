# End the turn from the terrain map and play through to the next turn's map, driven by the screen id (read from the game's memory)
# instead of fixed sleeps and pixel colours.   usage: prod_endturn.ps1 [-Log]   (-Log prints every screen id it passes through)
#   id 2013 = terrain map (done)   id 8500 = trade "Offer Sheet": Escape rejects it (manual hot key; Return accepts)
#   id 8800 = trade results book (Sold / Bought / Bottom Line)   id 8451 = the Imperial Times newspaper: Return moves on from both
#   any other id: logged with a screenshot (shots\et_<id>.png), then tried in turn: Return, the old "next" click (62,136), the
#   newspaper exit (75,90), Escape.
param([switch]$Log)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
$sw = [Diagnostics.Stopwatch]::StartNew()
function Stamp($m) { if ($Log) { "{0,5:N1}s {1}" -f $sw.Elapsed.TotalSeconds, $m } }
$id = Get-ScreenId
if ($id -ne 2013) { Close-DialogIfAny; Post-Key 0x1B; Start-Sleep -Milliseconds 400; $id = Get-ScreenId }   # Esc leaves a screen for the map
if ($id -ne 2013) { Click-Wait 57 135; $id = Get-ScreenId }
if ($id -ne 2013) { throw "not on the terrain map (screen id $id)" }
Click-Wait 1160 955 0.5               # End Turn
$last = -1; $same = 0; $rejected = 0; $tried = @{}
for ($i = 0; $i -lt 400; $i++) {
  $id = Get-ScreenId
  if ($id -ne $last) { Stamp "screen id $id"; $last = $id; $same = 0 } else { $same++ }
  if ($id -eq 2013 -and $i -gt 3) { break }
  if ($id -eq 8500) { Post-Key 0x1B; $rejected++; Start-Sleep -Milliseconds 350; continue }
  if ($id -eq 8800 -or $id -eq 8451) { Start-Sleep -Milliseconds 400; Post-Key 0x0D; Start-Sleep -Milliseconds 350; continue }   # trade results book, Imperial Times
  if ($id -ne 2013 -and $same -eq 6) {            # an unfamiliar screen that does not move on by itself
    if (-not $tried[$id]) { $tried[$id] = 0; Snap "et_$id" | Out-Null }
    $n = $tried[$id]; $tried[$id] = $n + 1
    switch ($n % 4) {
      0 { Stamp "id ${id}: Return"; Post-Key 0x0D }
      1 { Stamp "id ${id}: click next (62,136)"; Click-Wait 62 136 2 }
      2 { Stamp "id ${id}: click newspaper exit (75,90)"; Click-Wait 75 90 2 }
      3 { Stamp "id ${id}: Escape"; Post-Key 0x1B }
    }
    $same = 0
  }
  Start-Sleep -Milliseconds 150
}
if ($id -ne 2013) { throw "end of turn did not finish (screen id $id)" }
"turn ended in $([int]$sw.Elapsed.TotalSeconds) s, $rejected offers rejected"
