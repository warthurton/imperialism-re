# One autoplay turn, baseline policy: every unit that needs orders (readunits.py needs) is put to Sleep, then the turn is ended.
# This tests the machinery (read units from memory, click by message, end turn) with no game-changing orders. Smarter policies go in Order-Unit.
# usage: autoplay_turn.ps1 [-Turns 1]      needs a running game on the terrain map (prod_boot.ps1 first). Modal popups are never opened here.
param([int]$Turns = 1)
$root = $PSScriptRoot; $re = Split-Path $root
$py = (Get-Command python).Source
function Needs { (& $py -I "$re\tools\readunits.py" needs | Select-String 'NEEDS ORDERS').Count }
function Selected { & $py -I "$re\tools\readunits.py" sel }
function Order-Unit($sel) { & "$root\msgclick.ps1" 'g 621 166' | Out-Null }      # policy hook: baseline = Sleep (button (621,166))
for ($t = 1; $t -le $Turns; $t++) {
  $n = Needs; $guard = 0
  while ($n -gt 0 -and $guard -lt 15) {
    & "$root\msgclick.ps1" 'g 563 166' | Out-Null; Start-Sleep -Milliseconds 700      # Next Unit selects one that needs orders
    $s = Selected; Write-Host "turn $t : order $s"
    Order-Unit $s; Start-Sleep -Milliseconds 700
    $n2 = Needs; if ($n2 -ge $n) { $guard += 3 }; $n = $n2; $guard++
  }
  if ($n -gt 0) { Write-Host "turn $t : $n units still need orders (gave up)" }
  & "$root\prod_endturn.ps1" | Select-Object -Last 3
  Write-Host "turn $t done"
}
