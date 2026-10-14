# ==============================================================================
# ชื่อไฟล์: backend/app/routes/sd.py
# หน้าที่: จัดการกระบวนการสร้างรูปภาพด้วย AI (Stable Diffusion), การประมาณเวลา (Time Estimation), 
#         และการให้บริการสตรีมไฟล์รูปภาพพร้อมระบบป้องกันการข้ามสิทธิ์ (IDOR Protection)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Generate (สร้างภาพ), หน้า Result (ดูผลลัพธ์), หน้า Home (ดึงโมเดล)
# ==============================================================================

import os
import json
import base64
import random
from io import BytesIO
from flask import Blueprint, request, send_file, current_app

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
        # เรียก Service ดึงรายชื่อโมเดลจาก AI Server โดยตรง
        models_list = fetch_available_models()
        return success_response({"models": models_list}, status_code=200)
    except AIServerTimeoutException as exc:
        return error_response(AI_SERVER_TIMEOUT, str(exc), 504)
    except AIServerErrorException as exc:
        return error_response(AI_SERVER_ERROR, str(exc), 503)
    except Exception as exc:
        return error_response(AI_SERVER_ERROR, f"Unexpected error: {str(exc)}", 500)



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
    prompt = str(data.get("prompt") or "").strip()
    if not prompt or len(prompt) > 2000:
        return error_response(
            VALIDATION_ERROR, 
            "Prompt is required and must not exceed 2000 characters", 
            400
        )

    negative_prompt = str(data.get("negative_prompt") or "")
    if len(negative_prompt) > 2000:
        return error_response(
            VALIDATION_ERROR, 
            "Negative prompt must not exceed 2000 characters", 
            400
        )

    try:
        width = int(data.get("width", 512))
        height = int(data.get("height", 512))
        steps = int(data.get("steps", 20))
        cfg_scale = float(data.get("cfg_scale", 7.0))
        seed = int(data.get("seed", -1))
    except (ValueError, TypeError):
        return error_response(
            VALIDATION_ERROR, 
            "Invalid numeric parameters: width, height, steps, cfg_scale, and seed must be valid numbers", 
            400
        )

    if width not in [512, 768, 1024] or height not in [512, 768, 1024]:
        return error_response(
            VALIDATION_ERROR, 
            "Width and Height must be 512, 768, or 1024", 
            400
        )

    if not (1 <= steps <= 50):
        return error_response(
            VALIDATION_ERROR, 
            "Steps must be between 1 and 50", 
            400
        )

    if not (1.0 <= cfg_scale <= 20.0):
        return error_response(
            VALIDATION_ERROR, 
            "CFG Scale must be between 1 and 20", 
            400
        )

    # [แก้บัค] seed ต้องเป็น -1 (สุ่ม) หรือ 0 ถึง 2147483647 ตามกติกาที่ตกลงกัน
    # เดิมไม่ได้เช็ค seed ใหญ่เกินจะพังตอนบันทึก ทั้งที่ AI สร้างรูปเสร็จแล้ว (เสียเวลา GPU)
    if not (seed == -1 or 0 <= seed <= 2147483647):
        return error_response(
            VALIDATION_ERROR,
            "Seed must be -1 (random) or between 0 and 2147483647",
            400
        )

    # [แก้บัค] ถ้าผู้ใช้เลือกสุ่ม (-1) ให้ backend สุ่มเลขเองแล้วส่งเลขนั้นให้ AI
    # เดิมส่ง -1 ไปให้ AI สุ่ม เราเลยไม่รู้เลขจริง ประวัติเก็บได้แค่ -1 และสร้างรูปเดิมซ้ำไม่ได้
    if seed == -1:
        seed = random.randint(0, 2147483647)

    sampler = str(data.get("sampler") or data.get("sampler_name") or "Euler a")
    checkpoint = str(data.get("checkpoint") or "")

    # [แก้บัค] เก็บเฉพาะค่าที่ใช้จริง เดิมใช้ dict(data) ทำให้ใครส่งข้อมูลขยะมาก็ถูกเก็บลง database
    clean_payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "sampler": sampler,
        "checkpoint": checkpoint,
        "seed": seed,
    }

    try:
        # 3. ส่งคำสั่งไปยัง AI Server ผ่านระบบ Concurrency Queue
        base64_image, actual_duration, estimated_duration = generate_sd_image(clean_payload)

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
            params=json.dumps(clean_payload),     # บันทึกเฉพาะพารามิเตอร์ที่ใช้จริง (JSON)
            image_data=image_bytes,               # เก็บข้อมูลภาพ Binary ลง SQLite
        )

        # 6. เพิ่มข้อมูลและบันทึกลงใน Database
        db.session.add(new_generation)
        db.session.commit()

        # 6.1 บันทึกไฟล์ภาพลงใน Disk Storage (uploads/generations/{id}.png) เพื่อประสิทธิภาพการดึงข้อมูล
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        if upload_folder:
            gen_dir = os.path.join(upload_folder, "generations")
            os.makedirs(gen_dir, exist_ok=True)
            disk_path = os.path.join(gen_dir, f"{new_generation.id}.png")
            try:
                with open(disk_path, "wb") as img_file:
                    img_file.write(image_bytes)
                new_generation.image_path = disk_path
                db.session.commit()
            except Exception as io_err:
                current_app.logger.warning("Failed to save image to disk storage: %s", str(io_err))

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
    ⚡ ประสิทธิภาพสูง: สตรีมตรงจากไฟล์ Disk ก่อน หากไม่มีจึงดึงจาก Database BLOB
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

    # 3. หากมีไฟล์บน Disk Storage ให้ Stream ตรงจากไฟล์ (ใช้ OS sendfile เร็วกว่าและประหยัด RAM)
    if record.image_path and os.path.isfile(record.image_path):
        return send_file(
            record.image_path,
            mimetype="image/png",
            as_attachment=False,
            download_name=f"luma_image_{gen_id}.png"
        )

    # 4. หากไม่มีไฟล์บน Disk ให้ดึงข้อมูลสำรองจาก image_data ใน Database
    if record.image_data:
        return send_file(
            BytesIO(record.image_data),
            mimetype="image/png",
            as_attachment=False,
            download_name=f"luma_image_{gen_id}.png"
        )

    # 5. หากไม่มีทั้งสองแห่ง
    return error_response(
        IMAGE_NOT_FOUND, 
        "Image binary data is missing in database or storage", 
        404
    )


# ==============================================================================
# [UNUSED BY FRONTEND] ย้ายส่วนที่ Frontend ไม่ได้เรียกใช้มาไว้ด้านล่างสุด
# เผื่อต้องการนำกลับมาเปิดใช้งานในอนาคต (เพียงเอาเครื่องหมาย # ออก)
# ==============================================================================
# @sd_bp.route("/estimate", methods=["GET", "POST"])
# def estimate_time():
#     """
#     GET / POST /api/v1/estimate
#     เส้นทางสำหรับคำนวณและส่งค่าเวลาโดยประมาณที่ต้องใช้ในการสร้างภาพ
#     Frontend ไม่ได้เรียกใช้งาน (หน้า Generate เรียก /generate ตรงๆ)
#     """
#     if request.method == "POST":
#         data = request.get_json() or {}
#     else:
#         data = request.args
#     width = int(data.get("width", 512))
#     height = int(data.get("height", 512))
#     steps = int(data.get("steps", 20))
#     estimate_result = calculate_estimated_time(width=width, height=height, steps=steps)
#     return success_response(estimate_result, status_code=200)