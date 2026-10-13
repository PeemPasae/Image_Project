# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/__init__.py
# หน้าที่: รวบรวมและส่งออกอัลกอริทึมการประมวลผลรูปภาพ (Pure Image Processing Services)
# ==============================================================================

from app.services.image_filters.cartoonize import cartoonize
from app.services.image_filters.tilt_shift import tilt_shift
from app.services.image_filters.hdr_enhancer import hdr_enhancer
from app.services.image_filters.spot_blur import spot_blur
from app.services.image_filters.remove_bg import remove_background
from app.services.image_filters.gesture import recognize_gesture

__all__ = [
    "cartoonize",
    "tilt_shift",
    "hdr_enhancer",
    "spot_blur",
    "remove_background",
    "recognize_gesture",
]


def __getattr__(name):
    """Lazy import for backward-compatibility without circular dependency"""
    if name == "process_bp":
        from app.routes.process import process_bp
        return process_bp
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
