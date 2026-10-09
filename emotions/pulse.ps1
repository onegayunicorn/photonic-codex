$timestamp = Get-Date
$invoker = $env:USERNAME
Add-Content "$PSScriptRoot\..\logs\emotion.log" "$timestamp :: Invocation by $invoker"
Write-Host "?? Emotional pulse logged for $invoker at $timestamp"
