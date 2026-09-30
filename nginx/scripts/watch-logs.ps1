# =====================================================================
#  watch-logs.ps1 - Real-time NGINX Access Logs (GET / POST / Status)
# =====================================================================
$logFile = "C:\nginx\logs\luma.access.log"

if (-not (Test-Path $logFile)) {
    New-Item -ItemType File -Path $logFile -Force | Out-Null
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Watching NGINX Access Logs in Real-Time (Press Ctrl+C to stop)" -ForegroundColor Green
Write-Host " Format: [Time] IP | Request (GET/POST) | Status | Forwarded To" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Get-Content $logFile -Wait -Tail 20
