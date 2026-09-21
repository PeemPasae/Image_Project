import cv2
import numpy as np


def spot_blur(img, circles, strength=10, soft=True):
    """เบลอเฉพาะจุดเป็นวงกลม

    img      : ภาพ (BGR)
    circles  : รายการวงกลม [(x, y, radius), ...] หน่วยเป็น pixel ของภาพจริง
               ลากเมาส์ 1 ครั้ง = หลายวงกลมต่อกัน เหมือนระบายด้วยพู่กัน
    strength : ความแรงของการเบลอ 1-30
    soft     : True = ขอบวงกลมค่อย ๆ จางลง (ดูเนียน), False = ขอบคม
    """
    # 1) เบลอทั้งภาพเตรียมไว้
    k = strength * 2 + 1
    blurred = cv2.GaussianBlur(img, (k, k), 0)

    # 2) สร้าง mask: วาดวงกลมสีขาว (1) บนพื้นดำ (0) ตรงที่ผู้ใช้เลือก
    mask = np.zeros(img.shape[:2], np.float32)
    for x, y, r in circles:
        cv2.circle(mask, (int(x), int(y)), int(r), 1.0, -1)

    # 3) ทำขอบ mask ให้นุ่ม รอยต่อระหว่างส่วนที่เบลอกับไม่เบลอจะได้ไม่เป็นเส้นแข็ง
    if soft and circles:
        edge = int(max(r for _, _, r in circles) * 0.5) * 2 + 1
        mask = cv2.GaussianBlur(mask, (edge, edge), 0)

    # 4) ผสมภาพ: ตรงไหน mask = 1 ใช้ภาพเบลอ, mask = 0 ใช้ภาพเดิม, ค่ากลาง ๆ ผสมกัน
    mask = mask[:, :, None]
    out = img * (1 - mask) + blurred * mask
    return out.astype(np.uint8)