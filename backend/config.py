import os
from datetime import timedelta


class Config:
    """
    รวมค่า config ทั้งหมดไว้ที่เดียว เพื่อให้ app factory (app/__init__.py)
    เรียกใช้ผ่าน app.config.from_object(Config) จุดเดียว แทนที่จะกระจาย
    os.environ.get(...) ไปทั่วโค้ด — ถ้าอนาคตต้องมี TestConfig/ProdConfig
    ก็แค่สร้าง subclass ใหม่แล้ว override ค่าที่ต่างกัน
    """

    # spec ข้อ 4: secret ต้องอ่านจาก .env ห้าม hardcode/commit
    SECRET_KEY = os.environ.get("JWT_SECRET")
    if not SECRET_KEY:
        raise RuntimeError(
            "ไม่พบ JWT_SECRET ใน environment — คัดลอก .env.example เป็น .env "
            "แล้วใส่ค่า secret ก่อนรัน"
        )

    # spec ข้อ 4: JWT หมดอายุ 24 ชั่วโมง
    JWT_EXPIRES_IN = timedelta(hours=24)

    # spec ข้อ 6: CORS อนุญาตเฉพาะ origin ที่กำหนด
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://172.20.56.225:5173",
    ]

    # spec ข้อ 7: timeout ตอนเรียก AI Server
    AI_SERVER_TIMEOUT_SECONDS = 75

    # AI Server อยู่เครื่องอื่นในวง LAN -> อ่าน IP จาก .env เหมือน JWT_SECRET
    # เปลี่ยน IP เมื่อไหร่ แก้ที่ .env อย่างเดียว ไม่ต้องแตะโค้ด
    AI_SERVER_URL = os.environ.get("AI_SERVER_URL")
    if not AI_SERVER_URL:
        raise RuntimeError(
            "ไม่พบ AI_SERVER_URL ใน environment — เพิ่มบรรทัด "
            "AI_SERVER_URL=http://<ip>:<port> ใน .env ก่อนรัน"
        )