# ==============================================================================
# ชื่อไฟล์: database/init_db.py
# หน้าที่: สร้างตารางใน database/database.db (ถ้ายังไม่มี) แล้วโชว์ว่ามีตาราง/ข้อมูลอะไรบ้าง
#
# โครงตารางมี "ที่เดียว" คือโมเดลใน backend/app/models/ (user.py, generation.py)
#   - สคริปต์นี้ไม่ได้เขียน CREATE TABLE เอง แต่เรียก create_app() ของ backend
#     ซึ่งสร้างตารางจากโมเดล (db.create_all) + เติมคอลัมน์ที่ขาด แบบเดียวกับตอนเปิด backend
#   - เดิมมี schema.sql เขียนโครงตารางซ้ำอีกชุด สองที่ไม่ตรงกัน จึงลบออก
#
# ข้อมูลเดิมไม่หาย:
#   - create_all() สร้างเฉพาะตารางที่ยังไม่มี ตารางที่มีอยู่แล้วไม่แตะ ไม่ลบ ไม่เขียนทับ
#   - กันพลาดอีกชั้น: ก่อนทำอะไรจะสำรองไฟล์เดิมเป็น database.db.bak ไว้ก่อน (ไม่ขึ้น git)
#
# วิธีรัน (ใช้ Python ตัวเดียวกับ backend เพราะต้องใช้ Flask / SQLAlchemy):
#   python database/init_db.py
# ==============================================================================

import os
import shutil
import sqlite3
import sys

# รองรับการพิมพ์ภาษาไทยบน Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
BACKEND_DIR = os.path.join(BASE_DIR, "..", "backend")

# 1. สำรองไฟล์เดิมก่อน (ถ้ามี)
if os.path.exists(DB_PATH):
    shutil.copy2(DB_PATH, DB_PATH + ".bak")
    print("สำรองไฟล์เดิมไว้ที่:", DB_PATH + ".bak")

# 2. ให้ Python หาโค้ด backend เจอ แล้วเรียก create_app() ซึ่งสร้างตารางจากโมเดล
sys.path.insert(0, BACKEND_DIR)
from app import create_app  # noqa: E402

create_app({
    "SQLALCHEMY_DATABASE_URI": f"sqlite:///{DB_PATH}",
    # create_app ต้องมีรหัสลับถึงจะยอมทำงาน แต่สคริปต์นี้แค่สร้างตาราง ไม่ได้ออก token
    # จึงใช้ค่าชั่วคราวได้ ไม่ต้องมี backend/.env
    "SECRET_KEY": "init-db-only",
    "LOG_FILE": None,  # ไม่ต้องเขียน log ไฟล์
})

# 3. โชว์ผล: ตาราง + จำนวนแถว (ข้อมูลเดิมต้องยังอยู่ครบ)
conn = sqlite3.connect(DB_PATH)
tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
)]
print("ฐานข้อมูล:", DB_PATH)
for name in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  ตาราง {name:<12} {count} แถว")
conn.close()
print("เรียบร้อย (โครงตารางมาจาก backend/app/models/)")
