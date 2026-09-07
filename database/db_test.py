import sqlite3

# เชื่อมต่อ (ถ้ายังไม่มี app.db จะถูกสร้างให้อัตโนมัติ)
conn = sqlite3.connect("app.db")

# ต้องเปิดเองเสมอ ไม่งั้น ON DELETE CASCADE จะไม่ทำงาน
conn.execute("PRAGMA foreign_keys = ON;")

# cursor คือตัวที่ใช้ "รัน" คำสั่ง SQL จริงๆ
cur = conn.cursor()

print("เชื่อมต่อสำเร็จ")
conn.close()