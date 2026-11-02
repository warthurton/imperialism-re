# Dot-source this file. Switches shim switches in imperialism_shim.ini ([text_log] enabled=, [test_hook] enabled=) on for a test and puts the user's value back afterwards.
#   Set-TextLog -On   remembers the user's original value once (results\textlog.orig: 0, 1 or 'absent') and writes enabled=1  (prod_boot.ps1 calls this before launching)
#   Restore-TextLog   writes the remembered value back (prod_end.ps1 calls this)
#   Set-TestHook / Restore-TestHook   the same for [test_hook] (the shim's WM_TEST_CLICK, see compat/src/shim_internal.h); remembered in results\testhook.orig
# The shim reads the ini at launch, so the Set-* calls must run before the game starts.
$script:TL_INI = 'C:\GOG Games\Imperialism\imperialism_shim.ini'
$script:TL_ORIG = Join-Path (Split-Path $PSScriptRoot) 'results\textlog.orig'
$script:TH_ORIG = Join-Path (Split-Path $PSScriptRoot) 'results\testhook.orig'

function Get-IniFlag([string]$section) {
  if (-not (Test-Path $script:TL_INI)) { return 'absent' }
  $in = $false
  foreach ($l in Get-Content $script:TL_INI) {
    if ($l -match '^\s*\[(.+)\]\s*$') { $in = ($Matches[1] -eq $section); continue }
    if ($in -and $l -match '^\s*enabled\s*=\s*(\d+)') { return $Matches[1] }
  }
  return 'absent'
}

function Write-IniFlag([string]$section, [string]$value) {
  $lines = if (Test-Path $script:TL_INI) { @(Get-Content $script:TL_INI) } else { @() }
  $out = New-Object System.Collections.Generic.List[string]; $in = $false; $done = $false; $sawSection = $false
  foreach ($l in $lines) {
    if ($l -match '^\s*\[(.+)\]\s*$') {
      if ($in -and -not $done) { $out.Add("enabled=$value"); $done = $true }   # section had no enabled= line
      $in = ($Matches[1] -eq $section); if ($in) { $sawSection = $true }
    }
    elseif ($in -and $l -match '^\s*enabled\s*=') { $out.Add("enabled=$value"); $done = $true; continue }
    $out.Add($l)
  }
  if ($in -and -not $done) { $out.Add("enabled=$value"); $done = $true }
  if (-not $sawSection) { $out.Add("[$section]"); $out.Add("enabled=$value") }
  Set-Content -Path $script:TL_INI -Value $out
}

function Set-Flag([string]$section, [string]$origFile) {
  # remember the user's value, unless an earlier run of ours already switched it on (then the saved value is still the user's)
  $cur = Get-IniFlag $section
  if (-not (Test-Path $origFile) -or $cur -ne '1') { New-Item -ItemType Directory -Force (Split-Path $origFile) | Out-Null; Set-Content -Path $origFile -Value $cur }
  Write-IniFlag $section '1'
}

function Restore-Flag([string]$section, [string]$origFile) {
  if (-not (Test-Path $origFile)) { return }
  $orig = (Get-Content $origFile | Select-Object -First 1).Trim()
  if ($orig -eq '0' -or $orig -eq '1') { Write-IniFlag $section $orig } elseif ($orig -eq 'absent') { Write-IniFlag $section '0' }
  # the file stays (Remove-Item on C:\GOG paths can be blocked); Set-Flag re-reads the user's value whenever the ini is not currently ours (enabled=1)
}

function Set-TextLog([switch]$On) { Set-Flag 'text_log' $script:TL_ORIG }
function Restore-TextLog { Restore-Flag 'text_log' $script:TL_ORIG }
function Set-TestHook { Set-Flag 'test_hook' $script:TH_ORIG }
function Restore-TestHook { Restore-Flag 'test_hook' $script:TH_ORIG }
