#!/usr/bin/env bash
# =====================================================================
#  make_htpasswd.sh — สร้าง/เพิ่ม user ในไฟล์ luma_dev.htpasswd (basic auth ของหลังบ้าน)
#
#    bash scripts/make_htpasswd.sh <username>          # ถามรหัสผ่าน (ไม่โชว์บนจอ)
#    bash scripts/make_htpasswd.sh <username> <pass>
#
#  ใช้ได้ทั้ง Git Bash (Windows) และ Linux — ต้องมี openssl
#  ผลลัพธ์อยู่ที่ nginx/luma_dev.htpasswd → ก๊อปไปวางข้าง nginx.conf บนเครื่อง nginx
# =====================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/luma_dev.htpasswd"

USER_NAME="${1:-}"
[ -z "$USER_NAME" ] && { echo "usage: $0 <username> [password]"; exit 1; }

if [ -n "${2:-}" ]; then
    PASS="$2"
else
    read -r -s -p "Password for $USER_NAME: " PASS; echo
fi
[ "${#PASS}" -lt 8 ] && { echo "รหัสผ่านต้องยาว >= 8 ตัวอักษร"; exit 1; }

HASH="$(openssl passwd -apr1 "$PASS")"

# ลบ user เดิม (ถ้ามี) แล้วเติมใหม่
touch "$OUT"
grep -v "^${USER_NAME}:" "$OUT" > "$OUT.tmp" || true
echo "${USER_NAME}:${HASH}" >> "$OUT.tmp"
mv "$OUT.tmp" "$OUT"

echo "เพิ่ม/อัปเดต user '$USER_NAME' ใน $OUT แล้ว"
echo "อย่าลืม: nginx -s reload"
