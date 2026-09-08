from datetime import datetime
from app.extensions import db  # หรือ db Instance หลักของโปรเจกต์คุณ

class Generation(db.Model):
    __tablename__ = "generations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.String(2000), nullable=False)
    negative_prompt = db.Column(db.String(2000), nullable=True, default="")
    checkpoint = db.Column(db.String(255), nullable=False)
    sampler = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.Integer, nullable=False)
    cfg_scale = db.Column(db.Float, nullable=False)
    seed = db.Column(db.BigInteger, nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """แปลง Object เป็น Dictionary สำหรับส่งกลับไปให้ API"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "checkpoint": self.checkpoint,
            "sampler": self.sampler,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "seed": self.seed,
            "image_url": f"/api/v1/images/{self.id}",
            "created_at": self.created_at.isoformat()
        }
