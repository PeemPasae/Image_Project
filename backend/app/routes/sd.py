# ==============================================================================
# ชื่อไฟล์: backend/app/routes/sd.py
# หน้าที่: จัดการกระบวนการสร้างรูปภาพด้วย AI (Stable Diffusion), การประมาณเวลา (Time Estimation), 
#         และการให้บริการสตรีมไฟล์รูปภาพพร้อมระบบป้องกันการข้ามสิทธิ์ (IDOR Protection)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Generate (สร้างภาพ), หน้า Result (ดูผลลัพธ์), หน้า Home (ดึงโมเดล)
# ==============================================================================

import os
import json
import base64
from io import BytesIO
from flask import Blueprint, request, send_file, current_app

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

sd_bp = Blueprint("sd", __name__)


@sd_bp.route("/models", methods=["GET", "OPTIONS"])
def get_models():
    """
    GET /api/v1/models
    ดึงรายชื่อโมเดล Checkpoints ทั้งหมดจาก Stable Diffusion AI Server
    """
    if request.method == "OPTIONS":
        return "", 200

    try:
        models_list = fetch_available_models()
        return success_response({"models": models_list}, status_code=200)
    except AIServerTimeoutException as exc:
        return error_response(AI_SERVER_TIMEOUT, str(exc), 504)
    except AIServerErrorException as exc:
        return error_response(AI_SERVER_ERROR, str(exc), 503)
    except Exception as exc:
        return error_response(AI_SERVER_ERROR, f"Unexpected error: {str(exc)}", 500)


@sd_bp.route("/estimate", methods=["GET", "POST"])
def estimate_time():
    """
    GET / POST /api/v1/estimate
    เส้นทางสำหรับคำนวณและส่งค่าเวลาโดยประมาณที่ต้องใช้ในการสร้างภาพ
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = request.args

    try:
        width = int(data.get("width", 512))
        height = int(data.get("height", 512))
        steps = int(data.get("steps", 20))
    except (ValueError, TypeError):
        width, height, steps = 512, 512, 20

    estimate_result = calculate_estimated_time(width=width, height=height, steps=steps)
    return success_response(estimate_result, status_code=200)


@sd_bp.route("/generate", methods=["POST"])
@token_required
def generate_image():
    """
    POST /api/v1/generate 🔒 (ต้องใช้ JWT Token)
    สร้างรูปภาพจากข้อความ Prompt ผ่าน Stable Diffusion AI Server
    """
    data = request.get_json() or {}

    # 1. ตรวจสอบว่าผู้ใช้งานมีตัวตนในระบบจริง
    current_user = db.session.get(User, request.user_id)
    if not current_user:
        return error_response(UNAUTHORIZED, "User not found in system", 401)

    # 2. ตรวจสอบเงื่อนไขพารามิเตอร์ (Validation)
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

    sampler = data.get("sampler") or data.get("sampler_name") or "Euler a"
    checkpoint = data.get("checkpoint", "")

    clean_payload = dict(data)
    clean_payload.update({
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "sampler": sampler,
        "checkpoint": checkpoint,
        "seed": seed,
    })

    try:
        # 3. ส่งคำสั่งไปยัง AI Server ผ่าน Concurrency Queue
        base64_image, actual_duration, estimated_duration = generate_sd_image(clean_payload)

        # 4. ถอดรหัสรูปภาพ Base64 เป็น Binary
        image_bytes = base64.b64decode(base64_image)

        # 5. สร้างเรคคอร์ดใหม่ในตาราง generations
        new_generation = Generation(
            user_id=request.user_id,
            category="sd_generate",
            action_type="txt2img",
            prompt=prompt,
            negative_prompt=negative_prompt,
            checkpoint=checkpoint,
            sampler=sampler,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
            params=json.dumps(data),
            image_data=image_bytes,
        )

        db.session.add(new_generation)
        db.session.commit()

        # 6. บันทึกสำเนาลง Disk Storage เพื่อการเข้าถึงที่รวดเร็ว
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

        # 7. ตอบกลับผลลัพธ์
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
    สตรีมไฟล์รูปภาพไบนารี พร้อมป้องกันการข้ามสิทธิ์ผู้ใช้ (Anti-Hopping & IDOR Protection)
    """
    record = Generation.query.filter_by(
        id=gen_id, 
        user_id=request.user_id
    ).first()

    if not record:
        return error_response(
            GENERATION_NOT_FOUND, 
            "Image record not found or access denied", 
            404
        )

    # 1. สตรีมจาก Disk Storage หากมี
    if record.image_path and os.path.isfile(record.image_path):
        return send_file(
            record.image_path,
            mimetype="image/png",
            as_attachment=False,
            download_name=f"luma_image_{gen_id}.png"
        )

    # 2. หากไม่มีบน Disk ให้ดึงจาก Database BLOB
    if record.image_data:
        return send_file(
            BytesIO(record.image_data),
            mimetype="image/png",
            as_attachment=False,
            download_name=f"luma_image_{gen_id}.png"
        )

    return error_response(
        IMAGE_NOT_FOUND, 
        "Image binary data is missing in database or storage", 
        404
    )