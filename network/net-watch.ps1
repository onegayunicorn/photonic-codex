Write-Host 'Network AI: Monitoring TP-Link_EC1D_5G 2...'
Get-NetAdapter | Where-Object {\.Name -eq 'Wi-Fi'} | Format-List
