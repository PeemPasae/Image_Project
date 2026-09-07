# app/routes/history.py
import os
from flask import Blueprint, request
from app.middleware.jwt_auth import token_required
from app.extensions import db
from app.models.generation import Generation
from app.utils.error_codes import (
    success_response, error_response, 
    GENERATION_NOT_FOUND, INTERNAL_SERVER_ERROR
)

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    """GET /api/v1/history - ดึงประวัติแบบ Pagination จาก Database"""
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)

    # 🔍 Query เฉพาะของ user_id ปัจจุบัน เรียงลำดับจากใหม่ไปเก่า (desc)
    pagination = Generation.query.filter_by(user_id=request.user_id)\
        .order_by(Generation.created_at.desc())\
        .paginate(page=page, per_page=limit, error_out=False)

    items_data = [
        {
            "id": item.id,
            "prompt": item.prompt,
            "checkpoint": item.checkpoint,
            "image_url": f"/api/v1/images/{item.id}",
            "created_at": item.created_at.isoformat()
        }
        for item in pagination.items
    ]

    return success_response({
        "items": items_data,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages
        }
    }, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["DELETE"])
@token_required
def delete_history(generation_id):
    """DELETE /api/v1/history/:id - ลบรูปภาพออกจาก Disk และ Database"""
    # เช็ก ownership ใน Query เดียว
    gen = Generation.query.filter_by(id=generation_id, user_id=request.user_id).first()

    if not gen:
        return error_response(GENERATION_NOT_FOUND, "Record not found", 404)

    # 1. ลบไฟล์จริงบน Local Disk ก่อน
    if os.path.exists(gen.image_path):
        try:
            os.remove(gen.image_path)
        except Exception as e:
            return error_response(INTERNAL_SERVER_ERROR, f"Failed to delete file: {str(e)}", 500)

    # 2. ลบ Row ออกจาก DB
    db.session.delete(gen)
    db.session.commit()

    return success_response({"message": "History deleted successfully"}, status_code=200)