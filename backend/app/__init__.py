# backend/app/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from app.extensions import db  # 1. Import db มาจาก extensions

def create_app():
    app = Flask(__name__)
    CORS(app)

    # 2. ตั้งค่าการเชื่อมต่อฐานข้อมูล (SQLite)
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 3. เริ่มการทำงานของ db ร่วมกับ app
    db.init_app(app)

    # 4. Register Blueprints
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp

    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")

    # 5. โหลดโมเดลทั้งหมดก่อนสร้างตาราง
    with app.app_context():
        from app.models.generation import Generation
        db.create_all()

    return app