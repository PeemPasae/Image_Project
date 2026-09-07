# นำเข้า Blueprint และ request
from flask import Blueprint, request
# นำเข้า Decorator เช็ก JWT Token
from app.middleware.jwt_auth import token_required
# ดึง DB จำลองของผู้ใช้
from app.routes.auth import MOCK_USERS_DB
# นำเข้าตัวตอบกลับและ Error Codes
from app.utils.error_codes import success_response, error_response, UNAUTHORIZED

# สร้าง Blueprint "profile"
profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """GET /api/v1/profile 🔒 - ดึงข้อมูลส่วนตัวของผู้ใช้"""
    user = MOCK_USERS_DB.get(request.user_id)
    # หากไม่พบผู้ใช้ ให้ตอบกลับ 401
    if not user:
        return error_response(UNAUTHORIZED, "User not found", 401)

    # ส่งคืนข้อมูลผู้ใช้
    return success_response({
        "id": user["id"],
        "email": user["email"],
        "created_at": user["created_at"]
    }, status_code=200)