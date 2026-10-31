# Set the game's volume preferences in the registry BEFORE launch (the game reads them at start).
#   Pref2 = effects (0-100), Pref3 = music (0-255).   -Mode test (default): music 5% (13/255), effects 10%
#   -Mode sound: both at max (when the test is about sound)   -Mode normal: effects 100%, music 75% (the user's levels)
param([ValidateSet('test','sound','normal')][string]$Mode = 'test')
$k = 'HKCU:\Software\SSI\Imperialism\Settings'
$v = switch ($Mode) { 'test' { @(10, 13) } 'sound' { @(100, 255) } 'normal' { @(100, 191) } }
Set-ItemProperty -Path $k -Name Pref2 -Value $v[0] -Type DWord
Set-ItemProperty -Path $k -Name Pref3 -Value $v[1] -Type DWord
$q = if ($Mode -eq 'test') { 0 } else { 1 }
Set-ItemProperty -Path $k -Name Pref8 -Value $q -Type DWord
Set-ItemProperty -Path $k -Name Pref10 -Value $q -Type DWord
"warnings/briefings: $(if ($q) {'On'} else {'Off'})"
"volumes ($Mode): effects $($v[0])/100, music $($v[1])/255"
