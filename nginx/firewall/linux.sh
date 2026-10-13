#!/usr/bin/env bash
# =====================================================================
#  linux.sh — เวอร์ชัน ufw (Ubuntu) ของ for-nginx.ps1 / for-ai.ps1 (ใช้เมื่อเครื่องนั้นเป็น Linux)
#
#    sudo bash nginx/firewall/linux.sh backend            # เครื่อง nginx
#    sudo bash nginx/firewall/linux.sh ai 192.168.1.169    # เครื่อง AI Server (ระบุ IP backend)
# =====================================================================
set -euo pipefail

ROLE="${1:-}"
BACKEND_IP="${2:-192.168.1.169}"

case "$ROLE" in
  backend)
    ufw allow 22/tcp                       # กันล็อกตัวเองออกจาก ssh
    ufw allow 80/tcp                       # nginx สาธารณะ
    ufw allow 8089/tcp                     # nginx dev gateway (nginx คัด IP เอง)
    ufw deny  5000/tcp                     # Flask  — ห้ามเข้าตรง
    ufw deny  5173/tcp                     # Vite   — ห้ามเข้าตรง
    ;;
  ai)
    ufw allow 22/tcp
    ufw allow from "$BACKEND_IP" to any port 8088 proto tcp   # SD WebUI: รับจาก backend เท่านั้น
    ufw deny  8088/tcp
    ;;
  *)
    echo "usage: $0 backend | ai <backend-ip>"; exit 1 ;;
esac

ufw --force enable
ufw status numbered
