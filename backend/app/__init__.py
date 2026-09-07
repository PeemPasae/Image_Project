# backend/app/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.extensions import db  # 1. Import db มาจาก extensions

def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(
        app,
        origins=[
            "http://localhost:5173",
            "http://172.20.56.147:5173",
            "http://172.20.56.225:5173",
        ],
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # 2. ตั้งค่าการเชื่อมต่อฐานข้อมูล (SQLite)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_path = os.path.join(project_root, "database", "database.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 3. เริ่มการทำงานของ db ร่วมกับ app
    db.init_app(app)

    # 4. Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")

    # 5. โหลดโมเดลทั้งหมดก่อนสร้างตาราง
    with app.app_context():
        from app.models.user import User
        from app.models.generation import Generation
        db.create_all()
        generation_columns = {
            column["name"]
            for column in db.inspect(db.engine).get_columns("generations")
        }
        if "image_data" not in generation_columns:
            db.session.execute(db.text(
                "ALTER TABLE generations ADD COLUMN image_data BLOB"
            ))
            db.session.commit()

    return app