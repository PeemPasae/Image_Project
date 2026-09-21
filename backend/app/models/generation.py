# ==============================================================================
# ชื่อไฟล์: backend/app/models/generation.py
# หน้าที่: โมเดลตารางประวัติรูปภาพ (generations) รองรับประวัติทั้ง 2 รูปแบบ (AI Checkpoint & Sub-Functions)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Generate (สร้างภาพ), หน้า Result (ดูผลลัพธ์), หน้า History (ประวัติทั้งหมด)
# ==============================================================================

import json
from datetime import datetime
from app.extensions import db


class Generation(db.Model):
    """
    คลาสโมเดล Generation สำหรับแมปกับตาราง 'generations' ในฐานข้อมูล SQLite
    ทำหน้าที่เก็บประวัติรูปภาพทั้ง 2 รูปแบบอย่างเป็นระเบียบ:
    - รูปแบบที่ 1 (Checkpoint): ภาพที่สร้างผ่าน AI Stable Diffusion (txt2img)
    - รูปแบบที่ 2 (Sub-Functions): ภาพที่นำไปผ่านฟังก์ชันแต่งภาพย่อย (Canny, Blur, Gaussian Blur, Custom)
    """
    # กำหนดชื่อตารางในฐานข้อมูลให้ตรงกับ schema.sql
    __tablename__ = "generations"

    # 1. รหัสภาพ (Primary Key) เพิ่มขึ้นอัตโนมัติ (Auto Increment)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 2. รหัสผู้ใช้เจ้าของภาพ (Foreign Key เชื่อมกับตาราง users.id)
    #    เมื่อ User ถูกลบ ภาพทั้งหมดของ User นั้นจะถูกลบตาม Cascade ทันที
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 3. หมวดหมู่ของรูปภาพ (Category เพื่อแยกประเภทประวัติ 2 แบบ):
    #    - 'sd_generate'  : รูปแบบที่ 1 สร้างจาก AI Stable Diffusion ผ่าน Checkpoint
    #    - 'image_filter' : รูปแบบที่ 2 สร้างจากฟังก์ชันแต่งภาพ Sub-functions
    category = db.Column(db.String(50), nullable=False, default="sd_generate", index=True)

    # 4. ฟังก์ชันการทำงานที่ใช้ (Action Type):
    #    เช่น 'txt2img', 'canny', 'blur', 'gaussian_blur', 'custom_filter'
    action_type = db.Column(db.String(50), nullable=False, default="txt2img")

    # 5. พารามิเตอร์สำหรับ AI Stable Diffusion (รูปแบบที่ 1)
    prompt = db.Column(db.String(2000), nullable=False, default="")
    negative_prompt = db.Column(db.String(2000), nullable=True, default="")
    checkpoint = db.Column(db.String(255), nullable=True, default="")
    sampler = db.Column(db.String(100), nullable=True, default="")
    width = db.Column(db.Integer, nullable=True, default=512)
    height = db.Column(db.Integer, nullable=True, default=512)
    steps = db.Column(db.Integer, nullable=True, default=20)
    cfg_scale = db.Column(db.Float, nullable=True, default=7.0)
    seed = db.Column(db.BigInteger, nullable=True, default=-1)

    # 6. พารามิเตอร์เพิ่มเติมในรูป JSON String (เช่น threshold สำหรับ canny, kernel_size สำหรับ blur)
    params = db.Column(db.Text, nullable=True, default="{}")

    # 7. ไอดีของภาพต้นฉบับ (กรณีเป็นภาพรูปแบบที่ 2 ที่นำภาพเดิมมาแต่งต่อ)
    source_image_id = db.Column(db.Integer, nullable=True)

    # 8. เส้นทางไฟล์ (สำหรับรองรับความเข้ากันได้กับระบบเดิม)
    image_path = db.Column(db.String(500), nullable=True, default="")

    # 9. ข้อมูลไฟล์ภาพแบบไบนารี (BLOB / LargeBinary) สำหรับจัดเก็บภาพลงในฐานข้อมูลโดยตรง
    image_data = db.Column(db.LargeBinary, nullable=False)

    # 10. วันและเวลาที่สร้างรูปภาพ (UTC) สำหรับใช้จัดเรียงประวัติจากล่าสุดไปเก่าสุด
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def get_params_dict(self) -> dict:
        """
        ฟังก์ชันสำหรับแปลงข้อความ JSON ในฟิลด์ params ให้เป็น Python Dictionary
        
        :return: Dictionary ของพารามิเตอร์
        """
        if not self.params:
            return {}
        try:
            return json.loads(self.params)
        except Exception:
            return {}

    def get_type_display_name(self) -> str:
        """
        ฟังก์ชันคืนค่าชื่อประเภทภาษาไทย/อังกฤษที่เข้าใจง่ายสำหรับแสดงบนหน้าเว็บ History
        
        :return: ข้อความแสดงประเภท
        """
        if self.category == "sd_generate":
            return "Checkpoint Generation (Stable Diffusion)"
        elif self.category == "image_filter":
            filter_names = {
                "canny": "Sub-Function: Canny Edge Detection",
                "blur": "Sub-Function: Average Blur",
                "gaussian_blur": "Sub-Function: Gaussian Blur",
                "custom_filter": "Sub-Function: Custom Filter",
            }
            return filter_names.get(self.action_type, f"Sub-Function ({self.action_type})")
        return "Image Generation"

    def to_dict(self) -> dict:
        """
        ฟังก์ชันแปลงข้อมูล Generation Model เป็น Dictionary สำหรับส่งกลับใน JSON Response
        ตามมาตรฐาน LUMA API Contract
        
        :return: Dictionary ข้อมูลประวัติการสร้างภาพ
        """
        return {
            "id": self.id,
            "generation_id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "action_type": self.action_type,
            "type_display": self.get_type_display_name(),
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "checkpoint": self.checkpoint,
            "sampler": self.sampler,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "seed": self.seed,
            "params": self.get_params_dict(),
            "source_image_id": self.source_image_id,
            "image_url": f"/api/v1/images/{self.id}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
