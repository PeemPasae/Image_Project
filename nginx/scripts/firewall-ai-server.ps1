# =====================================================================
#  firewall-ai-server.ps1 — รันบน "เครื่อง AI Server" (172.20.56.221) แบบ Run as Administrator
#
#  ผล: พอร์ต 8088 (SD WebUI --listen) รับได้จาก "เครื่อง Backend/nginx" เท่านั้น
#      → คนอื่นในวง LAN เปิด http://172.20.56.221:8088 ไม่ได้อีกต่อไป
#      → ทีม DEV เข้า WebUI ผ่าน http://<backend-ip>:8089 (nginx คัด IP + รหัสผ่าน)
#
#  เปลี่ยน IP ของเครื่อง Backend ที่ $BackendIp ให้ตรงก่อนรัน
#  ถอนออก:  Get-NetFirewallRule -DisplayName "LUMA *" | Remove-NetFirewallRule
# =====================================================================
#Requires -RunAsAdministrator
param(
    [string]$BackendIp = "172.20.56.158"
)

$ErrorActionPreference = "Stop"

Get-NetFirewallRule -DisplayName "LUMA *" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

# 1) allow เฉพาะ backend
New-NetFirewallRule -DisplayName "LUMA allow SD 8088 from backend" -Direction Inbound -Protocol TCP -LocalPort 8088 `
    -RemoteAddress $BackendIp -Action Allow -Profile Any | Out-Null

# 2) block ที่เหลือ — Block ชนะ Allow ดังนั้นต้องยกเว้น backend ออกจากกฎ block
#    (Windows ไม่มี "block all except" ตรง ๆ → ใช้ RemoteAddress เป็นช่วง แล้วเว้น backend ไว้)
$octets = $BackendIp.Split('.')
$before = "{0}.{1}.{2}.{3}" -f $octets[0], $octets[1], $octets[2], ([int]$octets[3] - 1)
$after  = "{0}.{1}.{2}.{3}" -f $octets[0], $octets[1], $octets[2], ([int]$octets[3] + 1)
New-NetFirewallRule -DisplayName "LUMA block SD 8088 others (low)"  -Direction Inbound -Protocol TCP -LocalPort 8088 `
    -RemoteAddress "0.0.0.1-$before" -Action Block -Profile Any | Out-Null
New-NetFirewallRule -DisplayName "LUMA block SD 8088 others (high)" -Direction Inbound -Protocol TCP -LocalPort 8088 `
    -RemoteAddress "$after-255.255.255.254" -Action Block -Profile Any | Out-Null

Write-Host "`nพอร์ต 8088 รับได้จาก $BackendIp เท่านั้น:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "LUMA *" |
    Select-Object DisplayName, Direction, Action, Enabled |
    Format-Table -AutoSize
