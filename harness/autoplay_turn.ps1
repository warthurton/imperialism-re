# Autoplay turns. Policy: Prospectors search the nearest visibly unprospected hill/mountain, Farmers and Miners improve a tile (one click, order 10),
# everything else sleeps. Every turn starts with 'w' (rouse sleepers) so units are offered again. Then the turn is ended.
# Reads units from memory (readunits.py needs/sel), picks tiles with maptarget.py (player-visible data only), clicks by window message.
# usage: autoplay_turn.ps1 [-Turns 1]      needs a running game on the terrain map (prod_boot.ps1 first). Modal popups are never opened here.
param([int]$Turns = 1)
$root = $PSScriptRoot; $re = Split-Path $root
. "$root\gw.ps1"; . "$root\fast.ps1"
$py = (Get-Command python).Source
function Needs { (& $py -I "$re\tools\readunits.py" needs | Select-String 'NEEDS ORDERS').Count }
function Selected { & $py -I "$re\tools\readunits.py" sel }
# Advice popups (Interior Minister etc., 390x282 modal) open after a turn even with briefings off and block every message click: dismiss with the mirror click on OK.
function Clear-Popups { for ($i = 0; $i -lt 4; $i++) { $d = Get-Dialog; if ($d -and $d.W -eq 390 -and $d.H -eq 282) { Write-Host '  advice popup: OK'; Click-Wait 820 760 } else { break } } }
function Sleep-Unit { & "$root\msgclick.ps1" 'g 621 166' | Out-Null }               # Sleep button (621,166)
# After an accepted order the game selects the next unit by itself, so success = fewer units needing orders.
# A Prospector with nothing eligible on screen clicks the toolbar "Search In" tiles (hills (539,315), mountains (539,335)) to scroll, up to 4 tries.
function Order-Unit($sel) {
  $kind = if ($sel -match "'type': 1,") { 'prospect' } elseif ($sel -match "'type': 2,") { 'farmer' } elseif ($sel -match "'type': 0,") { 'miner' } else { $null }
  if (-not $kind) { Sleep-Unit; return }
  $before = Needs
  $loc = @('539 335', '539 315', '539 335', '539 315')
  for ($k = 0; $k -le 4; $k++) {
    $t = (& $py -I "$re\tools\maptarget.py" $kind)
    if ($t -match '^\d+ \d+ (\d+) (\d+)$') {
      & "$root\msgclick.ps1" "g $($Matches[1]) $($Matches[2])" | Out-Null; Start-Sleep -Milliseconds 800
      if ((Needs) -lt $before) { Write-Host "  $kind tile $t"; return }
    }
    if ($kind -ne 'prospect') { break }
    if ($k -lt 4) { & "$root\msgclick.ps1" "g $($loc[$k])" | Out-Null; Start-Sleep -Milliseconds 800 }
  }
  Write-Host "  no $kind target found, sleeping"; Sleep-Unit
}
for ($t = 1; $t -le $Turns; $t++) {
  Clear-Popups; Post-Key 0x57; Start-Sleep -Milliseconds 500
  $n = Needs; $guard = 0
  while ($n -gt 0 -and $guard -lt 15) {
    Clear-Popups; & "$root\msgclick.ps1" 'g 563 166' | Out-Null; Start-Sleep -Milliseconds 700      # Next Unit selects one that needs orders
    $s = Selected; Write-Host "turn $t : order $s"
    Order-Unit $s; Start-Sleep -Milliseconds 700
    $n2 = Needs; if ($n2 -ge $n) { $guard += 3 }; $n = $n2; $guard++
  }
  if ($n -gt 0) { Write-Host "turn $t : $n units still need orders (gave up)" }
  Clear-Popups; & "$root\prod_endturn.ps1" | Select-Object -Last 3
  Write-Host "turn $t done"
}
