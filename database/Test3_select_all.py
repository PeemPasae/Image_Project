# ==============================================================================
# Test3_select_all.py — แสดงข้อมูลในฐานข้อมูลจริง (database/database.db) แบบอ่านอย่างเดียว
# ==============================================================================
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT id, email, role, created_at FROM users;")
print("users ทั้งหมด:")
for row in cur.fetchall():
    print(" ", row)

print()

# ไม่ดึงคอลัมน์ image_data (ข้อมูลรูปทั้งก้อน) เพราะจะพิมพ์ไบต์รูปยาวเต็มจอ
cur.execute("""
    SELECT id, user_id, category, action_type, prompt, width, height, seed,
           length(image_data) AS image_bytes, created_at
    FROM generations;
""")
print("generations ทั้งหมด:")
for row in cur.fetchall():
    print(" ", row)

conn.close()
