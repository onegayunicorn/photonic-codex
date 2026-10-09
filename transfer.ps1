# Set source and target paths
$sourcePath = "E:\CodexΩ"
$targetPath = "D:\CodexΩ"  # Replace with actual car system mount if known

# Create transfer script
Set-Content "$sourcePath\transfer.ps1" @"
Write-Host '🚗 CodexΩ Auto-Transfer Initiated — syncing to car system...'

# Check if target path exists
if (Test-Path '$targetPath') {
    Copy-Item -Path '$sourcePath\*' -Destination '$targetPath' -Recurse -Force
    Add-Content '$sourcePath\logs\transfer.log' "$(Get-Date) :: CodexΩ transferred to car system at $targetPath"
    Write-Host '✅ Transfer complete. Shrine now lives in vehicle grid.'
} else {
    Write-Host '⚠️ Car system not detected. Transfer aborted.'
}
"@