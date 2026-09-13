import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.execute(
    "INSERT INTO users (email, password_hash) VALUES (?, ?);",
    ("peem@example.com", "fake_hashed_password_123")
)
conn.commit()

print("สร้าง user สำเร็จ id =", cur.lastrowid)

conn.close()