# ==============================================================================
# ชื่อไฟล์: backend/app/routes/auth.py
# หน้าที่: จัดการระบบลงทะเบียนผู้ใช้ (Register) และระบบเข้าสู่ระบบ (Login) พร้อมตรวจสอบชื่อซ้ำ
# เกี่ยวข้องกับหน้าเว็บ: หน้า Register (สมัครสมาชิก), หน้า Login (เข้าสู่ระบบ)
# ==============================================================================

import re
import datetime
import jwt
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

# นำเข้าส่วนประกอบของ Database และ Model
from app.extensions import db
from app.models.user import User
from app.middleware.jwt_auth import get_jwt_secret
from app.utils.error_codes import (
    success_response,
    error_response,
    VALIDATION_ERROR,
    EMAIL_EXISTS,
    INVALID_CREDENTIALS,
    INTERNAL_SERVER_ERROR,
)

# สร้าง Flask Blueprint สำหรับกลุ่มเส้นทาง Authentication (/api/v1/...)
auth_bp = Blueprint("auth", __name__)


def is_valid_email(email: str) -> bool:
    """
    ฟังก์ชันตรวจสอบความถูกต้องของรูปแบบอีเมลด้วย Regular Expression (Regex)
    
    :param email: ข้อความอีเมลที่ต้องการตรวจสอบ
    :return: True หากรูปแบบถูกต้อง, False หากรูปแบบไม่ถูกต้อง
    """
    # กำหนดรูปแบบ Regex สำหรับตรวจสอบอีเมลมาตรฐาน
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/register
    เส้นทางสำหรับสมัครสมาชิกบัญชีผู้ใช้งานใหม่
    
    ขั้นตอนการทำงาน:
    1. รับข้อมูล JSON { "email": "...", "password": "..." } จาก Frontend
    2. ตรวจสอบความถูกต้องของข้อมูล (Validation): รูปแบบอีเมล และรหัสผ่านขั้นต่ำ 8 ตัวอักษร
    3. ตรวจสอบการซ้ำของอีเมล/ชื่อผู้ใช้ในฐานข้อมูล (Duplicate Check)
    4. เข้ารหัสแฮชรหัสผ่าน (Password Hashing) ก่อนบันทึกลง Database
    5. ส่งผลลัพธ์การลงทะเบียนสำเร็จกลับไปยัง Frontend (HTTP 201 Created)
    """
    # 1. ดึงข้อมูล JSON Payload จากคำขอ
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # 2. ตรวจสอบความถูกต้องของอีเมล (ห้ามว่าง และรูปแบบต้องถูกต้อง)
    if not email or not is_valid_email(email):
        return error_response(
            VALIDATION_ERROR, 
            "Invalid or missing email address", 
            400
        )

    # 3. ตรวจสอบความยาวรหัสผ่าน (ต้องมีความยาวอย่างน้อย 8 ตัวอักษรตามมาตรฐานความปลอดภัย)
    if not password or len(password) < 8:
        return error_response(
            VALIDATION_ERROR, 
            "Password must be at least 8 characters long", 
            400
        )

    # 4. ตรวจสอบว่าอีเมลนี้มีผู้ใช้งานลงทะเบียนไว้แล้วหรือไม่ (ป้องกันชื่อซ้ำ)
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        # หากมีอยู่แล้ว ให้ตอบกลับ Error Code: EMAIL_EXISTS พร้อม HTTP 409 Conflict
        return error_response(
            EMAIL_EXISTS, 
            "Email is already registered", 
            409
        )

    # 5. สร้าง User Object ใหม่ และทำการเข้ารหัสรหัสผ่านด้วย Werkzeug (PBKDF2/SHA256)
    new_user = User(
        email=email,
        password_hash=generate_password_hash(password),
    )

    # 6. เพิ่มข้อมูลลงใน Session ของ Database
    db.session.add(new_user)

    # 7. บันทึกข้อมูลลงใน SQLite Database
    try:
        db.session.commit()
    except IntegrityError:
        # กรณีเกิด Race Condition มีคนสมัครอีเมลเดียวกันพร้อมกัน
        db.session.rollback()
        return error_response(EMAIL_EXISTS, "Email is already registered", 409)
    except Exception as e:
        # ข้อผิดพลาดอื่นๆ ในการบันทึกฐานข้อมูล
        db.session.rollback()
        return error_response(INTERNAL_SERVER_ERROR, f"Database error: {str(e)}", 500)

    # 8. ตอบกลับผลลัพธ์การสมัครสำเร็จตามมาตรฐาน LUMA Contract (HTTP 201 Created)
    return success_response({
        "message": "Registration successful",
        "user": new_user.to_dict()
    }, status_code=201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/login
    เส้นทางสำหรับเข้าสู่ระบบเพื่อรับสิทธิ์ JWT Access Token
    
    ขั้นตอนการทำงาน:
    1. รับข้อมูล JSON { "email": "...", "password": "..." } จาก Frontend
    2. ค้นหาผู้ใช้จากอีเมลในฐานข้อมูล
    3. ตรวจสอบความถูกต้องของรหัสผ่านเทียบกับค่า Hash
    4. สร้าง JWT Token อายุ 24 ชั่วโมง โดยมี user_id และ email ฝังอยู่ใน Payload
    5. ส่ง Access Token และข้อมูลผู้ใช้กลับไปให้ Frontend บันทึกใน localStorage
    """
    # 1. ดึงข้อมูล JSON Payload
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # 2. ตรวจสอบว่ากรอกข้อมูลครบถ้วนหรือไม่
    if not email or not password:
        return error_response(
            VALIDATION_ERROR, 
            "Email and password are required", 
            400
        )

    # 3. ค้นหาผู้ใช้งานจากฐานข้อมูลด้วย Email
    target_user = User.query.filter_by(email=email).first()

    # 4. ตรวจสอบว่าพบผู้ใช้หรือไม่ และรหัสผ่านตรงกับ Hash หรือไม่
    if not target_user or not check_password_hash(target_user.password_hash, password):
        # หากไม่ถูกต้อง ให้ตอบกลับ HTTP 401 INVALID_CREDENTIALS
        return error_response(
            INVALID_CREDENTIALS, 
            "Invalid email or password", 
            401
        )

    # 5. สร้าง JWT Access Token ที่มีอายุ 24 ชั่วโมง (86,400 วินาที)
    try:
        expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        token_payload = {
            "user_id": target_user.id,
            "email": target_user.email,
            "exp": expiration_time
        }
        # เข้ารหัส Token ด้วย Secret Key และ Algorithm HS256
        token = jwt.encode(token_payload, get_jwt_secret(), algorithm="HS256")
    except Exception as e:
        return error_response(
            INTERNAL_SERVER_ERROR, 
            f"Failed to generate access token: {str(e)}", 
            500
        )

    # 6. ส่งผลลัพธ์การเข้าสู่ระบบสำเร็จพร้อม Token กลับไปยัง Frontend (HTTP 200 OK)
    return success_response({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "user": target_user.to_dict()
    }, status_code=200)