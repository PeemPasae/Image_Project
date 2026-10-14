# ==============================================================================
# Test1_create_user.py — สร้าง user ทดสอบ 1 คนในฐานข้อมูลจริง (database/database.db)
#
# ⚠️ สคริปต์นี้เขียนลงฐานข้อมูลจริงที่ backend ใช้
#    user ทดสอบจะมี email แบบ test_<เวลา>@example.com เพื่อแยกจากผู้ใช้จริง
#    และ login ไม่ได้ (รหัสผ่านเป็นค่าปลอม) ลบทิ้งได้ด้วย clear.py
# ==============================================================================
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

# ใส่เวลาลงใน email ให้ไม่ซ้ำกัน รันกี่รอบก็ได้ (email ในตาราง users ห้ามซ้ำ)
now = datetime.now()
email = f"test_{now:%Y%m%d_%H%M%S}@example.com"

# ตารางจริงบังคับให้ใส่ created_at และ role ด้วย
cur.execute(
    "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?);",
    (email, "fake_hashed_password_123", "user", now)
)
conn.commit()

print("สร้าง user ทดสอบสำเร็จ id =", cur.lastrowid, "email =", email)

conn.close()
