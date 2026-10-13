# =====================================================================
#  for-nginx.ps1 — รันบน "เครื่อง nginx" (ตอนนี้ 192.168.1.171) แบบ Run as Administrator
#
#  ผล:
#    - เปิดพอร์ต 80   ให้ทุกคนในวง LAN   (หน้าเว็บ + API ผ่าน nginx)
#    - เปิดพอร์ต 8089 ให้ทุกคน แต่ nginx เป็นคนคัด IP เอง (conf/dev_allowlist.conf + รหัสผ่าน)
#    - ปิดพอร์ต 5000 / 5173 / 8088 ของเครื่องนี้ (กันเผลอรัน Flask / Vite / SD เปิดออก LAN)
#
#  ใช้เมื่อ: เครื่องอื่นเปิด http://<IP เครื่องนี้>/ ไม่ได้ ทั้งที่ http://localhost/ เปิดได้
#  ถอนออก:  Get-NetFirewallRule -DisplayName "LUMA *" | Remove-NetFirewallRule
# =====================================================================
#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# ล้างกฎเดิมของ LUMA ก่อน (รันซ้ำได้)
Get-NetFirewallRule -DisplayName "LUMA *" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

New-NetFirewallRule -DisplayName "LUMA allow nginx 80"  -Direction Inbound -Protocol TCP -LocalPort 80   -Action Allow -Profile Any | Out-Null
New-NetFirewallRule -DisplayName "LUMA allow nginx dev 8089" -Direction Inbound -Protocol TCP -LocalPort 8089 -Action Allow -Profile Any | Out-Null

# Block ชนะ Allow เสมอใน Windows Firewall → ต่อให้ Python มีกฎ allow อยู่ก็เข้าไม่ได้
New-NetFirewallRule -DisplayName "LUMA block Flask 5000 from LAN" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Block -Profile Any | Out-Null
New-NetFirewallRule -DisplayName "LUMA block Vite 5173 from LAN"  -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Block -Profile Any | Out-Null
# SD WebUI รันเครื่องเดียวกัน (--listen เปิด 0.0.0.0:8088) → ปิดจาก LAN, DEV เข้าผ่าน nginx :8089 แทน
New-NetFirewallRule -DisplayName "LUMA block SD WebUI 8088 from LAN" -Direction Inbound -Protocol TCP -LocalPort 8088 -Action Block -Profile Any | Out-Null

Write-Host "`nกฎ firewall ของ LUMA ตอนนี้:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "LUMA *" |
    Select-Object DisplayName, Direction, Action, Enabled |
    Format-Table -AutoSize
