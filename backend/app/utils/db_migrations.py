# ==============================================================================
# ชื่อไฟล์: backend/app/utils/db_migrations.py
# หน้าที่: ตรวจสอบและอัปเดตโครงสร้างฐานข้อมูลอัตโนมัติ (Auto Schema Migration)
#         เพื่อให้คอลัมน์ในตารางตรงกับ Model โดยไม่ต้องใช้ Alembic ด้วยตนเอง
# ==============================================================================

import logging

logger = logging.getLogger("luma.db_migrations")


def run_auto_migrations(db) -> None:
    """
    ตรวจสอบตารางในฐานข้อมูล และดำเนินการ ALTER TABLE เพิ่มคอลัมน์ที่ขาดหายไป
    """
    # 1. นำเข้า Models เพื่อให้ SQLAlchemy รับรู้ Schema ล่าสุด
    from app.models.user import User  # noqa: F401
    from app.models.generation import Generation  # noqa: F401

    # 2. สร้างตารางทั้งหมดที่ยังไม่มี
    db.create_all()

    # 3. ตรวจสอบคอลัมน์ของตารางเดิมเพื่อเพิ่มคอลัมน์ใหม่ (Backward Compatibility)
    try:
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()

        # ตรวจสอบตาราง users
        if "users" in table_names:
            existing_user_cols = {col["name"] for col in inspector.get_columns("users")}
            if "role" not in existing_user_cols:
                logger.info("Migrating schema: adding 'role' column to users table")
                db.session.execute(db.text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))

        # ตรวจสอบตาราง generations
        if "generations" in table_names:
            existing_gen_cols = {col["name"] for col in inspector.get_columns("generations")}
            migrations = [
                ("image_data", "ALTER TABLE generations ADD COLUMN image_data BLOB"),
                ("category", "ALTER TABLE generations ADD COLUMN category VARCHAR(50) DEFAULT 'sd_generate'"),
                ("action_type", "ALTER TABLE generations ADD COLUMN action_type VARCHAR(50) DEFAULT 'txt2img'"),
                ("params", "ALTER TABLE generations ADD COLUMN params TEXT DEFAULT '{}'"),
                ("source_image_id", "ALTER TABLE generations ADD COLUMN source_image_id INTEGER"),
            ]

            for col_name, sql_stmt in migrations:
                if col_name not in existing_gen_cols:
                    logger.info("Migrating schema: adding '%s' column to generations table", col_name)
                    db.session.execute(db.text(sql_stmt))

        db.session.commit()
    except Exception as e:
        logger.warning("Auto migration encountered an issue (rolled back): %s", str(e))
        db.session.rollback()
