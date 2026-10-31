# Capture and validate one fixture turn in one process lifetime; always restore settings.
param([string]$Fixture = 'oil_plant_built', [string]$Name = 'snapshot_live',
      [ValidateRange(0,30)][int]$WarmupTurns = 0, [switch]$TracePlanning,
      [string]$SaveFixture = '')
$ErrorActionPreference = 'Stop'
$repository = Split-Path $PSScriptRoot
if ($Name -notmatch '^snapshot_[A-Za-z0-9_-]+$') { throw 'Name must start with snapshot_ and contain only letters, digits, underscores or hyphens' }
$prefix = Join-Path $repository "results\$Name"
if ($SaveFixture) {
    if ($SaveFixture -notmatch '^[A-Za-z0-9_-]{1,31}$') { throw 'SaveFixture must be a simple name, at most 31 characters' }
    if (Test-Path (Join-Path $repository "saves\$SaveFixture.imp")) { throw 'SaveFixture already exists' }
}
foreach ($suffix in @('_before.json', '_idle.json', '_after.json')) {
    if (Test-Path "$prefix$suffix") { throw "output exists: $prefix$suffix" }
}
function Run-Python([string[]]$Arguments) {
    & python -I @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python failed ($LASTEXITCODE): $Arguments" }
}
try {
    Push-Location $repository
    & "$PSScriptRoot\prod_boot.ps1" -Fixture $Fixture -Restart
    for ($turn = 0; $turn -lt $WarmupTurns; $turn++) {
        "warmup turn $($turn + 1)/$WarmupTurns"
        & "$PSScriptRoot\prod_endturn.ps1"
    }
    $processes = @(Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited })
    if ($processes.Count -ne 1) { throw "expected one live game after boot; found $($processes.Count)" }
    $gamePid = $processes[0].Id
    Run-Python @('tools/snapshot.py', "${prefix}_before.json", '--pid', "$gamePid")
    Run-Python @('tools/readcity.py', "${Name}_before")
    Run-Python @('tools/readtech.py', "${Name}_before")
    Run-Python @('tools/readdiplo.py', "${Name}_before")
    Run-Python @('tools/snapshot.py', "${prefix}_idle.json", '--pid', "$gamePid")
    if ($TracePlanning) {
        & "$PSScriptRoot\trace_city_planning.ps1" -Name "trace_$Name"
    } else {
        & "$PSScriptRoot\prod_endturn.ps1" -Log
    }
    Run-Python @('tools/snapshot.py', "${prefix}_after.json", '--pid', "$gamePid")
    Run-Python @('tools/readcity.py', "${Name}_after")
    Run-Python @('tools/readtech.py', "${Name}_after")
    Run-Python @('tools/readdiplo.py', "${Name}_after")
    Run-Python @('tools/validate_snapshot.py', $prefix)
    if ($SaveFixture) {
        & "$PSScriptRoot\prod_save.ps1" $SaveFixture $SaveFixture
    }
}
finally {
    & "$PSScriptRoot\prod_end.ps1"
    Pop-Location
}
