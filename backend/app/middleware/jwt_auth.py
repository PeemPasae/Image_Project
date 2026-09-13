# นำเข้าโมดูล os สำหรับอ่านค่าตัวแปรสภาพแวดล้อม (Environment Variables) จากระบบ
import os
# นำเข้า wraps จาก functools เพื่อใช้ในการสร้าง Decorator โดยไม่เสียข้อมูล Metadata ของฟังก์ชันเดิม
from functools import wraps
# นำเข้า request จาก flask เพื่อใช้ดึงข้อมูล Request Header ที่ส่งมาจาก Client
from flask import request
# นำเข้าไลบรารี PyJWT สำหรับใช้ถอดรหัสและตรวจสอบความถูกต้องของ JWT Token
import jwt
# นำเข้าตัวช่วยตอบกลับข้อผิดพลาด และ Error Code Constants
from app.utils.error_codes import error_response, UNAUTHORIZED, INTERNAL_SERVER_ERROR


def get_jwt_secret():
    """ฟังก์ชันสำหรับดึง Secret Key จากไฟล์ .env"""
    # อ่านค่า JWT_SECRET_KEY จากตัวแปรสภาพแวดล้อม
    secret = os.getenv("JWT_SECRET_KEY")
    # ถ้าหาค่า JWT_SECRET_KEY ไม่เจอ ให้หยุดการทำงานและโยน Exception ทันที
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not configured in .env")
    # คืนค่า secret key กลับไป
    return secret


def token_required(f):
    """Decorator สำหรับตรวจสอบความถูกต้องของ JWT Token ก่อนอนุญาตให้เข้าถึง Endpoint"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # ดึงค่าจาก HTTP Header ชื่อ Authorization
        auth_header = request.headers.get("Authorization")
        # ถ้าไม่มี Authorization header ส่งมาด้วย ให้ตอบกลับ error 401 UNAUTHORIZED
        if not auth_header:
            return error_response(UNAUTHORIZED, "Authorization header is missing", 401)

        # แยกข้อความใน Header ด้วยช่องว่าง (คาดหวังรูปแบบ: "Bearer <token>")
        parts = auth_header.split()
        # ถ้าความยาวไม่เท่ากับ 2 หรือคำแรกไม่ใช่ "Bearer" ให้ตอบกลับ error 401
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response(UNAUTHORIZED, "Invalid Authorization header format. Must be 'Bearer <token>'", 401)

        # แยกเอาเฉพาะตัวสตริง Token ที่อยู่ตำแหน่งที่ 2
        token = parts[1]
        try:
            # ถอดรหัสและตรวจสอบ Token ด้วย Secret Key และอัลกอริทึม HS256
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            # เมื่อ Token ถูกต้อง ให้นำ user_id จาก payload ไปฝากไว้ที่ request object เพื่อใช้ใน Endpoint ถัดไป
            request.user_id = payload.get("user_id")
            # ฝาก email ไว้ที่ request object ด้วย
            request.user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            # ถ้า Token หมดอายุ ให้ตอบกลับ error 401
            return error_response(UNAUTHORIZED, "Token has expired", 401)
        except jwt.InvalidTokenError:
            # ถ้า Token รูปแบบไม่ถูกต้อง หรือถูกแก้ไข ให้ตอบกลับ error 401
            return error_response(UNAUTHORIZED, "Invalid token", 401)
        except Exception as e:
            # หากเกิดข้อผิดพลาดอื่นๆ ให้ตอบกลับ error 500
            return error_response(INTERNAL_SERVER_ERROR, str(e), 500)

        # หากผ่านการตรวจสอบ ให้รันฟังก์ชันของ Endpoint ต่อไป
        return f(*args, **kwargs)

    # คืนค่าฟังก์ชันที่ถูกครอบไว้
    return decorated