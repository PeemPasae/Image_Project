# ==============================================================================
# ชื่อไฟล์: backend/app/routes/history.py
# หน้าที่: จัดการประวัติการสร้างรูปภาพของผู้ใช้งาน (History) รองรับการแสดงผลทั้ง 2 รูปแบบ
#         (แบบที่ 1 Checkpoint ปกติ และ แบบที่ 2 Sub-Functions) พร้อมระบบแบ่งหน้าและป้องกันข้ามสิทธิ์
# เกี่ยวข้องกับหน้าเว็บ: หน้า History (ประวัติทั้งหมด), หน้ารายละเอียดภาพ, หน้า Home (แสดงประวัติย่อ)
# ==============================================================================

import os
from flask import Blueprint, request

# นำเข้าองค์ประกอบของ Database, Models, Middleware และ Error Codes
from app.extensions import db
from app.models.generation import Generation
from app.middleware.jwt_auth import token_required
from app.utils.error_codes import (
    success_response,
    error_response,
    GENERATION_NOT_FOUND,
    INTERNAL_SERVER_ERROR,
)

# สร้าง Flask Blueprint สำหรับกลุ่มเส้นทาง History (/api/v1/...)
history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    """
    GET /api/v1/history 🔒 (ต้องใช้ JWT Token)
    ดึงรายการประวัติการสร้างภาพของผู้ใช้งานปัจจุบัน โดยแยกตาม user_id อย่างเด็ดขาด
    
    Query Parameters ที่รองรับ:
    - category : กรองตามหมวดหมู่ ('sd_generate' สำหรับแบบที่ 1, 'image_filter' สำหรับแบบที่ 2)
    - type     : กรองตามประเภท ('checkpoint' หรือ 'sub_function')
    - page     : หมายเลขหน้าที่ต้องการดู (ค่าเริ่มต้น: 1)
    - limit    : จำนวนรายการต่อหน้า (ค่าเริ่มต้น: 20 รายการ)
    """
    # 1. รับค่า Query Parameters จาก URL (Frontend ส่งเฉพาะ page, limit)
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)

    # 2. สร้าง Base Query ที่กรองเฉพาะข้อมูลของผู้ใช้ปัจจุบันเท่านั้น (User Isolation)
    query = Generation.query.filter_by(user_id=request.user_id)

    # 4. เรียงลำดับจากภาพล่าสุดไปเก่าสุด (created_at DESC) และแบ่งหน้า Pagination
    pagination = query.order_by(Generation.created_at.desc()).paginate(
        page=page, 
        per_page=limit, 
        error_out=False
    )

    # 5. แปลง Object แต่ละรายการเป็น Dictionary พร้อมข้อมูลประเภทภาพที่ชัดเจน
    history_items = [item.to_dict() for item in pagination.items]

    # 6. ส่งผลลัพธ์กลับไปยัง Frontend พร้อมโครงสร้าง Pagination ครบถ้วน
    return success_response({
        "history": history_items,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        }
    }, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["GET"])
@token_required
def get_generation_detail(generation_id: int):
    """
    GET /api/v1/history/:id 🔒 (ต้องใช้ JWT Token)
    ดึงรายละเอียดแบบเต็มของภาพรายการหนึ่ง พร้อมพารามิเตอร์ทั้งหมดที่ใช้สร้าง
    
    🛡️ ระบบป้องกัน IDOR:
    - ตรวจสอบว่าภาพนี้เป็นของผู้ใช้ปัจจุบันจริง (id=generation_id และ user_id=request.user_id)
    - หากไม่ใช่ของตนเอง จะตอบกลับ 404 เพื่อไม่ให้ผู้อื่นรู้ว่ามีเรคคอร์ดนี้อยู่
    """
    # 1. ค้นหารายการภาพโดยเช็กทั้ง ID ภาพ และ ID ผู้ใช้งาน
    generation = Generation.query.filter_by(
        id=generation_id,
        user_id=request.user_id
    ).first()

    # 2. หากไม่พบภาพ หรือเป็นภาพของผู้อื่น
    if not generation:
        return error_response(
            GENERATION_NOT_FOUND, 
            "Generation record not found or access denied", 
            404
        )

    # 3. ส่งข้อมูลรายละเอียดของภาพกลับไป
    return success_response(generation.to_dict(), status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["DELETE"])
@token_required
def delete_history(generation_id: int):
    """
    DELETE /api/v1/history/:id 🔒 (ต้องใช้ JWT Token)
    ลบรายการประวัติรูปภาพออกจากระบบ
    
    🛡️ ระบบป้องกัน IDOR:
    - ตรวจสอบว่าภาพนี้เป็นของผู้ใช้ปัจจุบันจริงก่อนทำการลบ
    - ไม่อนุญาตให้ผู้ใช้คนใดลบข้อมูลของผู้อื่นโดยเด็ดขาด
    """
    # 1. ค้นหารายการภาพที่ต้องการลบของผู้ใช้ปัจจุบัน
    target_gen = Generation.query.filter_by(
        id=generation_id,
        user_id=request.user_id
    ).first()

    # 2. หากไม่พบภาพ หรือเป็นภาพของผู้อื่น
    if not target_gen:
        return error_response(
            GENERATION_NOT_FOUND, 
            "Generation record not found or access denied", 
            404
        )

    try:
        # 3. ลบไฟล์ภาพออกจาก Disk Storage หากมี
        if target_gen.image_path and os.path.isfile(target_gen.image_path):
            try:
                os.remove(target_gen.image_path)
            except Exception:
                pass

        # 4. ลบข้อมูลออกจากฐานข้อมูล SQLite
        db.session.delete(target_gen)
        db.session.commit()
        
        # 5. ส่งผลการลบสำเร็จกลับไปยัง Frontend
        return success_response(
            {"message": "Generation deleted successfully"}, 
            status_code=200
        )
    except Exception as e:
        # กรณีเกิดข้อผิดพลาดในการลบ
        db.session.rollback()
        return error_response(
            INTERNAL_SERVER_ERROR, 
            f"Failed to delete generation: {str(e)}", 
            500
        )


# ==============================================================================
# [UNUSED BY FRONTEND] การกรองประวัติตาม category หรือ type
# Frontend ไม่ได้ส่ง parameter เหล่านี้มา (ส่งเฉพาะ page, limit เสมอ)
# เผื่อต้องการนำกลับมาเปิดใช้งานในอนาคต (เพียงเอาเครื่องหมาย # ออก)
# ==============================================================================
# category = request.args.get("category", type=str)
# gen_type = request.args.get("type", type=str)
# if category:
#     query = query.filter_by(category=category)
# elif gen_type == "checkpoint":
#     query = query.filter_by(category="sd_generate")
# elif gen_type == "sub_function":
#     query = query.filter_by(category="image_filter")