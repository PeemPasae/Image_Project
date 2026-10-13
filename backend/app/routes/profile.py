# ==============================================================================
# ชื่อไฟล์: backend/app/routes/profile.py
# หน้าที่: จัดการข้อมูลโปรไฟล์ของผู้ใช้งาน (User Profile) และสรุปสถิติจำนวนการสร้างภาพ
# เกี่ยวข้องกับหน้าเว็บ: หน้า Profile (โปรไฟล์ผู้ใช้), หน้า Setting (การตั้งค่าบัญชี)
# ==============================================================================

from flask import Blueprint, request

from app.extensions import db
from app.models.user import User
from app.models.generation import Generation
from app.middleware.jwt_auth import token_required
from app.utils.error_codes import success_response, error_response, UNAUTHORIZED

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """
    GET /api/v1/profile 🔒 (ต้องใช้ JWT Token)
    ดึงข้อมูลส่วนตัวและสถิติการใช้งานของผู้ใช้งานปัจจุบันที่ล็อกอินอยู่
    """
    # 1. ค้นหาข้อมูลผู้ใช้งานจากฐานข้อมูลด้วย user_id ที่ได้จาก JWT Token
    current_user = db.session.get(User, request.user_id)
    if not current_user:
        return error_response(UNAUTHORIZED, "User account not found", 401)

    # 2. นับจำนวนภาพทั้งหมดที่สร้างโดยผู้ใช้คนนี้
    total_generations = Generation.query.filter_by(user_id=current_user.id).count()

    # 3. ส่งข้อมูลโปรไฟล์และสถิติกลับไปยัง Frontend
    return success_response({
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role or "user",
        "is_admin": (current_user.role == "admin"),
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "generation_count": total_generations,
    }, status_code=200)