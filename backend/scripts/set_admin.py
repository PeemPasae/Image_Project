# ==============================================================================
# ชื่อไฟล์: backend/scripts/set_admin.py
# หน้าที่: สคริปต์ CLI สำหรับตั้งค่าสิทธิ์ Admin หรือดูรายชื่อบัญชีผู้ใช้ในระบบ
# การใช้งาน:
#   1. ดูรายชื่อผู้ใช้ทั้งหมด:
#      python backend/scripts/set_admin.py --list
#   2. ตั้งผู้ใช้เป็น Admin:
#      python backend/scripts/set_admin.py user@example.com
#   3. ปลดสิทธิ์ Admin กลับเป็น User ทั่วไป:
#      python backend/scripts/set_admin.py --revoke user@example.com
# ==============================================================================

import sys
import os
import argparse

# เพิ่มพาธ backend เข้า sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from app.extensions import db
from app.models.user import User


def list_users(app):
    with app.app_context():
        users = User.query.order_by(User.id.asc()).all()
        print("=" * 65)
        print(f"{'ID':<6} {'Role':<10} {'Email':<35} {'Created At'}")
        print("-" * 65)
        for u in users:
            role_display = f"[{u.role}]" if u.role == "admin" else u.role
            created = u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "-"
            print(f"{u.id:<6} {role_display:<10} {u.email:<35} {created}")
        print("=" * 65)
        print(f"Total: {len(users)} users\n")


def set_user_role(app, email: str, role: str):
    with app.app_context():
        user = User.query.filter_by(email=email.strip()).first()
        if not user:
            print(f"[!] Error: User with email '{email}' not found in database.")
            return False

        old_role = user.role
        user.role = role
        db.session.commit()
        print(f"[*] Success: User '{email}' (ID: {user.id}) role changed: '{old_role}' -> '{role}'")
        return True


def main():
    parser = argparse.ArgumentParser(description="Manage user roles (admin / user) for LUMA Backend")
    parser.add_argument("email", nargs="?", help="Email of the user to update")
    parser.add_argument("--list", action="store_true", help="List all users and their current roles")
    parser.add_argument("--role", default="admin", choices=["admin", "user"], help="Role to assign (default: admin)")
    parser.add_argument("--revoke", action="store_true", help="Revoke admin role (set back to 'user')")

    args = parser.parse_args()
    app = create_app()

    if args.list or not args.email:
        list_users(app)
        if not args.email:
            print("Tip: Run 'python backend/scripts/set_admin.py <email>' to grant admin privileges.")
        return

    target_role = "user" if args.revoke else args.role
    set_user_role(app, args.email, target_role)


if __name__ == "__main__":
    main()
