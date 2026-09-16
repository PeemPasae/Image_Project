# ==============================================================================
# ชื่อไฟล์: backend/app/routes/profile.py
# หน้าที่: จัดการข้อมูลโปรไฟล์ของผู้ใช้งาน (User Profile) และสรุปสถิติจำนวนการสร้างภาพแยกตามประเภท
# เกี่ยวข้องกับหน้าเว็บ: หน้า Profile (โปรไฟล์ผู้ใช้), หน้า Setting (การตั้งค่าบัญชี)
# ==============================================================================

from flask import Blueprint, request

# นำเข้าองค์ประกอบของ Database, Models, Middleware และ Error Codes
from app.extensions import db
from app.models.user import User
from app.models.generation import Generation
from app.middleware.jwt_auth import token_required
from app.utils.error_codes import success_response, error_response, UNAUTHORIZED

# สร้าง Flask Blueprint สำหรับกลุ่มเส้นทาง Profile (/api/v1/...)
profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """
    GET /api/v1/profile 🔒 (ต้องใช้ JWT Token)
    ดึงข้อมูลส่วนตัวและสถิติการใช้งานของผู้ใช้งานปัจจุบันที่ล็อกอินอยู่
    
    ข้อมูลที่ส่งกลับ:
    - id : รหัสผู้ใช้ (User ID)
    - email : อีเมลผู้ใช้งาน
    - created_at : วันเวลาที่ลงทะเบียน
    - generation_count : จำนวนรูปภาพทั้งหมดที่สร้าง
    - checkpoint_count : จำนวนรูปที่สร้างจาก Checkpoint (รูปแบบที่ 1)
    - filter_count : จำนวนรูปที่แต่งผ่าน Sub-functions (รูปแบบที่ 2)
    """
    # 1. ค้นหาข้อมูลผู้ใช้งานจากฐานข้อมูลด้วย user_id ที่ได้จาก JWT Token
    current_user = db.session.get(User, request.user_id)
    if not current_user:
        return error_response(UNAUTHORIZED, "User account not found", 401)

    # 2. นับจำนวนภาพทั้งหมดที่สร้างโดยผู้ใช้คนนี้
    total_generations = Generation.query.filter_by(user_id=current_user.id).count()

    # 3. นับจำนวนภาพแยกตามประเภท (แบบที่ 1 AI Checkpoint vs แบบที่ 2 Sub-functions)
    checkpoint_count = Generation.query.filter_by(
        user_id=current_user.id, 
        category="sd_generate"
    ).count()
    
    filter_count = Generation.query.filter_by(
        user_id=current_user.id, 
        category="image_filter"
    ).count()

    # 4. ส่งข้อมูลโปรไฟล์และสถิติกลับไปยัง Frontend ตามมาตรฐาน LUMA
    return success_response({
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "generation_count": total_generations,
        "checkpoint_count": checkpoint_count,
        "filter_count": filter_count,
    }, status_code=200)