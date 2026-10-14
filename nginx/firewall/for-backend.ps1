# =====================================================================
#  for-backend.ps1 — รันบน "เครื่อง Backend" (ตอนนี้ 172.20.10.8) แบบ Run as Administrator
#
#  ผล:
#    - พอร์ต 5000 (Flask) → รับจากเครื่อง nginx เท่านั้น
#    - พอร์ต 5173 (Vite dev) → ปิด
#  ต้องตั้ง HOST=0.0.0.0 ใน backend/.env (ถ้า 127.0.0.1 เครื่อง nginx จะต่อไม่ติด)
#
#  IP ของเครื่อง nginx ใส่ไว้ที่ $NginxIp ข้างล่าง (หรือส่งเข้ามา: -NginxIp x.x.x.x)
#  ถอนออก:  Get-NetFirewallRule -DisplayName "LUMA *" | Remove-NetFirewallRule
# =====================================================================
#Requires -RunAsAdministrator
param(
    [string]$NginxIp = "172.20.10.6"
)

$ErrorActionPreference = "Stop"

Get-NetFirewallRule -DisplayName "LUMA *" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

New-NetFirewallRule -DisplayName "LUMA allow Flask 5000 from nginx" -Direction Inbound -Protocol TCP -LocalPort 5000 `
    -RemoteAddress $NginxIp -Action Allow -Profile Any | Out-Null
$o = $NginxIp.Split('.')
$before = "{0}.{1}.{2}.{3}" -f $o[0], $o[1], $o[2], ([int]$o[3] - 1)
$after  = "{0}.{1}.{2}.{3}" -f $o[0], $o[1], $o[2], ([int]$o[3] + 1)
New-NetFirewallRule -DisplayName "LUMA block Flask 5000 others (low)" -Direction Inbound -Protocol TCP -LocalPort 5000 `
    -RemoteAddress "0.0.0.1-$before" -Action Block -Profile Any | Out-Null
New-NetFirewallRule -DisplayName "LUMA block Flask 5000 others (high)" -Direction Inbound -Protocol TCP -LocalPort 5000 `
    -RemoteAddress "$after-255.255.255.254" -Action Block -Profile Any | Out-Null
New-NetFirewallRule -DisplayName "LUMA block Vite 5173 from LAN" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Block -Profile Any | Out-Null

Write-Host "`nกฎ firewall ของ LUMA (เครื่อง Backend) — 5000 รับจาก $NginxIp เท่านั้น:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "LUMA *" |
    Select-Object DisplayName, Direction, Action, Enabled |
    Format-Table -AutoSize
