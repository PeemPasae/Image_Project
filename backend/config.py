import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET")
    if not SECRET_KEY:
        raise RuntimeError(
            "ไม่พบ JWT_SECRET ใน environment — คัดลอก .env.example เป็น .env "
            "แล้วใส่ค่า secret ก่อนรัน"
        )

    JWT_EXPIRES_IN = timedelta(hours=24)

    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://192.168.1.10:5173",
    ]

    AI_SERVER_TIMEOUT_SECONDS = 75


