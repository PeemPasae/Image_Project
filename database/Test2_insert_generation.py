import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

# หา user ล่าสุดที่มีอยู่ในฐานข้อมูล (แทนที่จะ hardcode id เอง)
cur.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1;")
row = cur.fetchone()

if row is None:
    print("ยังไม่มี user ในฐานข้อมูลเลย ให้รัน 1_create_user.py ก่อน")
else:
    user_id = row[0]

    cur.execute("""
        INSERT INTO generations (user_id, prompt, checkpoint, sampler, width, height, steps, cfg_scale, seed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        user_id,
        "a cat wearing a wizard hat, fantasy art",
        "sd_xl_base_1.0",
        "DPM++ 2M Karras",
        1024, 1024, 20, 7.0, -1
    ))
    conn.commit()

    print("สร้าง generation สำเร็จ id =", cur.lastrowid, "(user_id =", user_id, ")")

conn.close()