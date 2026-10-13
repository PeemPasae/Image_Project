# ==============================================================================
# ชื่อไฟล์: backend/app/__init__.py
# หน้าที่: Flask Application Factory ทำหน้าที่เริ่มต้นระบบ, ตั้งค่า CORS, เชื่อมต่อฐานข้อมูล,
#         ลงทะเบียน Blueprints ทั้งหมด, และเรียกใช้ระบบ Auto Schema Migration
# ==============================================================================

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import RequestEntityTooLarge

from app.extensions import db
from app.routes import register_routes
from app.utils.error_codes import success_response, error_response
from app.utils.db_migrations import run_auto_migrations
from config import Config


def _setup_logging(app: Flask) -> None:
    """
    ตั้งค่าระบบ Centralized Logging บันทึกทั้ง Console และ Rotating Log File
    """
    log_level = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    app.logger.setLevel(log_level)

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler
    if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)

    # 2. File Handler (เมื่อไม่ใช่ Testing Mode)
    if not app.config.get("TESTING"):
        log_file_path = app.config.get("LOG_FILE")
        if log_file_path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(log_file_path)), exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_file_path,
                    maxBytes=5 * 1024 * 1024,  # 5 MB ต่อไฟล์
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
    # 1. โหลดตัวแปรสภาพแวดล้อม
    load_dotenv()

    # 2. สร้าง Flask App Instance
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # 3. กำหนดค่า CORS
    CORS(
        app,
        origins=Config.CORS_ORIGINS,
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # 4. กำหนดเส้นทางฐานข้อมูลเริ่มต้น (database/database.db)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        db_dir = os.path.join(project_root, "database")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "database.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 5. โฟลเดอร์เก็บไฟล์รูปภาพ
    upload_dir = app.config.get("UPLOAD_FOLDER")
    if upload_dir:
        os.makedirs(os.path.join(upload_dir, "generations"), exist_ok=True)

    # 6. ตั้งค่า Logging
    _setup_logging(app)

    # 7. ผูก Extensions & Routes
    db.init_app(app)
    register_routes(app)

    # 8. Health Check Endpoint
    @app.route("/health", methods=["GET"])
    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        """ตรวจสอบความพร้อมทำงานของระบบ Backend"""
        return success_response({
            "status": "healthy",
            "database": "connected",
            "ai_server_url": app.config.get("AI_SERVER_URL"),
        }, status_code=200)

    # 9. Global Error Handler: 413 Payload Too Large
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(exc):
        return error_response(
            "FILE_TOO_LARGE",
            "Uploaded file exceeds the maximum allowed limit of 16 MB",
            413
        )

    # 10. ProxyFix สำหรับ Nginx Reverse Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # 11. อัปเดตตารางฐานข้อมูลอัตโนมัติ (Auto Schema Migration)
    with app.app_context():
        run_auto_migrations(db)

    return app