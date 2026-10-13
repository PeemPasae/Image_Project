# ==============================================================================
# ชื่อไฟล์: database/clear.py
# หน้าที่: สคริปต์สำหรับลบข้อมูลในฐานข้อมูล SQLite
#         รองรับการระบุ user_id ที่ "ไม่ต้องการลบ" (Whitelist) เพื่อเก็บข้อมูลผู้ใช้คนนั้นไว้
# ==============================================================================

import sqlite3
import os
import sys

# รองรับการพิมพ์ข้อความภาษาไทย/UTF-8 บน Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# ⚙️ กำหนด user_id ที่ *ไม่ต้องการลบ* (Whitelist)
# ------------------------------------------------------------------------------
# - หากต้องการลบข้อมูลทั้งหมด (Clear All):
#     EXCLUDE_USER_IDS = []
#
# - หากต้องการเก็บข้อมูลของบาง user_id ไว้ (เช่น ไม่ลบ user_id 1):
#     EXCLUDE_USER_IDS = [1]
#
# - หากต้องการเก็บข้อมูลหลาย user_id (เช่น ไม่ลบ user_id 1, 2, 5):
#     EXCLUDE_USER_IDS = [1, 2, 5]
# ==============================================================================
EXCLUDE_USER_IDS = []  # <-- ใส่ user_id ที่ต้องการเก็บไว้ตรงนี้ (เว้นว่าง [] เพื่อลบทั้งหมด)


def clear_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "database.db")

    if not os.path.exists(db_path):
        print(f"[ERROR] ไม่พบไฟล์ฐานข้อมูลที่: {db_path}")
        return

    print("=" * 65)
    print(f"[*] ฐานข้อมูล: {db_path}")
    if EXCLUDE_USER_IDS:
        print(f"[KEEP] User ID ที่ได้รับการยกเว้น (จะไม่ถูกลบ): {EXCLUDE_USER_IDS}")
    else:
        print("[CLEAR ALL] ไม่มีการยกเว้น User ID -> กำลังจะลบข้อมูลทั้งหมดในฐานข้อมูล")
    print("=" * 65)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ดึงรายชื่อตารางทั้งหมดในฐานข้อมูล (ยกเว้น sqlite system tables)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]
    print(f"[*] ตารางที่พบในฐานข้อมูล: {tables}\n")

    if not EXCLUDE_USER_IDS:
        # ----------------------------------------------------------------------
        # กรณีที่ 1: ลบข้อมูลทั้งหมด (Clear Everything)
        # ----------------------------------------------------------------------
        conn.execute("PRAGMA foreign_keys = OFF;")
        for table in tables:
            cur.execute(f"DELETE FROM {table};")
            print(f"[-] ลบข้อมูลทั้งหมดออกจากตาราง '{table}' เรียบร้อย")

        # รีเซ็ตเลข AUTOINCREMENT ให้กลับไปเริ่มต้นที่ 1
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cur.fetchone():
            cur.execute("DELETE FROM sqlite_sequence;")
            print("[*] รีเซ็ตเลข AUTOINCREMENT (sqlite_sequence) เรียบร้อย")

    else:
        # ----------------------------------------------------------------------
        # กรณีที่ 2: ลบข้อมูลโดยยกเว้น user_id ที่กำหนดไว้
        # ----------------------------------------------------------------------
        excluded_ids = [int(uid) for uid in EXCLUDE_USER_IDS]
        placeholders = ",".join(["?"] * len(excluded_ids))

        conn.execute("PRAGMA foreign_keys = OFF;")

        # 1. ลบจากตาราง generations (ประวัติรูปภาพของผู้ใช้ที่ไม่ได้อยู่ใน EXCLUDE_USER_IDS)
        if "generations" in tables:
            cur.execute(
                f"DELETE FROM generations WHERE user_id NOT IN ({placeholders});",
                excluded_ids,
            )
            deleted_gens = cur.rowcount
            print(f"[-] ลบประวัติรูปภาพใน 'generations' จำนวน {deleted_gens} รายการ (เก็บเฉพาะ user_id: {excluded_ids})")

        # 2. ลบจากตาราง users (ผู้ใช้ที่ไม่ได้อยู่ใน EXCLUDE_USER_IDS)
        if "users" in tables:
            cur.execute(
                f"DELETE FROM users WHERE id NOT IN ({placeholders});",
                excluded_ids,
            )
            deleted_users = cur.rowcount
            print(f"[-] ลบผู้ใช้ใน 'users' จำนวน {deleted_users} บัญชี (เก็บเฉพาะ user_id: {excluded_ids})")

        # 3. จัดการตารางอื่นๆ (ถ้ามี) ที่มีคอลัมน์ user_id
        for table in tables:
            if table in ["users", "generations"]:
                continue
            cur.execute(f"PRAGMA table_info({table});")
            cols = [col[1] for col in cur.fetchall()]
            if "user_id" in cols:
                cur.execute(
                    f"DELETE FROM {table} WHERE user_id NOT IN ({placeholders});",
                    excluded_ids,
                )
                print(f"[-] ลบข้อมูลใน '{table}' (ที่มี user_id) เรียบร้อย")

    conn.commit()
    conn.execute("VACUUM;")
    conn.close()

    # --------------------------------------------------------------------------
    # ตรวจสอบผลลัพธ์หลังการลบ (Verification)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("[*] สรุปข้อมูลคงเหลือในฐานข้อมูล:")
    print("=" * 65)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for table in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        print(f" - ตาราง '{table}': เหลือ {count} แถว")

    if "users" in tables:
        cur.execute("SELECT id, email, created_at FROM users;")
        remaining_users = cur.fetchall()
        if remaining_users:
            print("\n[+] รายชื่อผู้ใช้ที่คงเหลือในระบบ:")
            for u in remaining_users:
                print(f"   [ID: {u[0]}] {u[1]} (สร้างเมื่อ: {u[2]})")
        else:
            print("\n[!] ไม่มีผู้ใช้เหลืออยู่ในระบบ")

    conn.close()
    print("\n[SUCCESS] ดำเนินการเสร็จสิ้นเรียบร้อย!")


if __name__ == "__main__":
    clear_database()
