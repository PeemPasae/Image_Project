# backend/app/__init__.py

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.utils.error_codes import error_response, INTERNAL_SERVER_ERROR, VALIDATION_ERROR

# โหลดตัวแปรจาก .env
load_dotenv()


def create_app():
    """Application Factory สำหรับเริ่มต้น Flask App"""
    app = Flask(__name__)

    # อ่านค่า Secret Key
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # กำหนด Origins อัปเดตตาม IP Frontend ใหม่
    allowed_origins = [
        "http://localhost:5173",
        "http://172.20.56.225:5173"
    ]
    CORS(app, resources={r"/api/v1/*": {"origins": allowed_origins}}, supports_credentials=True)

    # นำเข้า Blueprints ทั้งหมด
    from app.routes.auth import auth_bp
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp
    from app.routes.images import images_bp
    from app.routes.profile import profile_bp

    # ลงทะเบียน Blueprints กำหนด prefix /api/v1/
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    app.register_blueprint(images_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return error_response(VALIDATION_ERROR, str(e.description if hasattr(e, 'description') else e), 400)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response(INTERNAL_SERVER_ERROR, "An internal server error occurred", 500)

    return app