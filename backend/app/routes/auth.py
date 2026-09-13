# นำเข้า datetime สำหรับบันทึกเวลาและคำนวณวันหมดอายุของ JWT
import datetime
# นำเข้า re สำหรับตรวจสอบรูปแบบอีเมล
import re
# นำเข้า jwt สำหรับสร้าง Access Token
import jwt
# นำเข้า Blueprint และ request จาก flask
from flask import Blueprint, request
# นำเข้าเครื่องมือเข้ารหัสรหัสผ่าน และตรวจสอบรหัสผ่าน
from werkzeug.security import generate_password_hash, check_password_hash

# นำเข้าตัวอ่าน secret key จาก middleware
from app.middleware.jwt_auth import get_jwt_secret
# นำเข้าฟังก์ชันตอบกลับ และ Error Codes
from app.utils.error_codes import (
    success_response,
    error_response,
    VALIDATION_ERROR,
    EMAIL_EXISTS,
    INVALID_CREDENTIALS,
    INTERNAL_SERVER_ERROR
)

# สร้าง Blueprint "auth" สำหรับเส้นทางเกี่ยวกับยืนยันตัวตน
auth_bp = Blueprint("auth", __name__)

# จำลองตารางผู้ใช้ใน DB (รอทีม DB นำ SQLAlchemy Model มาเปลี่ยนใช้งาน)
MOCK_USERS_DB = {}
# ตัวนับ ID จำลอง
MOCK_USER_ID_COUNTER = 1


def is_valid_email(email):
    """เช็กว่ารูปแบบสตริงตรงตามฟอร์แมตอีเมลหรือไม่"""
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None


@auth_bp.route("/register", methods=["POST"])
def register():
    """POST /api/v1/register - ลงทะเบียนผู้ใช้ใหม่"""
    # ดึงข้อมูล JSON จาก Body
    data = request.get_json() or {}
    # ดึงค่า email และตัดช่องว่าง
    email = data.get("email", "").strip()
    # ดึงค่า password
    password = data.get("password", "")

    # Validation: ตรวจสอบความถูกต้องของ Email
    if not email or not is_valid_email(email):
        return error_response(VALIDATION_ERROR, "Invalid or missing email address", 400)

    # Validation: รหัสผ่านต้องไม่ต่ำกว่า 8 ตัวอักษร
    if not password or len(password) < 8:
        return error_response(VALIDATION_ERROR, "Password must be at least 8 characters long", 400)

    # ตรวจสอบอีเมลซ้ำในระบบ
    for user in MOCK_USERS_DB.values():
        if user["email"] == email:
            # ตอบกลับ Error 409 EMAIL_EXISTS
            return error_response(EMAIL_EXISTS, "Email is already registered", 409)

    # เข้ารหัสรหัสผ่าน (ห้ามเก็บเป็น Plain Text)
    hashed_password = generate_password_hash(password)

    # เรียกตัวนับ ID
    global MOCK_USER_ID_COUNTER
    user_id = MOCK_USER_ID_COUNTER
    MOCK_USER_ID_COUNTER += 1

    # ดึงเวลาปัจจุบัน UTC
    now = datetime.datetime.now(datetime.timezone.utc)
    # จัดเก็บลงตารางจำลอง
    new_user = {
        "id": user_id,
        "email": email,
        "password_hash": hashed_password,
        "created_at": now.isoformat()
    }
    MOCK_USERS_DB[user_id] = new_user

    # คืน Response สำเร็จ 201 Created
    return success_response({
        "id": new_user["id"],
        "email": new_user["email"],
        "created_at": new_user["created_at"]
    }, status_code=201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/v1/login - เข้าสู่ระบบเพื่อรับ JWT"""
    # ดึงข้อมูล JSON จาก Body
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation: ตรวจสอบค่าว่าง
    if not email or not password:
        return error_response(VALIDATION_ERROR, "Email and password are required", 400)

    # ค้นหาผู้ใช้ตาม Email
    target_user = None
    for user in MOCK_USERS_DB.values():
        if user["email"] == email:
            target_user = user
            break

    # ตรวจสอบว่าพบผู้ใช้หรือไม่ และรหัสผ่านถูกต้องหรือไม่
    if not target_user or not check_password_hash(target_user["password_hash"], password):
        # ตอบกลับ Error 401 INVALID_CREDENTIALS
        return error_response(INVALID_CREDENTIALS, "Invalid email or password", 401)

    try:
        # กำหนดอายุ JWT ไว้ที่ 24 ชั่วโมง
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        # สร้าง Payload
        token_payload = {
            "user_id": target_user["id"],
            "email": target_user["email"],
            "exp": expiration
        }
        # สร้าง JWT Token
        token = jwt.encode(token_payload, get_jwt_secret(), algorithm="HS256")
    except Exception as e:
        return error_response(INTERNAL_SERVER_ERROR, f"Failed to generate token: {str(e)}", 500)

    # คืน Response สำเร็จพร้อม Access Token
    return success_response({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "user": {
            "id": target_user["id"],
            "email": target_user["email"],
            "created_at": target_user["created_at"]
        }
    }, status_code=200)