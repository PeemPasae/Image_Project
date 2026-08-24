import sqlite3
import os

DB_NAME = "database.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # อ่านไฟล์ schema.sql แล้วรันคำสั่งทั้งหมด
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()