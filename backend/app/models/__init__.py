# ==============================================================================
# ชื่อไฟล์: backend/app/models/__init__.py
# หน้าที่: รวบรวม Database Models หลักของระบบ Backend
# ==============================================================================

from app.models.user import User
from app.models.generation import Generation

__all__ = ["User", "Generation"]
