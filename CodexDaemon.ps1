$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "C:\CodexO\Scrolls\daemon_log.txt" -Value "[$timestamp] CodexO Daemon pulsing."
Start-Sleep -Seconds 5
Add-Content -Path "C:\CodexO\Scrolls\daemon_log.txt" -Value "[$timestamp] CodexO Daemon completed cycle."
