# ==============================================================================
# ชื่อไฟล์: backend/app/middleware/jwt_auth.py
# หน้าที่: มิดเดิลแวร์สำหรับตรวจสอบความถูกต้องของ JWT Token และป้องกันการเข้าถึงโดยไม่ได้รับอนุญาต (Anti-Hopping)
# เกี่ยวข้องกับหน้าเว็บ: ทุกหน้าที่มีการป้องกันสิทธิ์ (Generate, History, Profile, Result, Image View)
# ==============================================================================

import os
from functools import wraps
from flask import request
import jwt

# นำเข้าฟังก์ชันตอบกลับข้อผิดพลาดและ Error Codes มาตรฐาน
from app.utils.error_codes import error_response, UNAUTHORIZED, INTERNAL_SERVER_ERROR


def get_jwt_secret() -> str:
    """
    ฟังก์ชันสำหรับดึง JWT Secret Key จากตัวแปรสภาพแวดล้อม (.env)
    หากไม่พบการตั้งค่าใน Environment จะใช้ค่าเริ่มต้นสำหรับพัฒนา
    
    :return: ข้อความ Secret Key สำหรับเข้ารหัส/ถอดรหัส Token
    """
    # ตรวจสอบตัวแปร JWT_SECRET_KEY หรือ JWT_SECRET จาก .env
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        # กำหนดค่าสำรองสำหรับใช้งานในสภาพแวดล้อม Development
        secret = "luma_default_jwt_secret_key_2026"
    return secret


def token_required(f):
    """
    Decorator สำหรับคุ้มครอง API Endpoints ที่ต้องผ่านการยืนยันตัวตน (Protected Routes)
    ทำหน้าที่:
    1. ตรวจสอบว่ามี Header 'Authorization: Bearer <token>' แนบมาหรือไม่
    2. ตรวจสอบลายเซ็นและความถูกต้องของ Token (HS256)
    3. ตรวจสอบอายุของ Token (ไม่เกิน 24 ชั่วโมง)
    4. สกัด 'user_id' และ 'email' จาก Token แล้วนำไปเก็บไว้ใน 'request.user_id' และ 'request.user_email'
    5. ป้องกันไม่ให้ผู้ใช้ที่ไม่ล็อกอิน หรือมี Token ไม่ถูกต้อง กระโดดเข้ามาเรียกใช้ API ได้
    
    :param f: ฟังก์ชัน Controller ของ Endpoint ที่ถูกตกแต่ง
    :return: ฟังก์ชันที่ผ่านการตรวจสอบความปลอดภัยแล้ว
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. ดึงค่า Header "Authorization" จากคำขอที่ส่งมาจาก Frontend
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # หากไม่มี Header ให้ตอบกลับ 401 UNAUTHORIZED ทันที
            return error_response(UNAUTHORIZED, "Authorization header is missing", 401)

        # 2. แยกข้อความใน Header ออกเป็นส่วน (คาดหวังรูปแบบ: "Bearer <token_string>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            # หากรูปแบบไม่ใช่ "Bearer <token>" ให้ปฏิเสธคำขอ
            return error_response(
                UNAUTHORIZED, 
                "Invalid Authorization header format. Must be 'Bearer <token>'", 
                401
            )

        # ดึงสตริง Token ออกมาใช้งาน
        token = parts[1]

        # 3. ถอดรหัสและตรวจสอบความถูกต้องของ Token
        try:
            # ตรวจสอบความถูกต้องด้วย Secret Key และ Algorithm HS256
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            
            # ดึง user_id และ email ออกมาจาก Payload
            request.user_id = payload.get("user_id")
            request.user_email = payload.get("email")

            # ตรวจสอบว่าใน Payload มี user_id หรือไม่
            if not request.user_id:
                return error_response(UNAUTHORIZED, "Token payload is missing user_id", 401)

        except jwt.ExpiredSignatureError:
            # กรณี Token หมดอายุ (เกิน 24 ชั่วโมง)
            return error_response(UNAUTHORIZED, "Token has expired, please log in again", 401)
        except jwt.InvalidTokenError:
            # กรณี Token ผิดรูปแบบ หรือถูกดัดแปลงแก้ไข
            return error_response(UNAUTHORIZED, "Invalid token signature", 401)
        except Exception as e:
            # กรณีเกิดข้อผิดพลาดอื่นๆ ที่ไม่คาดคิด
            return error_response(INTERNAL_SERVER_ERROR, f"Authentication error: {str(e)}", 500)

        # 4. เมื่อผ่านการตรวจสอบสิทธิ์ครบถ้วน ให้ส่งต่อไปยังฟังก์ชัน Route หลัก
        return f(*args, **kwargs)

    return decorated