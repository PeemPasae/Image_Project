import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.commit()

cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("ตารางในฐานข้อมูล:", cur.fetchall())

conn.close()
print("สร้าง/อัปเดตฐานข้อมูลจาก schema.sql เรียบร้อยที่:", DB_PATH)