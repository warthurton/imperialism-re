# Start the idle-dock watcher hidden (it exits by itself when the game does, and only one instance can run).
$args2 = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSScriptRoot + '\idle_dock.ps1"'
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList $args2
