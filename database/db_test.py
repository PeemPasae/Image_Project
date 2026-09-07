import sqlite3
import os

# หาตำแหน่งโฟลเดอร์ที่ไฟล์ .py นี้อยู่จริงๆ ไม่สนว่ารันจากไหน
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("ตารางในฐานข้อมูล:", cur.fetchall())
print("สร้างตาราง users สำเร็จที่:", DB_PATH)

conn.close()