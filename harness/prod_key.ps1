# usage: prod_key.ps1 <name|vk> [shotname] [wait]   -- send one key to the game (focus is ensured first) and screenshot.
# names: esc enter space f1..f7 1..5 w a n x p d  (readme hot keys: 1-5 screens, Esc = reject/map/game options, Enter = accept)
param([string]$key, [string]$name = 'key', [int]$wait = 2)
$root = $PSScriptRoot
. "$root\gw.ps1"; . "$root\focus.ps1"
$map = @{ esc = 0x1B; enter = 0x0D; space = 0x20; f1 = 0x70; f2 = 0x71; f3 = 0x72; f4 = 0x73; f5 = 0x74; f6 = 0x75; f7 = 0x76 }
Ensure-Focus
if ($map.ContainsKey($key.ToLower())) { $vk = $map[$key.ToLower()] } else { $vk = [byte][char]$key.ToUpper() }
[GW]::Key([byte]$vk); Start-Sleep -Seconds $wait
[GW]::Shot((Mirror), "$root\shots\$name.png"); "key $key sent"
