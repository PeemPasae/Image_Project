# ==============================================================================
# ชื่อไฟล์: backend/app/routes/process.py
# หน้าที่: เส้นทาง API สำหรับประมวลผลรูปภาพด้วย OpenCV และ MediaPipe (Image Processor)
# เกี่ยวข้องกับหน้าเว็บ: Image Processor, Spot Blur, Hand Gesture, Remove Background,
#                      Cartoonize, Tilt-Shift, HDR Enhancer
# ==============================================================================

import json
import re
import cv2
from flask import Blueprint, request

from app.middleware.jwt_auth import token_required
from app.services.image_filters import (
    spot_blur,
    recognize_gesture,
    remove_background,
    cartoonize,
    tilt_shift,
    hdr_enhancer,
)
from app.utils.error_codes import (
    error_response,
    success_response,
    VALIDATION_ERROR,
    MODEL_UNAVAILABLE,
    GENERATION_FAILED,
)
from app.utils.image_helpers import extract_uploaded_image, send_image_png

process_bp = Blueprint("process", __name__)

GESTURE_PARAMS_ERROR = "num_hands must be an integer 1-4, min_confidence must be a number 0.1-1.0"
MODEL_ERROR = "Gesture model could not be downloaded"
HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_STROKES = 200
MAX_POINTS = 5000


def _is_num(val):
    """ตรวจสอบว่าเป็นตัวเลขจริง (ไม่นับ boolean)"""
    return type(val) in (int, float)


def _valid_rect(rect):
    """ตรวจสอบความถูกต้องของ bounding rect: [x, y, w, h] ที่ w, h > 0"""
    return rect is None or (
        isinstance(rect, list) and len(rect) == 4
        and all(_is_num(v) for v in rect)
        and rect[2] > 0 and rect[3] > 0
    )


def _valid_strokes(strokes):
    """ตรวจสอบความถูกต้องของเส้นแปรง (Brush Strokes)"""
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


# ==============================================================================
# 1. Spot Blur
# ==============================================================================
@process_bp.route("/process/spot-blur", methods=["POST"])
@token_required
def process_spot_blur():
    """POST /api/v1/process/spot-blur 🔒 เบลอเฉพาะจุดตามวงกลม แล้วส่งกลับเป็น PNG"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        circles = json.loads(form.get("circles", ""))
        strength = int(form.get("strength", ""))
    except (ValueError, TypeError):
        circles, strength = None, 0
    soft = form.get("soft", "true")

    valid = (
        isinstance(circles, list) and len(circles) > 0
        and all(
            isinstance(c, list) and len(c) == 3
            and all(_is_num(v) for v in c)
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

    result = spot_blur(img, circles, strength=strength, soft=(soft == "true"))
    return send_image_png(result)


# ==============================================================================
# 2. Hand Gesture Recognition
# ==============================================================================
@process_bp.route("/process/gesture", methods=["POST"])
@token_required
def process_gesture():
    """POST /api/v1/process/gesture 🔒 จดจำท่ามือจากรูปนิ่ง ส่งผลกลับเป็น JSON"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        num_hands = int(form.get("num_hands", "2"))
        min_confidence = float(form.get("min_confidence", "0.5"))
    except (ValueError, TypeError):
        return error_response(VALIDATION_ERROR, GESTURE_PARAMS_ERROR, 400)

    if not (1 <= num_hands <= 4 and 0.1 <= min_confidence <= 1.0):
        return error_response(VALIDATION_ERROR, GESTURE_PARAMS_ERROR, 400)

    try:
        result = recognize_gesture(img, num_hands, min_confidence)
    except OSError:
        return error_response(MODEL_UNAVAILABLE, MODEL_ERROR, 503)

    return success_response(result)


# ==============================================================================
# 3. Remove Background
# ==============================================================================
@process_bp.route("/process/remove-bg", methods=["POST"])
@token_required
def process_remove_bg():
    """POST /api/v1/process/remove-bg 🔒 ลบพื้นหลัง (AI อัตโนมัติ / ลากกรอบ / แปรง) แล้วส่งกลับเป็น PNG"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        rect = json.loads(form["rect"]) if form.get("rect") else None
        strokes = json.loads(form["strokes"]) if form.get("strokes") else []
    except (ValueError, TypeError):
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
    if bg != "transparent" and not HEX_COLOR_REGEX.match(bg):
        return error_response(VALIDATION_ERROR, 'bg must be "transparent" or a hex color like "#FFFFFF"', 400)

    color = None if bg == "transparent" else tuple(int(bg[i:i + 2], 16) for i in (5, 3, 1))
    try:
        result = remove_background(img, rect=rect, strokes=strokes, use_ai=(use_ai == "true"), bg_color=color)
    except OSError:
        return error_response(MODEL_UNAVAILABLE, "Background model could not be downloaded", 503)
    except cv2.error:
        return error_response(GENERATION_FAILED, "Background removal failed", 500)

    return send_image_png(result)


# ==============================================================================
# 4. Cartoonize Filter
# ==============================================================================
@process_bp.route("/process/cartoonize", methods=["POST"])
@token_required
def process_cartoonize():
    """POST /api/v1/process/cartoonize 🔒 แปลงภาพถ่ายเป็นสไตล์การ์ตูน/อนิเมะ แล้วส่งกลับเป็น PNG"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        num_colors = int(form.get("num_colors", 8))
        line_thickness = int(form.get("line_thickness", 2))
        smoothness = int(form.get("smoothness", 5))
    except (ValueError, TypeError):
        return error_response(VALIDATION_ERROR, "Parameters num_colors, line_thickness, and smoothness must be integers", 400)

    if not (2 <= num_colors <= 32 and 1 <= line_thickness <= 5 and 1 <= smoothness <= 10):
        return error_response(
            VALIDATION_ERROR,
            "num_colors must be 2-32, line_thickness must be 1-5, smoothness must be 1-10",
            400,
        )

    try:
        result = cartoonize(img, num_colors=num_colors, line_thickness=line_thickness, smoothness=smoothness)
    except Exception as e:
        return error_response(GENERATION_FAILED, f"Cartoonize processing failed: {str(e)}", 500)

    return send_image_png(result)


# ==============================================================================
# 5. Tilt-Shift Filter
# ==============================================================================
@process_bp.route("/process/tilt-shift", methods=["POST"])
@token_required
def process_tilt_shift():
    """POST /api/v1/process/tilt-shift 🔒 แปลงภาพถ่ายเป็นเอฟเฟกต์โมเดลจำลอง แล้วส่งกลับเป็น PNG"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        focus_position = float(form.get("focus_position", 0.5))
        focus_width = float(form.get("focus_width", 0.2))
        blur_strength = int(form.get("blur_strength", 15))
        saturation_boost = float(form.get("saturation_boost", 1.4))
        contrast_boost = float(form.get("contrast_boost", 1.2))
    except (ValueError, TypeError):
        return error_response(VALIDATION_ERROR, "Invalid numeric parameters for tilt-shift", 400)

    valid = (
        0.0 <= focus_position <= 1.0
        and 0.05 <= focus_width <= 0.8
        and 1 <= blur_strength <= 30
        and 1.0 <= saturation_boost <= 2.5
        and 1.0 <= contrast_boost <= 2.0
    )
    if not valid:
        return error_response(
            VALIDATION_ERROR,
            "focus_position must be 0.0-1.0, focus_width 0.05-0.8, blur_strength 1-30, "
            "saturation_boost 1.0-2.5, contrast_boost 1.0-2.0",
            400,
        )

    try:
        result = tilt_shift(
            img,
            focus_position=focus_position,
            focus_width=focus_width,
            blur_strength=blur_strength,
            saturation_boost=saturation_boost,
            contrast_boost=contrast_boost,
        )
    except Exception as e:
        return error_response(GENERATION_FAILED, f"Tilt-shift processing failed: {str(e)}", 500)

    return send_image_png(result)


# ==============================================================================
# 6. HDR Enhancer
# ==============================================================================
@process_bp.route("/process/hdr-enhancer", methods=["POST"])
@token_required
def process_hdr_enhancer():
    """POST /api/v1/process/hdr-enhancer 🔒 เพิ่มมิติและความคมชัดสไตล์ HDR แล้วส่งกลับเป็น PNG"""
    img, err = extract_uploaded_image(request.files.get("image"))
    if err:
        return err

    form = request.form
    try:
        clahe_clip_limit = float(form.get("clahe_clip_limit", 3.0))
        clahe_grid_size = int(form.get("clahe_grid_size", 8))
        detail_strength = float(form.get("detail_strength", 1.5))
    except (ValueError, TypeError):
        return error_response(VALIDATION_ERROR, "Invalid numeric parameters for hdr-enhancer", 400)

    color_balance = form.get("color_balance", "true").lower() in ("true", "1", "yes")

    valid = (
        1.0 <= clahe_clip_limit <= 5.0
        and 2 <= clahe_grid_size <= 16
        and 0.0 <= detail_strength <= 3.0
    )
    if not valid:
        return error_response(
            VALIDATION_ERROR,
            "clahe_clip_limit must be 1.0-5.0, clahe_grid_size 2-16, detail_strength 0.0-3.0",
            400,
        )

    try:
        result = hdr_enhancer(
            img,
            clahe_clip_limit=clahe_clip_limit,
            clahe_grid_size=clahe_grid_size,
            detail_strength=detail_strength,
            color_balance=color_balance,
        )
    except Exception as e:
        return error_response(GENERATION_FAILED, f"HDR enhancer processing failed: {str(e)}", 500)

    return send_image_png(result)
