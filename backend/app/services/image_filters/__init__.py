# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/__init__.py
# หน้าที่: รวบรวม Blueprint และ Service สำหรับ Edge Image Processing ทั้งหมด
# ==============================================================================

from app.services.image_filters.routes import process_bp
from app.services.image_filters.cartoonize import cartoonize
from app.services.image_filters.tilt_shift import tilt_shift
from app.services.image_filters.hdr_enhancer import hdr_enhancer
from app.services.image_filters.spot_blur import spot_blur
from app.services.image_filters.remove_bg import remove_background
from app.services.image_filters.gesture import (
    recognize_gesture,
    recognize_gesture_frame,
    close_gesture_session,
)

__all__ = [
    "process_bp",
    "cartoonize",
    "tilt_shift",
    "hdr_enhancer",
    "spot_blur",
    "remove_background",
    "recognize_gesture",
    "recognize_gesture_frame",
    "close_gesture_session",
]
