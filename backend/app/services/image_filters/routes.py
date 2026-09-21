# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/routes.py
# หน้าที่: เส้นทาง API สำหรับประมวลผลภาพด้วย OpenCV (Image Processor)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Image Processor (เครื่องมือ Spot Blur)
# ==============================================================================

import json
from io import BytesIO

import cv2
import numpy as np
from flask import Blueprint, request, send_file

from app.middleware.jwt_auth import token_required
from app.services.image_filters.spot_blur import spot_blur
from app.utils.error_codes import error_response, VALIDATION_ERROR, UNSUPPORTED_FILE_TYPE, INVALID_IMAGE

process_bp = Blueprint("process", __name__)


@process_bp.route("/process/spot-blur", methods=["POST"])
@token_required
def process_spot_blur():
    """POST /api/v1/process/spot-blur 🔒 เบลอเฉพาะจุดตามวงกลม แล้วส่งกลับเป็น PNG"""
    file = request.files.get("image")
    form = request.form

    # 1. ไฟล์ภาพ
    if not file:
        return error_response(VALIDATION_ERROR, "image file is required", 400)
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return error_response(UNSUPPORTED_FILE_TYPE, "Only .jpg, .jpeg, .png, .webp are supported", 415)

    # 2. พารามิเตอร์: circles = [[x, y, r], ...], strength = 1-30, soft = "true"/"false"
    try:
        circles = json.loads(form.get("circles", ""))
        strength = int(form.get("strength", ""))
    except ValueError:
        circles, strength = None, 0
    soft = form.get("soft", "true")

    valid = (
        isinstance(circles, list) and len(circles) > 0
        and all(
            isinstance(c, list) and len(c) == 3
            and all(type(v) in (int, float) for v in c)
            and c[2] > 0
            for c in circles
        )
        and 1 <= strength <= 30
        and soft in ("true", "false")
    )
    if not valid:
        return error_response(
            VALIDATION_ERROR,
            "circles must be a non-empty JSON array of [x, y, radius], "
            'strength must be an integer 1-30, soft must be "true" or "false"',
            400,
        )

    # 3. decode ภาพ (IMREAD_COLOR ทำให้เป็น BGR 3 ช่องเสมอ)
    data = file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) if data else None
    if img is None:
        return error_response(INVALID_IMAGE, "Unable to decode the uploaded image", 400)

    # 4. เบลอ แล้วส่งกลับเป็น PNG
    result = spot_blur(img, circles, strength=strength, soft=(soft == "true"))
    png = cv2.imencode(".png", result)[1].tobytes()
    return send_file(BytesIO(png), mimetype="image/png")
