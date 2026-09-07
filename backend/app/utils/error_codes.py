# นำเข้า jsonify จาก flask เพื่อใช้แปลง dictionary ใน Python ให้เป็น JSON response กลับไปหา client
from flask import jsonify

# ==========================================
# นิยามค่าคงที่สำหรับ Error Codes ตามข้อกำหนด
# ==========================================
VALIDATION_ERROR = "VALIDATION_ERROR"            # 400 ข้อมูลที่ส่งมาไม่ถูกต้องตามกฎ
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"      # 401 อีเมลหรือรหัสผ่านไม่ถูกต้อง
UNAUTHORIZED = "UNAUTHORIZED"                    # 401 ไม่มีสิทธิ์เข้าถึง หรือ Token ไม่ถูกต้อง/หมดอายุ
EMAIL_EXISTS = "EMAIL_EXISTS"                    # 409 อีเมลนี้ถูกลงทะเบียนในระบบแล้ว
GENERATION_NOT_FOUND = "GENERATION_NOT_FOUND"    # 404 ไม่พบข้อมูลการสร้างรูปภาพ
IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"              # 404 ไม่พบไฟล์รูปภาพที่ระบุ
AI_SERVER_BUSY = "AI_SERVER_BUSY"                # 409 AI Server กำลังประมวลผล request อื่นอยู่
MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"          # 503 ไม่พบ Model/Checkpoint ที่ต้องการ
AI_SERVER_ERROR = "AI_SERVER_ERROR"              # 502/503 เกิดข้อผิดพลาดฝั่ง AI Server
AI_SERVER_TIMEOUT = "AI_SERVER_TIMEOUT"          # 504 AI Server ตอบสนองช้าเกินเวลาที่กำหนด (75 วินาที)
GENERATION_FAILED = "GENERATION_FAILED"          # 500 กระบวนการสร้างรูปภาพล้มเหลว
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # 500 เกิดข้อผิดพลาดภายในระบบ Backend


def success_response(data=None, status_code=200):
    """
    ฟังก์ชันสำหรับสร้าง Response กรณีทำงานสำเร็จ
    ห่อข้อมูลให้อยู่ในโครงสร้างมาตรฐาน: { "success": true, "data": {...} }
    """
    # ส่งคืน response ในรูปแบบ JSON พร้อมกำหนด HTTP status code (ค่าเริ่มต้นคือ 200)
    return jsonify({
        "success": True,                                # กำหนดสถานะสำเร็จเป็น True
        "data": data if data is not None else {}       # ใส่ข้อมูลผลลัพธ์ ถ้าไม่มีให้ส่ง dict ว่าง {}
    }), status_code


def error_response(code, message, status_code):
    """
    ฟังก์ชันสำหรับสร้าง Response กรณีเกิดข้อผิดพลาด
    ห่อข้อมูลให้อยู่ในโครงสร้างมาตรฐาน: { "success": false, "error": { "code": "...", "message": "..." } }
    """
    # ส่งคืน response ในรูปแบบ JSON พร้อมกำหนด HTTP status code ที่ระบุ
    return jsonify({
        "success": False,                              # กำหนดสถานะสำเร็จเป็น False
        "error": {                                     # วัตถุบรรจุรายละเอียดข้อผิดพลาด
            "code": code,                              # รหัสข้อผิดพลาด เช่น "VALIDATION_ERROR"
            "message": message                         # ข้อความอธิบายความล้มเหลว
        }
    }), status_code