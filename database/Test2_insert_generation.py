# ==============================================================================
# Test2_insert_generation.py — เพิ่มประวัติรูป 1 รายการให้ user ทดสอบล่าสุด
#
# ⚠️ ใช้กับ user ทดสอบ (test_...@example.com) เท่านั้น ไม่แตะประวัติของผู้ใช้จริง
#    ต้องรัน Test1_create_user.py ก่อน
# ==============================================================================
import sqlite3
import os
import base64
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# รูป PNG ขนาด 1x1 พิกเซล (ตาราง generations บังคับว่าต้องมีข้อมูลรูปใน image_data)
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

# หา user ทดสอบล่าสุด (ไม่ใช้ "user ล่าสุด" เฉย ๆ เพราะอาจเป็นผู้ใช้จริง)
cur.execute("SELECT id FROM users WHERE email LIKE 'test%@example.com' ORDER BY id DESC LIMIT 1;")
row = cur.fetchone()

if row is None:
    print("ยังไม่มี user ทดสอบ ให้รัน Test1_create_user.py ก่อน")
else:
    user_id = row[0]

    # ใส่ทุกคอลัมน์ที่ตารางจริงบังคับ (NOT NULL)
    cur.execute("""
        INSERT INTO generations
            (user_id, category, action_type, prompt, negative_prompt, checkpoint, sampler,
             width, height, steps, cfg_scale, seed, params, image_path, image_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        user_id, "sd_generate", "txt2img",
        "a cat wearing a wizard hat, fantasy art", "",
        "sd_xl_base_1.0", "DPM++ 2M Karras",
        1024, 1024, 20, 7.0, 12345, "{}",
        "", TINY_PNG, datetime.now(),
    ))
    conn.commit()

    print("สร้าง generation สำเร็จ id =", cur.lastrowid, "(user_id =", user_id, ")")

conn.close()
