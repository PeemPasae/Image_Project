# =====================================================================
#  demo-tunnel.ps1 - open LUMA to outside the LAN "temporarily" for a demo
#
#  Uses Cloudflare quick tunnel pointing at nginx :80 -> gives a
#  https://xxx.trycloudflare.com URL. Close the demo: press Ctrl+C in this
#  window -> the URL dies instantly (nothing stays exposed).
#
#  Requires (the script checks): nginx on :80, backend running, SD WebUI running.
#
#    powershell -ExecutionPolicy Bypass -File nginx\scripts\demo-tunnel.ps1
#
#  หมายเหตุ (ไทย): สคริปต์นี้เปิดเว็บให้รุ่นน้องเข้าจากนอกวง LAN ชั่วคราว
#  ชี้เข้า nginx พอร์ต 80 อย่างเดียว ไม่แตะพอร์ตหลังบ้าน (8089/5000/8088)
# =====================================================================
$ErrorActionPreference = "Stop"
$cf = "C:\nginx\cloudflared.exe"

if (-not (Test-Path $cf)) {
    Write-Host "cloudflared not found at $cf" -ForegroundColor Red
    Write-Host "Download: https://github.com/cloudflare/cloudflared/releases/latest"
    exit 1
}

# nginx :80 must be up
$ok = Test-NetConnection 127.0.0.1 -Port 80 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $ok) {
    Write-Host "nginx :80 is not running - go to C:\nginx and run .\nginx.exe first" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host " Opening tunnel... the URL appears below (the trycloudflare.com line)" -ForegroundColor Cyan
Write-Host " Share that URL - juniors can open it on any phone/PC, any network." -ForegroundColor Cyan
Write-Host " When done: press Ctrl+C in this window to close the tunnel." -ForegroundColor Yellow
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# --url http://localhost:80 = front door (nginx) only; never :8089/:5000/:8088
& $cf tunnel --url http://localhost:80
