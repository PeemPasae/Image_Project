# นำเข้า os
import os
# นำเข้า send_file สำหรับส่งไฟล์ภาพ Binary กลับไปหา Client
from flask import Blueprint, send_file
# นำเข้า Decorator เช็ก JWT Token
from app.middleware.jwt_auth import token_required
# ดึง DB จำลองของ generations
from app.routes.sd import MOCK_GENERATIONS_DB
# นำเข้าตัวตอบกลับและ Error Codes
from app.utils.error_codes import error_response, IMAGE_NOT_FOUND

# สร้าง Blueprint "images"
images_bp = Blueprint("images", __name__)


@images_bp.route("/images/<int:generation_id>", methods=["GET"])
@token_required
def get_image_file(generation_id):
    """GET /api/v1/images/:generation_id 🔒 - ส่งไฟล์ Binary Stream ของรูปภาพ"""
    gen = MOCK_GENERATIONS_DB.get(generation_id)

    # ถ้าไม่พบเรคคอร์ด คืน 404
    if not gen:
        return error_response(IMAGE_NOT_FOUND, "Image not found", 404)

    # เช็ก Ownership IDOR: resource.user_id ต้องตรงกับ token
    if gen["user_id"] != request.user_id:
        return error_response(IMAGE_NOT_FOUND, "Image not found", 404)

    file_path = gen.get("image_path")
    # ตรวจสอบว่ามีไฟล์อยู่บน Disk จริงไหม
    if not file_path or not os.path.exists(file_path):
        return error_response(IMAGE_NOT_FOUND, "Image file is missing on server", 404)

    # คืนไฟล์แบบ Binary Stream (Content-Type: image/png) ไม่ใช้ JSON Envelope
    return send_file(file_path, mimetype="image/png")