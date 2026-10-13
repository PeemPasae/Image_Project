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
from werkzeug.middleware.proxy_fix import ProxyFix

# นำเข้า Extensions และ Configurations
import logging
from logging.handlers import RotatingFileHandler
from app.extensions import db
from config import Config


def _setup_logging(app: Flask) -> None:
    """
    ตั้งค่าระบบ Centralized Logging บันทึกทั้ง Console และ Log File แบบหมุนเวียน (Rotating)
    """
    log_level = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    app.logger.setLevel(log_level)

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)

    # File Handler (ถ้าไม่ใช่ Testing Mode)
    if not app.config.get("TESTING"):
        log_file_path = app.config.get("LOG_FILE")
        if log_file_path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(log_file_path)), exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file_path, 
                    maxBytes=5 * 1024 * 1024, # 5 MB ต่อไฟล์
                    backupCount=3, 
                    encoding="utf-8"
                )
                file_handler.setFormatter(log_format)
                file_handler.setLevel(log_level)
                app.logger.addHandler(file_handler)
            except Exception as e:
                app.logger.warning("Failed to initialize rotating file logger: %s", str(e))


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

    # [แก้บัค] ไม่ยอมเปิด backend ถ้าไม่มีรหัสลับสำหรับเซ็น JWT (กันคนปลอม token)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "ยังไม่ได้ตั้ง JWT_SECRET_KEY ในไฟล์ backend/.env — "
            "สร้างได้ด้วย: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )

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

    # 5.1 ตรวจสอบและสร้างโฟลเดอร์สำหรับจัดเก็บไฟล์ภาพ (Disk Uploads Storage)
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        os.makedirs(os.path.join(upload_dir, "generations"), exist_ok=True)

    # 5.2 ตั้งค่าระบบ Centralized Logging
    _setup_logging(app)

    # 6. เชื่อมต่อ SQLAlchemy Database Extension เข้ากับ Flask App
    db.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp
    from app.routes.admin import admin_bp
    from app.services.image_filters import process_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(process_bp, url_prefix="/api/v1")

    # URL Aliases สำหรับรองรับคำขอทั้งที่มีและไม่มีคำนำหน้า /api/v1
    # ป้องกัน 404 กรณี Frontend ยิงตรงไปที่ /register, /login, /models, /profile ฯลฯ
    app.register_blueprint(auth_bp, url_prefix="", name="auth_alias")
    app.register_blueprint(profile_bp, url_prefix="", name="profile_alias")
    app.register_blueprint(sd_bp, url_prefix="", name="sd_alias")
    app.register_blueprint(history_bp, url_prefix="", name="history_alias")

    # 6.1 เส้นทางตรวจสอบสถานะเซิร์ฟเวอร์ (Health Check Endpoint)
    from app.utils.error_codes import success_response, error_response
    @app.route("/health", methods=["GET"])
    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        """GET /health หรือ /api/v1/health ตรวจสอบความพร้อมทำงานของระบบ Backend"""
        # [แก้บัค] ไม่ส่ง IP ของเครื่อง AI กลับไป เพราะ endpoint นี้ใครก็เปิดได้
        return success_response({
            "status": "healthy",
            "database": "connected",
        }, status_code=200)

    # 6.2 ตัวดักจับข้อผิดพลาดขนาดไฟล์เกินกำหนด (413 Payload Too Large)
    from werkzeug.exceptions import RequestEntityTooLarge, HTTPException
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(exc):
        return error_response(
            "FILE_TOO_LARGE",
            "Uploaded file exceeds the maximum allowed limit of 16 MB",
            413
        )

    # 6.3 [แก้บัค] error อื่น ๆ ทั้งหมดให้ตอบเป็น JSON แบบเดียวกับ API ปกติ
    #     เดิม Flask ตอบเป็นหน้า HTML (เช่น 404, 405, 500) ทำให้หน้าเว็บอ่าน error ไม่ออก
    @app.errorhandler(Exception)
    def handle_any_error(exc):
        if isinstance(exc, HTTPException):
            # error ที่ Flask รู้จัก เช่น 404 Not Found -> code "NOT_FOUND"
            code = exc.name.upper().replace(" ", "_")
            return error_response(code, exc.description, exc.code)
        # error ที่ไม่คาดคิดในโค้ด -> บันทึก log แล้วตอบ 500
        app.logger.exception("Unexpected error: %s", exc)
        return error_response("INTERNAL_SERVER_ERROR", "Unexpected server error", 500)

    # 7. ครอบ wsgi_app ด้วย ProxyFix เพื่อให้อ่านค่าจาก Nginx Reverse Proxy ถูกต้อง
    #    (x_for=1, x_proto=1, x_host=1) ทำให้ request.remote_addr เป็น IP จริงของผู้ใช้
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # 8. ตรวจสอบและสร้างตารางฐานข้อมูลอัตโนมัติ (Auto Schema Migration)
    with app.app_context():
        from app.models.user import User
        from app.models.generation import Generation

        # สร้างตารางที่ยังไม่มีในฐานข้อมูล
        db.create_all()

        # ตรวจสอบโครงสร้างคอลัมน์ในตารางเพื่อความเข้ากันได้ 100%
        try:
            inspector = db.inspect(db.engine)
            
            # 8.1 อัปเดตตาราง users หากยังไม่มีคอลัมน์ role
            existing_user_columns = {col["name"] for col in inspector.get_columns("users")}
            if "role" not in existing_user_columns:
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))

            # 8.2 อัปเดตตาราง generations
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