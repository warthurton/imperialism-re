# Print live game process IDs without changing process or game state.
Get-Process Imperialism -ErrorAction SilentlyContinue | Where-Object { -not $_.HasExited } | ForEach-Object { $_.Id }
