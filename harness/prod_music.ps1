# Check that the game is actually making music: sample the game's audio peak for ~4 s. Prints MUSIC OK / MUSIC SILENT.
# (-1 = no audio session at all, 0 = silent session.) Quiet test volumes give small peaks; anything above 0.0003 counts.
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\audio.ps1"
$g = Get-Process Imperialism -ErrorAction Stop
$max = -1; 1..8 | ForEach-Object { Start-Sleep -Milliseconds 500; $p = [AudioPeek]::Peak($g.Id); if ($p -gt $max) { $max = $p } }
$k = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
$layer = (Get-ItemProperty $k -ErrorAction SilentlyContinue).'C:\GOG Games\Imperialism\Imperialism.exe'
if ($max -gt 0.0003) { "MUSIC OK (peak $([math]::Round($max,4)))" } else { "MUSIC SILENT (peak $max). Compat layer for the exe: '$layer' -- IgnoreFreeLibrary makes Windows load the system winmm instead of the music player" }
