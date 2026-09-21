# ==============================================================================
# ชื่อไฟล์: backend/app/__init__.py
# หน้าที่: Flask Application Factory ทำหน้าที่เริ่มต้นระบบ, ตั้งค่า CORS, เชื่อมต่อฐานข้อมูล,
#         ลงทะเบียน Blueprints ทั้งหมด, และตรวจสอบโครงสร้างตารางอัตโนมัติ (Auto-Migration)
# เกี่ยวข้องกับหน้าเว็บ: โครงสร้างหลักที่เชื่อมโยงระบบ Backend ทั้งหมดเข้ากับ Frontend
# ==============================================================================

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# นำเข้า Extensions และ Configurations
from app.extensions import db
from config import Config


def create_app(test_config=None) -> Flask:
    """
    Application Factory Function สำหรับสร้างและกำหนดค่า Flask Application Instance
    
    :param test_config: คอนฟิกูเรชันสำหรับการทดสอบ (Optional)
    :return: Flask App Instance ที่พร้อมทำงาน
    """
    # 1. โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env
    load_dotenv()

    # 2. สร้าง Flask App Instance
    app = Flask(__name__)

    # 3. โหลดค่าคอนฟิกจากคลาส Config
    app.config.from_object(Config)

    # หากมีการส่ง test_config มา ให้ override ค่าตามที่กำหนด
    if test_config:
        app.config.update(test_config)

    # 4. กำหนดค่า CORS ให้รองรับการเรียกจาก Frontend ทั้ง Localhost และ LAN
    CORS(
        app,
        origins=Config.CORS_ORIGINS,
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # 5. กำหนดเส้นทางไฟล์ฐานข้อมูล SQLite (database/database.db)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        db_dir = os.path.join(project_root, "database")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "database.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 6. เชื่อมต่อ SQLAlchemy Database Extension เข้ากับ Flask App
    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp
    #from app.services.image_filters import process_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    #app.register_blueprint(process_bp, url_prefix="/api/v1")

    # 8. ตรวจสอบและสร้างตารางฐานข้อมูลอัตโนมัติ (Auto Schema Migration)
    with app.app_context():
        from app.models.user import User
        from app.models.generation import Generation

        # สร้างตารางที่ยังไม่มีในฐานข้อมูล
        db.create_all()

        # ตรวจสอบโครงสร้างคอลัมน์ในตาราง generations เพื่อความเข้ากันได้ 100%
        try:
            inspector = db.inspect(db.engine)
            existing_columns = {col["name"] for col in inspector.get_columns("generations")}

            # รายการคำสั่ง SQL สำหรับเพิ่มคอลัมน์ที่จำเป็นหากยังไม่มี
            migrations = [
                ("image_data", "ALTER TABLE generations ADD COLUMN image_data BLOB"),
                ("category", "ALTER TABLE generations ADD COLUMN category VARCHAR(50) DEFAULT 'sd_generate'"),
                ("action_type", "ALTER TABLE generations ADD COLUMN action_type VARCHAR(50) DEFAULT 'txt2img'"),
                ("params", "ALTER TABLE generations ADD COLUMN params TEXT DEFAULT '{}'"),
                ("source_image_id", "ALTER TABLE generations ADD COLUMN source_image_id INTEGER"),
            ]

            for col_name, sql_stmt in migrations:
                if col_name not in existing_columns:
                    db.session.execute(db.text(sql_stmt))
            
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app