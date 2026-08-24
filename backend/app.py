import os
import sqlite3
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
AI_SERVER_IP = os.getenv('AI_SERVER_IP', 'http://172.20.57.51:8088')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'database', 'app.db')


# ---------------------------------------------------------
# Database helpers
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            negative_prompt TEXT,
            checkpoint TEXT,
            image_base64 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# App factory
# ---------------------------------------------------------
def create_app():
    app = Flask(__name__)
    CORS(app)
    init_db()

    # import ตรงนี้ (ไม่ใช่บนสุดของไฟล์) เพื่อกัน circular import
    # เพราะ routes.py ต้อง import get_db / AI_SERVER_IP กลับมาจากไฟล์นี้
    from routes import routes_bp
    app.register_blueprint(routes_bp)

    return app