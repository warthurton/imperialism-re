# Run a chain of UI actions in one go (one focus check per click, waits end when the screen settles).
# usage: prod_do.ps1 "city; m 1000 400; w 0.3; refinery; dplus 2; dclose; back"
#   c X Y        click (mirror coords) and wait for the screen to settle        m X Y   move the mouse (no wait)
#   s NAME       screenshot to shots\NAME.png                                    w SEC   fixed wait
#   cs X Y NAME  click, settle, screenshot (shorthand)
# Screens by hot key:  go transport|industry|trade|diplomacy|tech|map [shotname]   (map = back arrow)
# Named screens:  city = factory icon on the map (1133,295)   back = leave the screen (closes an open dialog first)
#   plant = Power Plant site (1080,470)   refinery = Refinery site (930,420)   endturn = run prod_endturn.ps1
#   (a site click waits until its dialog is on screen)
# Dialog steps use the dialog's real position, read from its window (fast.ps1 Get-Dialog), so they work wherever it opened:
#   dlg            print the open dialog (position, size, kind)         dwait [gone]   wait for a dialog to appear (or vanish)
#   dplus [N]      slider arrow right N times (production dialogs)       dminus [N]     slider arrow left
#   dend / dstart  drag the slider knob to its far end / back to the start
#   dexpand        the expand-capacity button of a production dialog
#   dclose         X button of a production dialog                       dok / dcancel  OK / Cancel of a construction dialog
param([Parameter(Mandatory = $true)][string]$Steps)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"; . "$root\fast.ps1"
$named = @{ city = @(1133, 295); plant = @(1080, 470); refinery = @(930, 420); mapend = @(1160, 955) }
$sites = 'plant', 'refinery'
function Close-Dialog { $d = Get-Dialog; if ($d) { if ($d.Kind -eq 'construct') { Dialog-Click 'cancel' } else { Dialog-Click 'close' }; Wait-Dialog $false | Out-Null } }
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
    'go' {    # hot keys 1-5 (manual: Hot Key List); 'map' = leave the screen with the back arrow
      $keys = @{ transport = 0x31; industry = 0x32; trade = 0x33; diplomacy = 0x34; tech = 0x35 }
      if ($t[1] -eq 'map') { Close-Dialog; Click-Wait 57 135 }
      elseif ($keys.ContainsKey($t[1])) { Close-Dialog; Post-Key $keys[$t[1]]; Wait-Stable -Max 5 -Before '' }
      else { throw "unknown screen '$($t[1])' (transport industry trade diplomacy tech map)" }
      if ($t.Count -gt 2) { Snap $t[2] }
    }
    'back'  { Close-Dialog; Click-Wait 57 135 }
    'dlg'   { $d = Get-Dialog; if ($d) { "dialog $($d.Kind) at ($($d.X),$($d.Y)) $($d.W)x$($d.H)" } else { 'no dialog' } }
    'dwait' { $ok = Wait-Dialog ($t.Count -lt 2); if (-not $ok) { "dwait: timed out" } }
    'dplus' { 1..$(if ($t.Count -gt 1) { [int]$t[1] } else { 1 }) | ForEach-Object { Dialog-Click 'plus' } }
    'dminus' { 1..$(if ($t.Count -gt 1) { [int]$t[1] } else { 1 }) | ForEach-Object { Dialog-Click 'minus' } }
    'dexpand' { Dialog-Click 'expand' }
    'dend'   { Dialog-Drag 'knob' 'end' }
    'dstart' { Dialog-Drag 'end' 'knob' }
    'dclose' { Dialog-Click 'close'; Wait-Dialog $false | Out-Null }
    'dok'    { Dialog-Click 'ok'; Wait-Dialog $false | Out-Null }
    'dcancel' { Dialog-Click 'cancel'; Wait-Dialog $false | Out-Null }
    default {
      if ($named.ContainsKey($t[0])) {
        Click-Wait $named[$t[0]][0] $named[$t[0]][1]
        if ($sites -contains $t[0] -and -not (Wait-Dialog)) { "warning: no dialog appeared after '$($t[0])'" }
        if ($t.Count -gt 1) { Snap $t[1] }
      }
      else { throw "unknown step '$($t[0])'" }
    }
  }
}
