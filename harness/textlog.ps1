# Dot-source this file. Switches the shim's text log (imperialism_shim.ini [text_log] enabled=) on for a test and puts the user's value back afterwards.
#   Set-TextLog -On   remembers the user's original value once (results\textlog.orig: 0, 1 or 'absent') and writes enabled=1  (prod_boot.ps1 calls this before launching)
#   Restore-TextLog   writes the remembered value back (prod_end.ps1 calls this)
# The shim reads the ini at launch, so Set-TextLog must run before the game starts.
$script:TL_INI = 'C:\GOG Games\Imperialism\imperialism_shim.ini'
$script:TL_ORIG = Join-Path (Split-Path $PSScriptRoot) 'results\textlog.orig'

function Get-TextLogValue {
  if (-not (Test-Path $script:TL_INI)) { return 'absent' }
  $in = $false
  foreach ($l in Get-Content $script:TL_INI) {
    if ($l -match '^\s*\[(.+)\]\s*$') { $in = ($Matches[1] -eq 'text_log'); continue }
    if ($in -and $l -match '^\s*enabled\s*=\s*(\d+)') { return $Matches[1] }
  }
  return 'absent'
}

function Write-TextLogValue([string]$value) {
  $lines = if (Test-Path $script:TL_INI) { @(Get-Content $script:TL_INI) } else { @() }
  $out = New-Object System.Collections.Generic.List[string]; $in = $false; $done = $false; $sawSection = $false
  foreach ($l in $lines) {
    if ($l -match '^\s*\[(.+)\]\s*$') {
      if ($in -and -not $done) { $out.Add("enabled=$value"); $done = $true }   # section had no enabled= line
      $in = ($Matches[1] -eq 'text_log'); if ($in) { $sawSection = $true }
    }
    elseif ($in -and $l -match '^\s*enabled\s*=') { $out.Add("enabled=$value"); $done = $true; continue }
    $out.Add($l)
  }
  if ($in -and -not $done) { $out.Add("enabled=$value"); $done = $true }
  if (-not $sawSection) { $out.Add('[text_log]'); $out.Add("enabled=$value") }
  Set-Content -Path $script:TL_INI -Value $out
}

function Set-TextLog([switch]$On) {
  # remember the user's value, unless an earlier run of ours already switched it on (then the saved value is still the user's)
  $cur = Get-TextLogValue
  if (-not (Test-Path $script:TL_ORIG) -or $cur -ne '1') { New-Item -ItemType Directory -Force (Split-Path $script:TL_ORIG) | Out-Null; Set-Content -Path $script:TL_ORIG -Value $cur }
  Write-TextLogValue '1'
}

function Restore-TextLog {
  if (-not (Test-Path $script:TL_ORIG)) { return }
  $orig = (Get-Content $script:TL_ORIG | Select-Object -First 1).Trim()
  if ($orig -eq '0' -or $orig -eq '1') { Write-TextLogValue $orig } elseif ($orig -eq 'absent') { Write-TextLogValue '0' }
  # the file stays (Remove-Item on C:\GOG paths can be blocked); Set-TextLog re-reads the user's value whenever the ini is not currently ours (enabled=1)
}
