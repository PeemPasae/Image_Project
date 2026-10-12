# ==============================================================================
# ชื่อไฟล์: backend/app/routes/admin.py
# หน้าที่: ระบบจัดการผู้ใช้งานสำหรับผู้ดูแลระบบ (Admin Management Endpoints)
# สิทธิ์การเข้าถึง: สงวนเฉพาะผู้ใช้ที่มี role = 'admin' เท่านั้น
# ==============================================================================

import os
from flask import Blueprint, request, current_app
from sqlalchemy import func

# นำเข้าองค์ประกอบของ Database, Models, Middleware และ Error Codes
from app.extensions import db
from app.models.user import User
from app.models.generation import Generation
from app.middleware.jwt_auth import admin_required
from app.utils.error_codes import (
    success_response,
    error_response,
    USER_NOT_FOUND,
    CANNOT_DELETE_SELF,
    INTERNAL_SERVER_ERROR,
)

# สร้าง Flask Blueprint สำหรับ Admin Endpoints
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """
    GET /api/v1/admin/users 🔒 (Admin Only)
    ดึงรายชื่อผู้ใช้งานทั้งหมดในระบบ พร้อมสถิติจำนวนการสร้างภาพของแต่ละคน
    
    Response:
    {
        "success": true,
        "data": {
            "users": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "role": "admin",
                    "created_at": "2026-10-08T07:15:00",
                    "generation_count": 12
                }
            ],
            "total_users": 1
        }
    }
    """
    try:
        # 1. ดึงผู้ใช้งานทั้งหมด เรียงตาม id จากน้อยไปมาก
        all_users = User.query.order_by(User.id.asc()).all()

        # 2. รวมจำนวน generation_count ของแต่ละ user ด้วย Group By Query เดียวเพื่อประสิทธิภาพสูงสุด
        counts = dict(
            db.session.query(Generation.user_id, func.count(Generation.id))
            .group_by(Generation.user_id)
            .all()
        )

        # 3. จัดโครงสร้างข้อมูลส่งกลับตาม Field ที่ Frontend ต้องการ
        users_data = []
        for u in all_users:
            users_data.append({
                "id": u.id,
                "email": u.email,
                "role": u.role or "user",
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "generation_count": counts.get(u.id, 0),
            })

        return success_response({
            "users": users_data,
            "total_users": len(users_data)
        }, status_code=200)

    except Exception as e:
        current_app.logger.error("Failed to list users for admin: %s", str(e))
        return error_response(INTERNAL_SERVER_ERROR, f"Failed to retrieve user list: {str(e)}", 500)


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id: int):
    """
    DELETE /api/v1/admin/users/:id 🔒 (Admin Only)
    ลบบัญชีผู้ใช้งานที่ระบุ พร้อมล้างประวัติการสร้างภาพ (Database) และไฟล์ภาพบนดิสก์ (Disk Storage) ทั้งหมด
    
    🛡️ กฎความปลอดภัย:
    - ห้ามไม่ให้ Admin ลบบัญชีตัวเอง (ตอบ HTTP 400 พร้อม Error Code: CANNOT_DELETE_SELF)
    """
    # 1. ตรวจสอบว่าแอดมินพยายามลบบัญชีของตัวเองหรือไม่
    if user_id == request.user_id:
        return error_response(
            CANNOT_DELETE_SELF,
            "Admin cannot delete their own account",
            400
        )

    # 2. ค้นหาผู้ใช้งานเป้าหมายในฐานข้อมูล
    target_user = db.session.get(User, user_id)
    if not target_user:
        return error_response(
            USER_NOT_FOUND,
            f"User with ID {user_id} not found",
            404
        )

    try:
        # 3. ค้นหารายการประวัติการสร้างภาพทั้งหมดของ User นี้เพื่อลบไฟล์ภาพบน Disk Storage
        user_generations = Generation.query.filter_by(user_id=target_user.id).all()
        deleted_files_count = 0
        for gen in user_generations:
            if gen.image_path and os.path.isfile(gen.image_path):
                try:
                    os.remove(gen.image_path)
                    deleted_files_count += 1
                except Exception as io_err:
                    current_app.logger.warning("Failed to remove user disk file %s: %s", gen.image_path, str(io_err))

        gen_count = len(user_generations)

        # 4. ลบ User ออกจากฐานข้อมูล (Cascade delete จะลบ rows ใน generations table ให้อัตโนมัติ)
        db.session.delete(target_user)
        db.session.commit()

        current_app.logger.info(
            "Admin ID %s deleted User ID %s (%s). Cleared %d generation DB records and %d disk files.",
            request.user_id,
            user_id,
            target_user.email,
            gen_count,
            deleted_files_count
        )

        # 5. ส่งผลลัพธ์ตอบกลับความสำเร็จ
        return success_response({
            "message": "User and all associated generations and image files deleted successfully",
            "deleted_user_id": user_id,
            "deleted_generations_count": gen_count,
            "deleted_disk_files_count": deleted_files_count
        }, status_code=200)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Failed to delete user ID %s: %s", user_id, str(e))
        return error_response(INTERNAL_SERVER_ERROR, f"Failed to delete user: {str(e)}", 500)
