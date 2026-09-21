# ==============================================================================
# ชื่อไฟล์: backend/app/models/user.py
# หน้าที่: โมเดลตารางผู้ใช้งาน (users) สำหรับจัดการข้อมูลบัญชีผู้ใช้และระบบความปลอดภัย
# เกี่ยวข้องกับหน้าเว็บ: หน้า Register (สมัครสมาชิก), หน้า Login (เข้าสู่ระบบ), และหน้า Profile (โปรไฟล์ผู้ใช้)
# ==============================================================================

from datetime import datetime
from app.extensions import db


class User(db.Model):
    """
    คลาสโมเดล User สำหรับแมปกับตาราง 'users' ในฐานข้อมูล SQLite
    ทำหน้าที่เก็บข้อมูลบัญชีผู้ใช้งาน, รหัสผ่านที่ผ่านการเข้ารหัสแฮช, และเวลาสร้างบัญชี
    """
    # กำหนดชื่อตารางในฐานข้อมูลให้ตรงกับ schema.sql
    __tablename__ = "users"

    # 1. รหัสผู้ใช้งาน (Primary Key) เพิ่มขึ้นอัตโนมัติ (Auto Increment)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 2. อีเมลผู้ใช้งาน (ห้ามเป็นค่าว่าง และต้องไม่ซ้ำกับใครในระบบ เพื่อป้องกันการสมัครซ้ำ)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)

    # 3. รหัสผ่านที่ผ่านการเข้ารหัสแฮช (Password Hash) ห้ามเก็บเป็น Plain Text เพื่อความปลอดภัย
    password_hash = db.Column(db.String(255), nullable=False)

    # 4. วันและเวลาที่ลงทะเบียนเข้าสู่ระบบ (ค่าเริ่มต้นเป็นวันเวลาปัจจุบัน UTC)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 5. ความสัมพันธ์แบบ 1 ต่อ กลุ่ม (1:N) ไปยังตาราง generations
    #    เมื่อ User ถูกลบ ข้อมูลการสร้างภาพทั้งหมดของ User นั้นจะถูกลบตามไปด้วย (Cascade Delete)
    generations = db.relationship(
        "Generation", 
        backref="user", 
        cascade="all, delete-orphan", 
        lazy=True
    )

    def to_dict(self):
        """
        ฟังก์ชันแปลงข้อมูล User Object ให้กลายเป็น Python Dictionary
        สำหรับส่งออกเป็น JSON Response ให้กับ Frontend (ไม่ส่ง password_hash เพื่อความปลอดภัย)
        
        :return: Dictionary ข้อมูลผู้ใช้
        """
        # สร้าง Dictionary ที่มีเฉพาะข้อมูลที่ปลอดภัยในการเปิดเผย
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
