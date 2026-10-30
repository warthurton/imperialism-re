# End of testing: stop the game and put the user's settings back: effects 100%, music 75%, briefings and warnings On.
Get-Process Imperialism -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$k = 'HKCU:\Software\SSI\Imperialism\Settings'
Set-ItemProperty -Path $k -Name Pref2 -Value 100 -Type DWord      # effects 100%
Set-ItemProperty -Path $k -Name Pref3 -Value 191 -Type DWord      # music 75% (191/255)
Set-ItemProperty -Path $k -Name Pref8 -Value 1 -Type DWord        # warnings On (the user's setting)
Set-ItemProperty -Path $k -Name Pref10 -Value 1 -Type DWord       # briefings On (the user's setting)
"game stopped; effects 100%, music 75%, warnings and briefings On"
