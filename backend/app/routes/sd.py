# app/routes/sd.py
import os
import uuid
import base64
from flask import Blueprint, request, send_file
from app.middleware.jwt_auth import token_required
from app.extensions import db
from app.models.generation import Generation  # Import SQLAlchemy Model
from app.services.ai_client import generate_sd_image, fetch_available_models
from app.utils.error_codes import (
    success_response, error_response, VALIDATION_ERROR, 
    GENERATION_NOT_FOUND, GENERATION_FAILED, AI_SERVER_ERROR
)

sd_bp = Blueprint("sd", __name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "app", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@sd_bp.route("/models", methods=["GET", "OPTIONS"])
def get_models():
    """GET /api/v1/models - return available Stable Diffusion models."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        return success_response({"models": fetch_available_models()})
    except Exception as exc:
        return error_response(AI_SERVER_ERROR, str(exc), 503)


@sd_bp.route("/generate", methods=["POST"])
@token_required
def generate_image():
    data = request.get_json() or {}
    
    # === [ส่วน Validation ตัวแประเดิมคงไว้ทั้งหมด] ===
    prompt = data.get("prompt", "").strip()
    if not prompt or len(prompt) > 2000:
        return error_response(VALIDATION_ERROR, "Prompt is required", 400)
    
    # ... Validation อื่นๆ (width, height, steps, cfg_scale, seed, sampler) ...

    try:
        # 1. ยิง API หา AI Server
        base64_img = generate_sd_image(data)

        # 2. บันทึกไฟล์ภาพลง Disk
        file_name = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        with open(file_path, "wb") as fh:
            fh.write(base64.b64decode(base64_img))

        # 3. บันทึกข้อมูลลง Database ผ่าน SQLAlchemy
        new_gen = Generation(
            user_id=request.user_id,  # 🔑 ผูกไอดีผู้สร้างจาก JWT Token
            prompt=prompt,
            negative_prompt=data.get("negative_prompt", ""),
            checkpoint=data.get("checkpoint", "v1-5-pruned.safetensors"),
            sampler=data.get("sampler"),
            width=data.get("width"),
            height=data.get("height"),
            steps=data.get("steps"),
            cfg_scale=data.get("cfg_scale"),
            seed=data.get("seed"),
            image_path=file_path
        )
        
        db.session.add(new_gen)
        db.session.commit() # บันทึกลงไฟล์ DB จริง

        return success_response({
            "id": new_gen.id,
            "prompt": new_gen.prompt,
            "image_url": f"/api/v1/images/{new_gen.id}"
        }, status_code=201)

    except Exception as e:
        db.session.rollback()
        return error_response(GENERATION_FAILED, f"Processing failed: {str(e)}", 500)


@sd_bp.route("/images/<int:gen_id>", methods=["GET"])
@token_required
def stream_image(gen_id):
    """ดึงไฟล์ภาพ Binary จาก DB (ป้องกัน IDOR)"""
    record = Generation.query.filter_by(id=gen_id, user_id=request.user_id).first()

    if not record:
        return error_response(GENERATION_NOT_FOUND, "Image not found or unauthorized", 404)

    if not os.path.exists(record.image_path):
        return error_response(GENERATION_NOT_FOUND, "File on disk not found", 404)

    return send_file(record.image_path, mimetype="image/png")