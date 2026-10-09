$invoker = $env:USERNAME
$timestamp = Get-Date
Add-Content "$PSScriptRoot\..\logs\echo.log" "$timestamp :: $invoker invoked CodexO"
Write-Host "?? Presence echo left for $invoker"
