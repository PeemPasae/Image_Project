import math
import os

from flask import Blueprint, request

from app.middleware.jwt_auth import token_required
from app.routes.sd import MOCK_GENERATIONS_DB
from app.utils.error_codes import (
    GENERATION_NOT_FOUND,
    INTERNAL_SERVER_ERROR,
    error_response,
    success_response,
)

history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    """GET /api/v1/history 🔒 - ดึงประวัติพร้อม Pagination"""
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=20, type=int)

    user_generations = [
        g for g in MOCK_GENERATIONS_DB.values() if g["user_id"] == request.user_id
    ]

    total = len(user_generations)
    total_pages = math.ceil(total / limit) if total > 0 else 1

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = user_generations[start_idx:end_idx]

    items_data = [
        {
            "id": g["id"],
            "prompt": g["prompt"],
            "checkpoint": g["checkpoint"],
            "image_url": f"/api/v1/images/{g['id']}",
            "created_at": g["created_at"],
        }
        for g in paginated_items
    ]

    return success_response(
        {
            "items": items_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            },
        },
        status_code=200,
    )


@history_bp.route("/history/<int:generation_id>", methods=["GET"])
@token_required
def get_history_detail(generation_id):
    """GET /api/v1/history/:id 🔒 - ดูรายละเอียดของภาพนั้น"""
    gen = MOCK_GENERATIONS_DB.get(generation_id)

    if not gen or gen["user_id"] != request.user_id:
        return error_response(
            GENERATION_NOT_FOUND, "Generation record not found", 404
        )

    return success_response(gen, status_code=200)


@history_bp.route("/history/<int:generation_id>", methods=["DELETE"])
@token_required
def delete_history(generation_id):
    """DELETE /api/v1/history/:id 🔒 - ลบรูปภาพและประวัติ"""
    gen = MOCK_GENERATIONS_DB.get(generation_id)

    if not gen or gen["user_id"] != request.user_id:
        return error_response(
            GENERATION_NOT_FOUND, "Generation record not found", 404
        )

    file_path = gen.get("image_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            return error_response(
                INTERNAL_SERVER_ERROR,
                f"Failed to delete image file: {str(e)}",
                500,
            )

    del MOCK_GENERATIONS_DB[generation_id]

    return success_response(
        {"message": "History deleted successfully"}, status_code=200
    )