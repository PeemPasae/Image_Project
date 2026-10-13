# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/routes.py
# หมายเหตุ: ย้ายไปที่ backend/app/routes/process.py ตามโครงสร้าง Clean Architecture
# ไฟล์นี้คงไว้เพื่อรองรับ Backward Compatibility สำหรับโค้ดที่ยัง import จากที่เดิม
# ==============================================================================

from app.routes.process import *  # noqa: F401, F403
from app.routes.process import process_bp

__all__ = ["process_bp"]
