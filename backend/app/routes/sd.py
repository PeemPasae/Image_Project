# นำเข้า os สำหรับจัดการที่อยู่ไฟล์ในระบบ
import os
# นำเข้า uuid สำหรับสุ่มชื่อไฟล์ภาพไม่ให้ซ้ำกัน
import uuid
# นำเข้า base64 สำหรับแปลง Base64 string กลับเป็น Binary
import base64
# นำเข้า Blueprint และ request
from flask import Blueprint, request
# นำเข้า Decorator เช็ก JWT Token
from app.middleware.jwt_auth import token_required
# นำเข้าฟังก์ชันเรียก AI Server และ Exception ต่างๆ
from app.services.ai_client import (
    fetch_available_models,
    generate_sd_image,
    AIServerBusyException,
    AIServerTimeoutException,
    AIServerErrorException
)
# นำเข้าฟังก์ชันตอบกลับ และ Error Codes
from app.utils.error_codes import (
    success_response,
    error_response,
    VALIDATION_ERROR,
    AI_SERVER_BUSY,
    AI_SERVER_TIMEOUT,
    AI_SERVER_ERROR,
    GENERATION_FAILED
)

# สร้าง Blueprint "sd"
sd_bp = Blueprint("sd", __name__)

# กำหนดโฟลเดอร์สำหรับเซฟไฟล์ภาพลง Disk
UPLOAD_FOLDER = os.path.join(os.getcwd(), "app", "uploads")
# ถ้ายังไม่มีโฟลเดอร์ให้สร้างขึ้นอัตโนมัติ
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# จำลองตาราง generations ใน DB
MOCK_GENERATIONS_DB = {}
MOCK_GEN_ID_COUNTER = 1


@sd_bp.route("/models", methods=["GET"])
def get_models():
    """GET /api/v1/models - ดึงรายการ Checkpoint/Model"""
    try:
        models = fetch_available_models()
        return success_response(models, status_code=200)
    except AIServerErrorException as e:
        return error_response(AI_SERVER_ERROR, str(e), 502)


@sd_bp.route("/generate", methods=["POST"])
@token_required
def generate_image():
    """POST /api/v1/generate 🔒 - สั่ง AI สร้างรูปภาพ"""
    data = request.get_json() or {}

    # === SERVER-SIDE VALIDATION ===
    prompt = data.get("prompt", "").strip()
    # prompt ต้องไม่ว่าง และความยาวไม่เกิน 2000 ตัวอักษร
    if not prompt or len(prompt) > 2000:
        return error_response(VALIDATION_ERROR, "Prompt is required and max 2000 characters", 400)

    width = data.get("width")
    height = data.get("height")
    # width/height ต้องเป็น integer 512, 768 หรือ 1024 เท่านั้น
    if width not in [512, 768, 1024] or height not in [512, 768, 1024]:
        return error_response(VALIDATION_ERROR, "Width and Height must be 512, 768, or 1024", 400)

    steps = data.get("steps")
    # steps ต้องเป็น integer 1-50
    if not isinstance(steps, int) or not (1 <= steps <= 50):
        return error_response(VALIDATION_ERROR, "Steps must be an integer between 1 and 50", 400)

    cfg_scale = data.get("cfg_scale")
    # cfg_scale ต้องเป็น float 1-20
    if not isinstance(cfg_scale, (int, float)) or not (1.0 <= cfg_scale <= 20.0):
        return error_response(VALIDATION_ERROR, "CFG Scale must be a float between 1 and 20", 400)

    seed = data.get("seed")
    # seed ต้องเป็น integer -1 หรือ 0 ถึง 2147483647
    if not isinstance(seed, int) or not (seed == -1 or 0 <= seed <= 2147483647):
        return error_response(VALIDATION_ERROR, "Seed must be -1 or between 0 and 2147483647", 400)

    sampler = data.get("sampler")
    allowed_samplers = ["DPM++ 2M Karras", "Euler a", "Euler"]
    # sampler ต้องเป็นตัวเลือกที่กำหนดไว้เท่านั้น
    if sampler not in allowed_samplers:
        return error_response(VALIDATION_ERROR, f"Sampler must be one of {allowed_samplers}", 400)

    # จัดเตรียม Payload ส่งหา AI Server
    ai_payload = {
        "prompt": prompt,
        "negative_prompt": data.get("negative_prompt", ""),
        "sampler_name": sampler,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "seed": seed
    }

    try:
        # ยิงไปยัง AI Server
        base64_img = generate_sd_image(ai_payload)

        # สุ่มชื่อไฟล์ภาพป้องกันชื่อซ้ำ
        file_name = f"{uuid.uuid4().hex}.png"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        # Decode Base64 เป็นไฟล์ PNG แล้วเซฟลง Local Disk
        with open(file_path, "wb") as fh:
            fh.write(base64.b64decode(base64_img))

        # บันทึกข้อมูลประวัติลง DB
        global MOCK_GEN_ID_COUNTER
        gen_id = MOCK_GEN_ID_COUNTER
        MOCK_GEN_ID_COUNTER += 1

        generation_record = {
            "id": gen_id,
            "user_id": request.user_id,
            "prompt": prompt,
            "negative_prompt": data.get("negative_prompt", ""),
            "checkpoint": data.get("checkpoint", "v1-5-pruned.safetensors"),
            "sampler": sampler,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "image_path": file_path,
            "created_at": "2026-09-07T10:00:00Z"
        }
        MOCK_GENERATIONS_DB[gen_id] = generation_record

        # ตอบกลับเฉพาะ image_url ห้ามฝัง Base64 ตรงๆ ใน response
        return success_response({
            "id": gen_id,
            "prompt": prompt,
            "image_url": f"/api/v1/images/{gen_id}"
        }, status_code=201)

    except AIServerBusyException as e:
        return error_response(AI_SERVER_BUSY, str(e), 409)
    except AIServerTimeoutException as e:
        return error_response(AI_SERVER_TIMEOUT, str(e), 504)
    except AIServerErrorException as e:
        return error_response(AI_SERVER_ERROR, str(e), 502)
    except Exception as e:
        return error_response(GENERATION_FAILED, f"Image processing failed: {str(e)}", 500)