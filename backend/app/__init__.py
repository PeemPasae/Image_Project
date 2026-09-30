# backend/app/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.extensions import db  # 1. Import db มาจาก extensions

def create_app():
    # โหลด backend/.env (JWT_SECRET_KEY, AI_SERVER_URL, CORS_ORIGINS ...) ไม่ว่าจะถูกเรียกจาก run.py หรือ pytest
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

    app = Flask(__name__)

    # CORS: อนุญาตเฉพาะ origin ที่ระบุ (spec ข้อ 6) — ค่า default คือ Vite dev server
    # ตอนอยู่หลัง nginx หน้าเว็บกับ API เป็น origin เดียวกัน → ไม่ต้องพึ่ง CORS เลย
    # ทดสอบข้ามเครื่องให้เติมใน .env:  CORS_ORIGINS=http://localhost:5173,http://172.20.56.158:5173
    cors_origins = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]
    CORS(app, origins=cors_origins, resources={r"/api/*": {"origins": cors_origins}})

    # 2. ตั้งค่าการเชื่อมต่อฐานข้อมูล (SQLite)
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 3. เริ่มการทำงานของ db ร่วมกับ app
    db.init_app(app)

    # 4. Register Blueprints
    from app.routes.auth import auth_bp          # /register, /login
    from app.routes.profile import profile_bp    # /profile
    from app.routes.sd import sd_bp              # /generate, /images/<id>
    from app.routes.history import history_bp    # /history, /history/<id>
    # หมายเหตุ: ไม่ register images_bp เพราะ /images/<id> มีอยู่ใน sd_bp แล้ว (ตัวที่ใช้ DB จริง)
    # และ images.py ยัง import MOCK_GENERATIONS_DB ที่ถูกลบไปแล้ว

    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")

    # 5. โหลดโมเดลทั้งหมดก่อนสร้างตาราง
    with app.app_context():
        from app.models.generation import Generation
        db.create_all()

    return app