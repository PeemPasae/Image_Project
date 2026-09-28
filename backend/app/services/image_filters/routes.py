# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/routes.py
# หน้าที่: เส้นทาง API สำหรับประมวลผลภาพด้วย OpenCV (Image Processor)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Image Processor (Spot Blur), หน้า Hand Gesture, หน้า Remove Background
# ==============================================================================

import json
import re
from io import BytesIO

import cv2
import numpy as np
from flask import Blueprint, request, send_file

from app.middleware.jwt_auth import token_required
from app.services.image_filters.spot_blur import spot_blur
from app.services.image_filters.gesture import (
    recognize_gesture, recognize_gesture_frame, close_gesture_session,
)
from app.services.image_filters.remove_bg import remove_background
from app.utils.error_codes import (
    error_response, success_response,
    VALIDATION_ERROR, UNSUPPORTED_FILE_TYPE, INVALID_IMAGE, MODEL_UNAVAILABLE, GENERATION_FAILED,
)

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


# ==============================================================================
# Hand Gesture
# ==============================================================================

GESTURE_PARAMS_ERROR = "num_hands must be an integer 1-4, min_confidence must be a number 0.1-1.0"
MODEL_ERROR = "Gesture model could not be downloaded"


def _read_gesture_params(form):
    """อ่าน num_hands (1-4) และ min_confidence (0.1-1.0) ไม่ส่งมาใช้ค่าเริ่มต้น ค่าผิดคืน None"""
    try:
        num_hands = int(form.get("num_hands", "2"))
        min_confidence = float(form.get("min_confidence", "0.5"))
    except ValueError:
        return None
    if not (1 <= num_hands <= 4 and 0.1 <= min_confidence <= 1.0):
        return None
    return num_hands, min_confidence


def _decode_image(file):
    """แปลงไฟล์ที่อัปโหลดเป็นภาพ BGR ถ้า decode ไม่ได้คืน None"""
    data = file.read()
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) if data else None


@process_bp.route("/process/gesture", methods=["POST"])
@token_required
def process_gesture():
    """POST /api/v1/process/gesture 🔒 จดจำท่ามือจากรูปนิ่ง ส่งผลกลับเป็น JSON (ไม่บันทึก history)"""
    file = request.files.get("image")

    # 1. ไฟล์ภาพ
    if not file:
        return error_response(VALIDATION_ERROR, "image file is required", 400)
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return error_response(UNSUPPORTED_FILE_TYPE, "Only .jpg, .jpeg, .png, .webp are supported", 415)

    # 2. พารามิเตอร์
    params = _read_gesture_params(request.form)
    if params is None:
        return error_response(VALIDATION_ERROR, GESTURE_PARAMS_ERROR, 400)

    # 3. decode ภาพ
    img = _decode_image(file)
    if img is None:
        return error_response(INVALID_IMAGE, "Unable to decode the uploaded image", 400)

    # 4. จดจำท่ามือ (ครั้งแรกอาจช้าเพราะต้องดาวน์โหลดหรือโหลดโมเดล)
    try:
        result = recognize_gesture(img, *params)
    except OSError:
        return error_response(MODEL_UNAVAILABLE, MODEL_ERROR, 503)

    return success_response(result)


@process_bp.route("/process/gesture/frame", methods=["POST"])
@token_required
def process_gesture_frame():
    """POST /api/v1/process/gesture/frame 🔒 จดจำท่ามือจากเฟรม webcam (เรียกซ้ำหลายครั้งต่อวินาที)"""
    file = request.files.get("image")

    # 1. เฟรมภาพ (มาจาก canvas.toBlob ของหน้าเว็บ จึงไม่ตรวจนามสกุลไฟล์ ใช้ decode ตัดสินแทน)
    if not file:
        return error_response(VALIDATION_ERROR, "image frame is required", 400)

    # 2. พารามิเตอร์
    params = _read_gesture_params(request.form)
    if params is None:
        return error_response(VALIDATION_ERROR, GESTURE_PARAMS_ERROR, 400)

    # 3. decode เฟรม
    img = _decode_image(file)
    if img is None:
        return error_response(INVALID_IMAGE, "Unable to decode the frame", 400)

    # 4. จดจำท่ามือด้วย recognizer ของ user คนนี้ (แยกกันต่อคน)
    try:
        result = recognize_gesture_frame(img, request.user_id, *params)
    except OSError:
        return error_response(MODEL_UNAVAILABLE, MODEL_ERROR, 503)

    return success_response(result)


@process_bp.route("/process/gesture/stop", methods=["POST"])
@token_required
def process_gesture_stop():
    """POST /api/v1/process/gesture/stop 🔒 ปิดกล้องแล้ว คืน recognizer ของ user นี้"""
    close_gesture_session(request.user_id)
    return success_response({"message": "Gesture session closed"})


# ==============================================================================
# Remove Background
# ==============================================================================

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_STROKES = 200      # กันคนส่งเส้นแปรงมาเยอะเกินจนเซิร์ฟเวอร์ช้า
MAX_POINTS = 5000


def _is_num(v):
    """ตัวเลขจริง ๆ (ไม่นับ True/False ที่ Python ถือว่าเป็น int)"""
    return type(v) in (int, float)


def _valid_rect(rect):
    """None หรือ [x, y, w, h] ที่ w, h > 0"""
    return rect is None or (
        isinstance(rect, list) and len(rect) == 4
        and all(_is_num(v) for v in rect)
        and rect[2] > 0 and rect[3] > 0
    )


def _valid_strokes(strokes):
    """[{"type": "keep"/"remove", "r": 1-500, "points": [[x, y], ...]}, ...]"""
    return (
        isinstance(strokes, list) and len(strokes) <= MAX_STROKES
        and all(
            isinstance(s, dict)
            and s.get("type") in ("keep", "remove")
            and _is_num(s.get("r")) and 1 <= s["r"] <= 500
            and isinstance(s.get("points"), list) and len(s["points"]) > 0
            and all(isinstance(p, list) and len(p) == 2 and all(_is_num(v) for v in p) for p in s["points"])
            for s in strokes
        )
        and sum(len(s["points"]) for s in strokes) <= MAX_POINTS
    )


@process_bp.route("/process/remove-bg", methods=["POST"])
@token_required
def process_remove_bg():
    """POST /api/v1/process/remove-bg 🔒 ลบพื้นหลัง (AI อัตโนมัติ / ลากกรอบ / แปรงเก็บ-ลบ) แล้วส่งกลับเป็น PNG"""
    file = request.files.get("image")
    form = request.form

    # 1. ไฟล์ภาพ
    if not file:
        return error_response(VALIDATION_ERROR, "image file is required", 400)
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return error_response(UNSUPPORTED_FILE_TYPE, "Only .jpg, .jpeg, .png, .webp are supported", 415)

    # 2. พารามิเตอร์ (ไม่ส่งมา = ใช้ AI อัตโนมัติ + พื้นโปร่งใส)
    #    rect    = "[x, y, w, h]"  หน่วย pixel ของรูปจริง
    #    strokes = '[{"type": "keep", "r": 12, "points": [[x, y], ...]}, ...]'
    try:
        rect = json.loads(form["rect"]) if form.get("rect") else None
        strokes = json.loads(form["strokes"]) if form.get("strokes") else []
    except ValueError:
        rect = strokes = "invalid"
    use_ai = form.get("use_ai", "true")
    bg = form.get("bg", "transparent")

    if not _valid_rect(rect):
        return error_response(VALIDATION_ERROR, "rect must be a JSON array [x, y, width, height] with width, height > 0", 400)
    if not _valid_strokes(strokes):
        return error_response(
            VALIDATION_ERROR,
            f'strokes must be a JSON array (max {MAX_STROKES} strokes, {MAX_POINTS} points) of '
            '{"type": "keep" or "remove", "r": 1-500, "points": [[x, y], ...]}',
            400,
        )
    if use_ai not in ("true", "false"):
        return error_response(VALIDATION_ERROR, 'use_ai must be "true" or "false"', 400)
    if use_ai == "false" and rect is None:
        return error_response(VALIDATION_ERROR, "rect is required when use_ai is false", 400)
    if bg != "transparent" and not HEX_COLOR.match(bg):
        return error_response(VALIDATION_ERROR, 'bg must be "transparent" or a hex color like "#FFFFFF"', 400)

    # 3. decode ภาพ
    img = _decode_image(file)
    if img is None:
        return error_response(INVALID_IMAGE, "Unable to decode the uploaded image", 400)

    # 4. ลบพื้นหลัง แล้วส่งกลับเป็น PNG (โปร่งใส = มีช่อง alpha)
    color = None if bg == "transparent" else tuple(int(bg[i:i + 2], 16) for i in (5, 3, 1))   # #RRGGBB -> (B, G, R)
    try:
        result = remove_background(img, rect=rect, strokes=strokes, use_ai=(use_ai == "true"), bg_color=color)
    except OSError:
        return error_response(MODEL_UNAVAILABLE, "Background model could not be downloaded", 503)
    except cv2.error:
        return error_response(GENERATION_FAILED, "Background removal failed", 500)

    png = cv2.imencode(".png", result)[1].tobytes()
    return send_file(BytesIO(png), mimetype="image/png")