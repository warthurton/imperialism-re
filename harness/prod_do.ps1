# Run a chain of UI actions in one go (one focus check per click, waits end when the screen settles).
# usage: prod_do.ps1 "c 1133 295; c 1080 470; s power_dialog"
#   c X Y        click (mirror coords) and wait for the screen to settle        m X Y   move the mouse (no wait)
#   s NAME       screenshot to shots\NAME.png                                    w SEC   fixed wait
#   cs X Y NAME  click, settle, screenshot (shorthand)
# Named screens (shorthand for common clicks):  city = factory icon on the map (1133,295)   back = back arrow (57,135)
#   plant = Power Plant site on the capital screen (1080,470)   refinery = (930,420)   endturn = run prod_endturn.ps1
param([Parameter(Mandatory = $true)][string]$Steps)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
$named = @{ city = @(1133, 295); back = @(57, 135); plant = @(1080, 470); refinery = @(930, 420); ok = @(853, 760); mapend = @(1160, 955) }
foreach ($raw in $Steps.Split(';')) {
  $t = $raw.Trim().Split(' ', [StringSplitOptions]::RemoveEmptyEntries)
  if (-not $t) { continue }
  switch ($t[0]) {
    'c'  { Click-Wait ([double]$t[1]) ([double]$t[2]) }
    'cs' { Click-Wait ([double]$t[1]) ([double]$t[2]); Snap $t[3] }
    'm'  { Ensure-Focus; $p = Mirror-Px ([double]$t[1]) ([double]$t[2]); [GW]::SetCursorPos($p[0], $p[1]) | Out-Null }
    's'  { Snap $t[1] }
    'w'  { Start-Sleep -Milliseconds ([int]([double]$t[1] * 1000)) }
    'endturn' { & "$root\prod_endturn.ps1" }
    default {
      if ($named.ContainsKey($t[0])) { Click-Wait $named[$t[0]][0] $named[$t[0]][1]; if ($t.Count -gt 1) { Snap $t[1] } }
      else { throw "unknown step '$($t[0])'" }
    }
  }
}
