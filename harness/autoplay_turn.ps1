# Autoplay turns. Policy: Prospectors search the nearest visibly unprospected hill/mountain, Farmers and Miners improve a tile (one click, order 10),
# everything else sleeps. Every turn starts with 'w' (rouse sleepers) so units are offered again. Then the turn is ended.
# Reads units from memory (readunits.py needs/sel), picks tiles with maptarget.py (player-visible data only), clicks by window message.
# usage: autoplay_turn.ps1 [-Turns 1]      needs a running game on the terrain map (prod_boot.ps1 first). Modal popups are never opened here.
param([int]$Turns = 1)
$root = $PSScriptRoot; $re = Split-Path $root
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
$py = (Get-Command python).Source
function Needs { (& $py -I "$re\tools\readunits.py" needs | Select-String 'NEEDS ORDERS').Count }
function Selected { & $py -I "$re\tools\readunits.py" sel }
# Advice popups (Interior Minister etc., 390x282 modal) open after a turn even with briefings off and block every message click: dismiss with the mirror click on OK.
# We know when one opens because the game draws its text ("Advice from your <Minister>") into the text log: watch the log from a mark taken before the click.
function Clear-Popups([long]$Mark = -1) {
  for ($i = 0; $i -lt 4; $i++) {
    $d = Get-Dialog; $txt = if ($Mark -ge 0) { (Text-Since $Mark) -join "`n" } else { '' }
    if (($d -and $d.W -eq 390 -and $d.H -eq 282) -or $txt -match 'Advice from your') {
      Write-Host "  advice popup ($(($txt -split "`n" | Where-Object { $_ -match 'Advice|Resources|Minister' } | Select-Object -First 2) -join ' | ')): OK"
      & "$root\msgclick.ps1" 'hc 406 364' | Out-Null; $Mark = Text-Mark; Start-Sleep -Milliseconds 300     # OK button, by the shim's test hook (no focus needed)
    } elseif (($d -and $d.W -eq 300 -and $d.H -eq 200) -or $txt -match 'Civilian Report') {
      # clicking a unit that is already working opens its Civilian Report (Rescind / Confirm): keep its orders with Confirm (mirror (685,630) = game (339,299))
      Write-Host '  civilian report: Confirm'
      & "$root\msgclick.ps1" 'hc 339 299' | Out-Null; $Mark = Text-Mark; Start-Sleep -Milliseconds 300
    } else { break }
  }
}
# Every game click is POSTED (gp), never sent: selecting an Engineer can open an advice popup, and a sent click blocks until the modal popup closes (that hung the script).
function Click-Game([string]$xy) { $m = Text-Mark; & "$root\msgclick.ps1" "gp $xy" | Out-Null; Start-Sleep -Milliseconds 500; Clear-Popups $m }
function Sleep-Unit { Click-Game '621 166' }               # Sleep button (621,166)
# After an accepted order the game selects the next unit by itself, so success = fewer units needing orders.
# A Prospector with nothing eligible on screen clicks the toolbar "Search In" tiles (hills (539,315), mountains (539,335)) to scroll, up to 4 tries.
# Engineer: on a tile worth a depot (own land, ungathered, with a farm or a prospected mineral) open the Construction Options popup by clicking the unit's own tile.
# The popup is modal, so it is opened with a POSTED click; its text comes from the text log ("($2,000) A connected Depot here ..." at x,y inside the popup) and its
# buttons are clicked with mirror clicks (posted clicks do not register there): first option button = popup + (34, text y + 10), Cancel = popup + (46, height - 17).
function Mirror-Game($gx, $gy) { @([int](10.4 + 1.993 * $gx), [int](34.5 + 1.993 * $gy)) }
function Build-Depot($sel) {
  if ($sel -notmatch "'x': (\d+), 'y': (\d+)") { return $false }
  $xy = (& $py -I "$re\tools\maptarget.py" tile $Matches[1] $Matches[2]).Split(' ')
  $before = Needs; $m = Text-Mark
  & "$root\msgclick.ps1" "gp $($xy[2]) $($xy[3])" | Out-Null; Start-Sleep -Milliseconds 1500
  $txt = (Text-Since $m) -join "`n"; $d = Get-Dialog
  if ($txt -notmatch 'Construction Options' -or -not $d) { Clear-Popups $m; return $false }
  $line = ($txt -split "`n") | Where-Object { $_ -match '^\d+,\d+ \(\$[\d,]+\) A connected Depot' } | Select-Object -First 1
  if ($line -and $line -match '^(\d+),(\d+) ') {
    Write-Host "  depot: $line"
    & "$root\msgclick.ps1" "hc $($d.X + 34) $($d.Y + [int]$Matches[2] + 10)" | Out-Null; Start-Sleep -Milliseconds 500
    if ((Needs) -lt $before) { return $true }
  }
  if (Get-Dialog) { & "$root\msgclick.ps1" "hc $($d.X + 46) $($d.Y + $d.H - 17)" | Out-Null; Start-Sleep -Milliseconds 500 }      # Cancel (never SC_CLOSE: that crashes the game)
  return $false
}
function Engineer-Order($sel) {
  $before = Needs
  # First priority: an unconnected depot gathers nothing, so lay the next missing piece of rail towards the network ($100, one turn per piece).
  $r = (& $py -I "$re\tools\maptarget.py" rail)
  if ($r -match '^(lay|move) (\d+) (\d+)$') {
    Click-Game "$($Matches[2]) $($Matches[3])"; Start-Sleep -Milliseconds 400
    if ((Needs) -lt $before) { Write-Host "  engineer $r"; return }
  }
  $t = (& $py -I "$re\tools\maptarget.py" engineer)
  if ($t -eq 'here') { if (Build-Depot $sel) { return } }
  elseif ($t -match '^\d+ \d+ (\d+) (\d+)$') {
    Click-Game "$($Matches[1]) $($Matches[2])"; Start-Sleep -Milliseconds 400     # redeploy (one turn); next turn he is idle on the tile and 'here' fires
    Clear-Popups; if ((Needs) -lt $before) { Write-Host "  engineer deploys to $t"; return }
  }
  Write-Host "  engineer: nothing to build, sleeping"; Sleep-Unit
}
function Order-Unit($sel) {
  if ($sel -match "'type': 4,") { Engineer-Order $sel; return }
  $kind = if ($sel -match "'type': 1,") { 'prospect' } elseif ($sel -match "'type': 2,") { 'farmer' } elseif ($sel -match "'type': 0,") { 'miner' } else { $null }
  if (-not $kind) { Sleep-Unit; return }
  $before = Needs
  # Try the screen as Next Unit left it (the unit is centred). A Prospector with nothing there scrolls with the toolbar "Search In" tiles; after a scroll no unit is
  # centred, so targets come from the visible-window origin and two row guesses (a wrong guess clicks another tile or nothing, which is harmless).
  $plans = @(@{ loc = $null; args = @($kind) })
  if ($kind -eq 'prospect') { foreach ($l in @('539 335', '539 315', '539 335')) { $plans += @{ loc = $l; args = @('prospect', '0') }; $plans += @{ loc = $null; args = @('prospect', '1') } } }
  foreach ($p in $plans) {
    if ($p.loc) { Click-Game $p.loc; Start-Sleep -Milliseconds 500 }
    $t = (& $py -I "$re\tools\maptarget.py" @($p.args))
    if ($t -match '^\d+ \d+ (\d+) (\d+)$') {
      Click-Game "$($Matches[1]) $($Matches[2])"; Start-Sleep -Milliseconds 400
      if ((Needs) -lt $before) { Write-Host "  $kind tile $t (plan $($p.loc) $($p.args -join ' '))"; return }
    }
  }
  Write-Host "  no $kind target found, sleeping"; Sleep-Unit
}
for ($t = 1; $t -le $Turns; $t++) {
  Clear-Popups; Post-Key 0x57; Start-Sleep -Milliseconds 500
  $n = Needs; $guard = 0
  while ($n -gt 0 -and $guard -lt 15) {
    $m = Text-Mark; Click-Game '563 166'; Start-Sleep -Milliseconds 500      # Next Unit selects one that needs orders
    # The cycle also offers garrisons and fleets (the toolbar then shows "Force Size: N"); memory's selected-civilian slot still names the OLD civilian then, so every
    # click would go to the wrong unit. Send them to sleep (until the next 'w') and look again.
    if (((Text-Since $m) -join "`n") -match 'Force Size|Fleet') { Write-Host "turn $t : military unit in the cycle: sleep"; Click-Game '621 166'; $guard++; continue }
    $s = Selected; Write-Host "turn $t : order $s"
    Order-Unit $s; Start-Sleep -Milliseconds 700
    $n2 = Needs; if ($n2 -ge $n) { $guard += 3 }; $n = $n2; $guard++
  }
  if ($n -gt 0) { Write-Host "turn $t : $n units still need orders (gave up)" }
  $m = Text-Mark; & "$root\prod_endturn.ps1" | Select-Object -Last 3; Clear-Popups $m
  Write-Host "turn $t done"
}
