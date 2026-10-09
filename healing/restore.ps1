$agents = @("epic-ai.ps1","mythic-ai.ps1","omni-ai.ps1")
foreach ($agent in $agents) {
    $path = "$PSScriptRoot\..\epic\$agent"
    if (-not (Test-Path $path)) {
        Write-Host "?? Restoring missing agent: $agent"
        New-Item -ItemType File -Path $path -Force
    }
}
Write-Host "? Healing protocol complete."
