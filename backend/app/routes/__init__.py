# ==============================================================================
# ชื่อไฟล์: backend/app/routes/__init__.py
# หน้าที่: รวบรวมและลงทะเบียน Blueprints ทั้งหมดของระบบ API
# ==============================================================================

from flask import Flask

from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.sd import sd_bp
from app.routes.history import history_bp
from app.routes.admin import admin_bp
from app.routes.process import process_bp

__all__ = [
    "auth_bp",
    "profile_bp",
    "sd_bp",
    "history_bp",
    "admin_bp",
    "process_bp",
    "register_routes",
]


def register_routes(app: Flask) -> None:
    """
    ลงทะเบียน Blueprints ทั้งหมดเข้ากับ Flask Application Instance
    พร้อมกำหนด URL Prefixes (/api/v1) และ Aliases สำหรับความเข้ากันได้ย้อนหลัง
    """
    # 1. กลุ่มเส้นทาง API มาตรฐาน (/api/v1/...)
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(process_bp, url_prefix="/api/v1")

    # 2. URL Aliases เพื่อรองรับ Frontend ที่เรียก URL แบบไม่มี /api/v1
    app.register_blueprint(auth_bp, url_prefix="", name="auth_alias")
    app.register_blueprint(profile_bp, url_prefix="", name="profile_alias")
    app.register_blueprint(sd_bp, url_prefix="", name="sd_alias")
    app.register_blueprint(history_bp, url_prefix="", name="history_alias")
