# ==============================================================================
# ชื่อไฟล์: backend/app/routes/sd.py
# หน้าที่: จัดการกระบวนการสร้างรูปภาพด้วย AI (Stable Diffusion), การประมาณเวลา (Time Estimation), 
#         และการให้บริการสตรีมไฟล์รูปภาพพร้อมระบบป้องกันการข้ามสิทธิ์ (IDOR Protection)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Generate (สร้างภาพ), หน้า Result (ดูผลลัพธ์), หน้า Home (ดึงโมเดล)
# ==============================================================================

import json
import base64
from io import BytesIO
from flask import Blueprint, request, send_file

# นำเข้าองค์ประกอบของ Database, Models, และ Middleware
from app.extensions import db
from app.models.user import User
from app.models.generation import Generation
from app.middleware.jwt_auth import token_required
from app.services.ai_client import (
    AIServerBusyException,
    AIServerTimeoutException,
    AIServerErrorException,
    generate_sd_image,
    fetch_available_models,
    calculate_estimated_time,
)
from app.utils.error_codes import (
    success_response,
    error_response,
    VALIDATION_ERROR,
    GENERATION_NOT_FOUND,
    IMAGE_NOT_FOUND,
    GENERATION_FAILED,
    AI_SERVER_ERROR,
    AI_SERVER_BUSY,
    AI_SERVER_TIMEOUT,
    UNAUTHORIZED,
)

# สร้าง Flask Blueprint สำหรับกลุ่มเส้นทาง Stable Diffusion (/api/v1/...)
sd_bp = Blueprint("sd", __name__)


@sd_bp.route("/models", methods=["GET", "OPTIONS"])
def get_models():
    """
    GET /api/v1/models
    ดึงรายชื่อโมเดล Checkpoints ทั้งหมดจาก Stable Diffusion AI Server
    เพื่อให้ Frontend นำไปแสดงใน Dropdown สำหรับเลือกโมเดล
    """
    # รองรับ CORS Preflight Request
    if request.method == "OPTIONS":
        return "", 200

    try:
        # เรียก Service ดึงรายชื่อโมเดลจาก AI Server
        models_list = fetch_available_models()
        return success_response({"models": models_list}, status_code=200)
    except AIServerErrorException as exc:
        # กรณี AI Server ตอบกลับข้อผิดพลาด
        return error_response(AI_SERVER_ERROR, str(exc), 503)
    except Exception as exc:
        # ข้อผิดพลาดที่ไม่คาดคิด
        return error_response(AI_SERVER_ERROR, f"Unexpected error: {str(exc)}", 500)


@sd_bp.route("/estimate", methods=["GET", "POST"])
def estimate_time():
    """
    GET / POST /api/v1/estimate
    เส้นทางสำหรับคำนวณและส่งค่าเวลาโดยประมาณที่ต้องใช้ในการสร้างภาพ
    คำนวณจากความละเอียดภาพ (Width, Height), จำนวน Steps, และจำนวนคิวที่กำลังรอ
    """
    # ดึงค่าพารามิเตอร์จาก JSON หรือ Query Parameters
    if request.method == "POST":
        data = request.get_json() or {}
    else:
        data = request.args

    width = int(data.get("width", 512))
    height = int(data.get("height", 512))
    steps = int(data.get("steps", 20))

    # เรียกใช้ฟังก์ชันคำนวณเวลาโดยประมาณ
    estimate_result = calculate_estimated_time(width=width, height=height, steps=steps)

    # ส่งคืนผลลัพธ์การประเมินเวลา
    return success_response(estimate_result, status_code=200)


@sd_bp.route("/generate", methods=["POST"])
@token_required
def generate_image():
    """
    POST /api/v1/generate 🔒 (ต้องใช้ JWT Token)
    เส้นทางหลักสำหรับการสร้างรูปภาพจากข้อความ Prompt (รูปแบบที่ 1: Checkpoint Generation)
    
    ขั้นตอนการทำงาน:
    1. ตรวจสอบสิทธิ์ผู้ใช้จาก JWT Token
    2. ตรวจสอบความถูกต้องของพารามิเตอร์ทั้งหมด (Prompt, Size, Steps, Sampler)
    3. ส่งคำขอเข้าสู่ Concurrency Queue เพื่อประมวลผลบน AI Server อย่างปลอดภัย
    4. แปลงภาพ Base64 เป็น Binary และบันทึกลงฐานข้อมูล โดยผูกกับ user_id ของผู้ใช้ปัจจุบัน
    5. ส่งคืน generation_id, image_url, เวลาประเมิน และเวลาที่ใช้จริง
    """
    data = request.get_json() or {}

    # 1. ตรวจสอบว่าผู้ใช้งานนี้มีตัวตนในระบบจริง
    current_user = db.session.get(User, request.user_id)
    if not current_user:
        return error_response(UNAUTHORIZED, "User not found in system", 401)

    # 2. ตรวจสอบเงื่อนไขพารามิเตอร์ (Validation) ตามสัญญา LUMA Contract
    prompt = data.get("prompt", "").strip()
    if not prompt or len(prompt) > 2000:
        return error_response(
            VALIDATION_ERROR, 
            "Prompt is required and must not exceed 2000 characters", 
            400
        )

    negative_prompt = data.get("negative_prompt", "")
    if len(negative_prompt) > 2000:
        return error_response(
            VALIDATION_ERROR, 
            "Negative prompt must not exceed 2000 characters", 
            400
        )

    width = data.get("width", 512)
    height = data.get("height", 512)
    if width not in [512, 768, 1024] or height not in [512, 768, 1024]:
        return error_response(
            VALIDATION_ERROR, 
            "Width and Height must be 512, 768, or 1024", 
            400
        )

    steps = data.get("steps", 20)
    if not (1 <= steps <= 50):
        return error_response(
            VALIDATION_ERROR, 
            "Steps must be between 1 and 50", 
            400
        )

    cfg_scale = data.get("cfg_scale", 7.0)
    if not (1.0 <= cfg_scale <= 20.0):
        return error_response(
            VALIDATION_ERROR, 
            "CFG Scale must be between 1 and 20", 
            400
        )

    sampler = data.get("sampler") or data.get("sampler_name") or "Euler a"
    checkpoint = data.get("checkpoint", "")
    seed = data.get("seed", -1)

    try:
        # 3. ส่งคำสั่งไปยัง AI Server ผ่านระบบ Concurrency Queue
        base64_image, actual_duration, estimated_duration = generate_sd_image(data)

        # 4. ถอดรหัสข้อความ Base64 ให้เป็น Binary Bytes เพื่อจัดเก็บลงฐานข้อมูล
        image_bytes = base64.b64decode(base64_image)

        # 5. สร้างเรคคอร์ดใหม่ในตาราง generations (กำหนด category='sd_generate' สำหรับรูปแบบที่ 1)
        new_generation = Generation(
            user_id=request.user_id,             # 🔑 ผูกไอดีเจ้าของภาพจาก JWT Token
            category="sd_generate",               # 🏷️ รูปแบบที่ 1: สร้างจาก AI Checkpoint
            action_type="txt2img",                # ⚙️ ชนิดการทำงาน: Text-to-Image
            prompt=prompt,
            negative_prompt=negative_prompt,
            checkpoint=checkpoint,
            sampler=sampler,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
            params=json.dumps(data),              # บันทึกพารามิเตอร์ทั้งหมดในรูปแบบ JSON
            image_data=image_bytes,               # เก็บข้อมูลภาพ Binary ลง SQLite
        )

        # 6. เพิ่มข้อมูลและบันทึกลงใน Database
        db.session.add(new_generation)
        db.session.commit()

        # 7. ตอบกลับผลลัพธ์ตามมาตรฐาน LUMA Contract พร้อมเวลาประมาณและเวลาจริง
        return success_response({
            "generation_id": new_generation.id,
            "image_url": f"/api/v1/images/{new_generation.id}",
            "seed": new_generation.seed,
            "estimated_time_seconds": estimated_duration,
            "actual_time_seconds": actual_duration,
            "created_at": new_generation.created_at.isoformat() if new_generation.created_at else None,
        }, status_code=201)

    except AIServerBusyException as exc:
        db.session.rollback()
        return error_response(AI_SERVER_BUSY, str(exc), 409)
    except AIServerTimeoutException as exc:
        db.session.rollback()
        return error_response(AI_SERVER_TIMEOUT, str(exc), 504)
    except AIServerErrorException as exc:
        db.session.rollback()
        return error_response(AI_SERVER_ERROR, str(exc), 503)
    except Exception as e:
        db.session.rollback()
        return error_response(GENERATION_FAILED, f"Image generation failed: {str(e)}", 500)


@sd_bp.route("/images/<int:gen_id>", methods=["GET"])
@token_required
def stream_image(gen_id: int):
    """
    GET /api/v1/images/:gen_id 🔒 (ต้องใช้ JWT Token)
    เส้นทางสำหรับส่งไฟล์รูปภาพแบบไบนารี (Binary Stream, image/png) กลับไปแสดงผลบน Frontend
    
    🛡️ ระบบป้องกันการข้ามสิทธิ์และ IDOR (Anti-Hopping & Ownership Protection):
    - ค้นหารูปภาพโดยระบุทั้ง id และ user_id จาก Token เสมอ
    - หากผู้ใช้พยายามเปิดดูภาพของคนอื่น ระบบจะมองไม่เห็นภาพนั้น และตอบกลับ 404 ทันที
    """
    # 1. ค้นหารูปภาพโดยกรองเฉพาะภาพที่เป็นของผู้ใช้คนนี้เท่านั้น
    record = Generation.query.filter_by(
        id=gen_id, 
        user_id=request.user_id
    ).first()

    # 2. หากไม่พบภาพ หรือภาพนั้นไม่ใช่ของผู้ใช้คนนี้
    if not record:
        return error_response(
            GENERATION_NOT_FOUND, 
            "Image record not found or access denied", 
            404
        )

    # 3. หากข้อมูลรูปภาพในฐานข้อมูลว่างเปล่า
    if not record.image_data:
        return error_response(
            IMAGE_NOT_FOUND, 
            "Image binary data is missing in database", 
            404
        )

    # 4. ส่งข้อมูลรูปภาพ Binary กลับไปในรูปแบบ Content-Type: image/png
    return send_file(
        BytesIO(record.image_data),
        mimetype="image/png",
        as_attachment=False,
        download_name=f"luma_image_{gen_id}.png"
    )