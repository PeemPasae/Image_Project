# ==============================================================================
# ชื่อไฟล์: backend/app/utils/error_codes.py
# หน้าที่: กำหนดมาตรฐาน Response Envelope และค่าคงที่ Error Codes ประจำระบบ
# เกี่ยวข้องกับหน้าเว็บ: ทุกหน้าเว็บที่ติดต่อกับ API เพื่อให้ Frontend จัดการ Error และ Data ได้เป็นมาตรฐานเดียวกัน
# ==============================================================================

from flask import jsonify

# ==============================================================================
# นิยามค่าคงที่สำหรับ Error Codes ทั้งหมด 12 รูปแบบตามสเปก LUMA Dashboard v1.4
# ==============================================================================
VALIDATION_ERROR = "VALIDATION_ERROR"            # HTTP 400: ข้อมูลที่ส่งมาไม่ถูกต้องตามเงื่อนไข (Validation ไม่ผ่าน)
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"      # HTTP 401: อีเมลหรือรหัสผ่านไม่ถูกต้อง
UNAUTHORIZED = "UNAUTHORIZED"                    # HTTP 401: ไม่มีสิทธิ์เข้าถึง หรือ JWT Token ไม่ถูกต้อง/หมดอายุ
EMAIL_EXISTS = "EMAIL_EXISTS"                    # HTTP 409: อีเมลหรือชื่อผู้ใช้นี้ถูกลงทะเบียนในระบบแล้ว (ตรวจชื่อซ้ำ)
GENERATION_NOT_FOUND = "GENERATION_NOT_FOUND"    # HTTP 404: ไม่พบข้อมูลรายการสร้างภาพตาม :id ที่ระบุ
IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"              # HTTP 404: ไม่พบไฟล์ข้อมูลรูปภาพไบนารีในระบบ
AI_SERVER_BUSY = "AI_SERVER_BUSY"                # HTTP 409: AI Server กำลังติดงานอื่นอยู่และคิวเต็มเกินกำหนด
MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"          # HTTP 503: ไม่พบโมเดล/Checkpoint ที่ต้องการบน AI Server
AI_SERVER_ERROR = "AI_SERVER_ERROR"              # HTTP 502/503: เกิดข้อผิดพลาดฝั่ง AI Server หรือไม่สามารถเชื่อมต่อได้
AI_SERVER_TIMEOUT = "AI_SERVER_TIMEOUT"          # HTTP 504: AI Server ประมวลผลช้าเกินเวลาที่กำหนด (เกิน 75 วินาที)
GENERATION_FAILED = "GENERATION_FAILED"          # HTTP 500: กระบวนการสร้างหรือประมวลผลรูปภาพล้มเหลว
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # HTTP 500: เกิดข้อผิดพลาดที่ไม่คาดคิดภายในระบบ Backend
UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"  # HTTP 415: ไฟล์ที่อัปโหลดไม่ใช่ .jpg / .jpeg / .png / .webp
INVALID_IMAGE = "INVALID_IMAGE"                  # HTTP 400: ไฟล์รูปภาพเสียหาย ถอดรหัส (decode) ไม่ได้


def success_response(data=None, status_code: int = 200):
    """
    ฟังก์ชันสำหรับสร้าง JSON Response กรณีที่ API ทำงานสำเร็จ
    ห่อข้อมูลให้อยู่ในโครงสร้างมาตรฐาน LUMA Envelope:
    {
        "success": true,
        "data": { ... }
    }
    
    :param data: ข้อมูล Dictionary หรือ List ที่ต้องการส่งกลับไปให้ Frontend
    :param status_code: HTTP Status Code (ค่าเริ่มต้นคือ 200 OK หรือ 201 Created)
    :return: Flask JSON Response Object พร้อมระบุ Status Code
    """
    # ตรวจสอบหากไม่มีการส่ง data มา ให้ใช้ Dictionary ว่างเป็นค่าเริ่มต้น
    payload = {
        "success": True,
        "data": data if data is not None else {}
    }
    # แปลงเป็น JSON และส่งกลับพร้อม HTTP Status Code
    return jsonify(payload), status_code


def error_response(code: str, message: str, status_code: int):
    """
    ฟังก์ชันสำหรับสร้าง JSON Response กรณีที่เกิดข้อผิดพลาดในการทำงาน
    ห่อข้อมูลให้อยู่ในโครงสร้างมาตรฐาน LUMA Envelope:
    {
        "success": false,
        "error": {
            "code": "...",
            "message": "..."
        }
    }
    
    :param code: รหัสข้อผิดพลาด เช่น VALIDATION_ERROR, UNAUTHORIZED, EMAIL_EXISTS
    :param message: ข้อความภาษาอังกฤษอธิบายสาเหตุของข้อผิดพลาดเพื่อให้ Frontend นำไปแสดงผล
    :param status_code: HTTP Status Code เช่น 400, 401, 404, 409, 500
    :return: Flask JSON Response Object พร้อมระบุ Status Code
    """
    # ประกอบโครงสร้าง Error Response ให้ตรงตามสัญญา API Contract
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    # แปลงเป็น JSON และส่งกลับพร้อม HTTP Status Code
    return jsonify(payload), status_code