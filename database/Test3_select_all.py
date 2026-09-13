import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.execute("SELECT * FROM users;")
print("users ทั้งหมด:")
for row in cur.fetchall():
    print(" ", row)

print()

cur.execute("SELECT * FROM generations;")
print("generations ทั้งหมด:")
for row in cur.fetchall():
    print(" ", row)

conn.close()