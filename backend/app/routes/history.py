# นำเข้า os สำหรับลบไฟล์
import os
# นำเข้า math สำหรับคำนวณจำนวนหน้า Pagination
import math
# นำเข้า Blueprint และ request
from flask import Blueprint, request
# นำเข้า Decorator ตรวจสอบ JWT
from app.middleware.jwt_auth import token_required
# ดึง DB จำลองของ generations
from app.routes.sd import MOCK_GENERATIONS_DB
# นำเข้าตัวตอบกลับและ Error Codes
from app.utils.error_codes import (
    success_response,
    error_response,
    GENERATION_NOT_FOUND,
    INTERNAL_SERVER_ERROR
)

# สร้าง Blueprint "history"
history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    """GET /api/v1/history 🔒 - ดึงประวัติพร้อม Pagination"""
    # อ่านค่า page จาก query string (default=1)
    page = request.args.get("page", default=1, type=int)
    # อ่านค่า limit จาก query string (default=20)
    limit = request.args.get("limit", default=20, type=int)

    # กรองเฉพาะรายการที่เป็นของผู้ใช้ที่ล็อกอินอยู่ (ป้องกัน IDOR)
    user_generations = [
        g for g in MOCK_GENERATIONS_DB.values()
        if g["user_id"] == request.user_id
    ]

    # คำนวณจำนวนรายการทั้งหมด และจำนวนหน้าทั้งหมด
    total = len(user_generations)
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # ตัดช่วงข้อมูลตาม Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = user_generations[start_idx:end_idx]

    # จัดรูปฟอร์แมตข้อมูลตอบกลับ
    items_data = [
        {
            "id": g["id"],
            "prompt": g["prompt"],
            "checkpoint": g["checkpoint"],
            "image_url": f"/api/v1/images/{g['id']}",
            "created_at": g["created_at"]
        }
        for g in paginated_items
    ]

    # คืนโครงสร้างข้อมูลพร้อม pagination object
    return success_response({
        "items": items_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["GET"])
@token_required
def get_history_detail(generation_id):
    """GET /api/v1/history/:id 🔒 - ดูรายละเอียดของภาพนั้น"""
    gen = MOCK_GENERATIONS_DB.get(generation_id)

    # หากไม่เจอข้อมูล ให้คืน 404
    if not gen:
        return error_response(GENERATION_NOT_FOUND, "Generation record not found", 404)

    # ตรวจสอบว่า resource.user_id ตรงกับ user จาก token หรือไม่ (ป้องกัน IDOR)
    if gen["user_id"] != request.user_id:
        return error_response(GENERATION_NOT_FOUND, "Generation record not found", 404)

    return success_response(gen, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["DELETE"])
@token_required
def delete_history(generation_id):
    """DELETE /api/v1/history/:id 🔒 - ลบรูปภาพและประวัติ"""
    gen = MOCK_GENERATIONS_DB.get(generation_id)

    if not gen:
        return error_response(GENERATION_NOT_FOUND, "Generation record not found", 404)

    # เช็ก ownership ป้องกัน IDOR
    if gen["user_id"] != request.user_id:
        return error_response(GENERATION_NOT_FOUND, "Generation record not found", 404)

    file_path = gen.get("image_path")
    # ลบไฟล์ภาพออกจาก Local Disk ก่อน
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # หากลบไฟล์ไม่สำเร็จ ห้ามลบ record ใน DB เด็ดขาด (Rollback)
            return error_response(INTERNAL_SERVER_ERROR, f"Failed to delete image file: {str(e)}", 500)

    # ลบ record ออกจาก DB เมื่อลบไฟล์รูปภาพสำเร็จเรียบร้อย
    del MOCK_GENERATIONS_DB[generation_id]

    return success_response({"message": "History deleted successfully"}, status_code=200)