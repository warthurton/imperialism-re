# End of testing: stop the game and put the user's settings back: effects 100%, music 75%, briefings and warnings On.
# Stop only the game this harness started (pid written by prod_boot.ps1 to results\game.pid), so a game the user runs themselves is never killed.
# Pass -All to stop every Imperialism process (only when the user has said to).
param([switch]$All)
$pidFile = Join-Path (Split-Path $PSScriptRoot) 'results\game.pid'
$ours = if (Test-Path $pidFile) { [int](Get-Content $pidFile) } else { 0 }
Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited -and ($All -or $_.Id -eq $ours) } | Stop-Process -Force
if (Test-Path $pidFile) { Set-Content -Path $pidFile -Value 0 }      # (Remove-Item on C:\GOG paths is blocked; 0 = no game of ours)
$left = @(Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited })
if ($left.Count) { "note: $($left.Count) other Imperialism process(es) still running (not started by this harness): $($left.Id -join ', ')" }
Start-Sleep -Seconds 2
$k = 'HKCU:\Software\SSI\Imperialism\Settings'
Set-ItemProperty -Path $k -Name Pref2 -Value 100 -Type DWord      # effects 100%
Set-ItemProperty -Path $k -Name Pref3 -Value 191 -Type DWord      # music 75% (191/255)
Set-ItemProperty -Path $k -Name Pref8 -Value 1 -Type DWord        # warnings On (the user's setting)
Set-ItemProperty -Path $k -Name Pref10 -Value 1 -Type DWord       # briefings On (the user's setting)
"game stopped; effects 100%, music 75%, warnings and briefings On"
