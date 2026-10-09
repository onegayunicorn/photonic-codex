Write-Host 'Epic AI: Monitoring system integrity...'
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
