# app/routes/history.py
from flask import Blueprint, request
from app.middleware.jwt_auth import token_required
from app.extensions import db
from app.models.generation import Generation
from app.utils.error_codes import (
    success_response, error_response, 
    GENERATION_NOT_FOUND
)

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    """GET /api/v1/history - ดึงประวัติการสร้างรูปภาพตาม user_id"""
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)

    # 🔍 ดึงประวัติเฉพาะของ user_id ปัจจุบัน
    pagination = Generation.query.filter_by(user_id=request.user_id)\
        .order_by(Generation.created_at.desc())\
        .paginate(page=page, per_page=limit, error_out=False)

    history_data = [
        item.to_dict()
        for item in pagination.items
    ]

    # 🎯 เปลี่ยน Key จาก "items" เป็น "history" ตามที่คุณต้องการ
    return success_response({
        "history": history_data,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages
        }
    }, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["GET"])
@token_required
def get_generation(generation_id):
    """GET /api/v1/history/:id - ดึงรายละเอียด generation ของผู้ใช้ปัจจุบัน"""
    generation = Generation.query.filter_by(
        id=generation_id,
        user_id=request.user_id,
    ).first()

    if not generation:
        return error_response(GENERATION_NOT_FOUND, "Record not found", 404)

    return success_response(generation.to_dict(), status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["DELETE"])
@token_required
def delete_history(generation_id):
    """DELETE /api/v1/history/:id - ลบรูปภาพออกจาก Disk และ Database"""
    gen = Generation.query.filter_by(id=generation_id, user_id=request.user_id).first()

    if not gen:
        return error_response(GENERATION_NOT_FOUND, "Record not found", 404)

    # ลบภาพและข้อมูลประวัติออกจากฐานข้อมูล
    db.session.delete(gen)
    db.session.commit()

    return success_response({"message": "History deleted successfully"}, status_code=200)