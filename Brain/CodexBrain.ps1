$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$cpuLoad = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
$ram = Get-CimInstance Win32_OperatingSystem
$usedRAM = ($ram.TotalVisibleMemorySize - $ram.FreePhysicalMemory) / 1MB
$feedbackPath = 'C:\CodexO\Brain\Feedback\feedback.txt'
Add-Content -Path 'C:\CodexO\Brain\Logs\brain_log.txt' -Value "[$timestamp] CPU: $cpuLoad%, RAM: $([math]::Round($usedRAM,2)) MB"
if (Test-Path $feedbackPath) {
    $feedback = Get-Content $feedbackPath
    Add-Content -Path 'C:\CodexO\Brain\Logs\brain_log.txt' -Value "[$timestamp] Feedback received: $feedback"
    Add-Content -Path 'C:\CodexO\Brain\Models\adaptive_model.txt' -Value "[$timestamp] Adapted to feedback: $feedback"
}
