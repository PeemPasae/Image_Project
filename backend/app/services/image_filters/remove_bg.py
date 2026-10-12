import threading
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
    "selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"
)
# backend/models/selfie_multiclass_256x256.tflite
MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "selfie_multiclass_256x256.tflite"

# GrabCut ช้าตามขนาดรูป จึงคำนวณที่รูปย่อ (ด้านยาวสุดเท่านี้) แล้วค่อยขยาย mask กลับ
WORK_SIDE = 900

# MediaPipe ใช้พร้อมกันหลาย thread ไม่ได้ แต่ Flask รับ request หลาย thread จึงต้องล็อก
_lock = threading.Lock()
_segmenter = None


# ==============================================================================
# AI: ความน่าจะเป็นว่าแต่ละ pixel เป็น "คน"
# ==============================================================================

def _get_segmenter():
    """โหลดโมเดลตอนใช้ครั้งแรก (ถ้ายังไม่มีไฟล์จะดาวน์โหลดให้) ต้องเรียกภายใน _lock"""
    global _segmenter
    if _segmenter is None:
        if not MODEL_PATH.is_file():
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = MODEL_PATH.with_suffix(".part")
            urllib.request.urlretrieve(MODEL_URL, tmp)
            tmp.replace(MODEL_PATH)
        _segmenter = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH)),
            output_confidence_masks=True,
        ))
    return _segmenter


def _person_prob(img):
    """คืนค่า 0-1 ต่อ pixel ว่าเป็นคน (= 1 - ความน่าจะเป็นที่เป็นพื้นหลัง)"""
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with _lock:
        result = _get_segmenter().segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    background = np.squeeze(result.confidence_masks[0].numpy_view()).astype(np.float32)
    return 1.0 - background


def _largest_blob(mask, extra=None):
    """เก็บก้อนที่ใหญ่ที่สุด (+ ก้อนที่ทับกับ extra ถ้ามี) ก้อนอื่นทิ้ง"""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    if n <= 1:
        return mask.astype(bool)
    keep = {1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))}
    if extra is not None:
        keep |= set(np.unique(labels[extra]).tolist()) - {0}
    return np.isin(labels, list(keep))


# ==============================================================================
# ตัดพื้นหลัง (ทำที่รูปย่อ)
# ==============================================================================

def _cut(img, person, rect, strokes):
    """คืน alpha 0-1 ของสิ่งที่เก็บไว้

    person  : ผลจาก AI (None = ไม่ใช้ AI)
    rect    : [x, y, w, h] หรือ None
    strokes : [{"type": "keep"/"remove", "r": รัศมี, "points": [[x, y], ...]}, ...]
    """
    H, W = img.shape[:2]

    # 1) ไม่ลากกรอบและไม่ระบาย -> ใช้ AI อย่างเดียว (เร็วที่สุด)
    if rect is None and not strokes:
        soft = np.clip((person - 0.3) / 0.4, 0, 1)                  # ขอบนุ่มตามความมั่นใจ
        return _largest_blob(person > 0.5).astype(np.float32) * soft

    # 2) mask เริ่มต้นของ GrabCut
    #    GC_BGD = พื้นหลังแน่นอน, GC_FGD = พื้นหน้าแน่นอน
    #    GC_PR_BGD / GC_PR_FGD = "น่าจะ" เป็นพื้นหลัง / พื้นหน้า (GrabCut เปลี่ยนได้)
    x, y, w, h = rect if rect is not None else (0, 0, W, H)
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(W, int(x + w)), min(H, int(y + h))
    inside = np.zeros((H, W), bool)
    inside[y0:y1, x0:x1] = True

    mask = np.full((H, W), cv2.GC_BGD, np.uint8)                    # นอกกรอบ = พื้นหลังแน่นอน
    if person is not None:
        mask[inside] = cv2.GC_PR_BGD                                 # ในกรอบ = น่าจะพื้นหลัง
        mask[inside & (person > 0.5)] = cv2.GC_PR_FGD                # ...ยกเว้นที่ AI บอกว่าเป็นคน
        mask[inside & (person > 0.9)] = cv2.GC_FGD                   # AI มั่นใจมาก = แน่นอน
    else:
        mask[inside] = cv2.GC_PR_FGD                                 # ไม่มี AI: ให้สีเป็นตัวตัดสิน

    # 3) เส้นที่ผู้ใช้ระบาย = คำตอบแน่นอน (ทับทุกอย่าง)
    for s in strokes:
        pts = np.array(s["points"], np.int32).reshape(-1, 2)
        value = cv2.GC_FGD if s["type"] == "keep" else cv2.GC_BGD
        r = max(1, int(s["r"]))
        if len(pts) == 1:
            cv2.circle(mask, (int(pts[0][0]), int(pts[0][1])), r, value, -1)
        else:
            cv2.polylines(mask, [pts], False, value, r * 2)

    # 4) GrabCut ต้องมีทั้งพื้นหน้าและพื้นหลังอย่างละนิด ไม่งั้นสร้างโมเดลสีไม่ได้
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD))
    if fg.all() or not fg.any():
        return fg.astype(np.float32)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd_model, fgd_model, 4, cv2.GC_INIT_WITH_MASK)
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD))

    # 5) ทิ้งเศษเล็ก ๆ แต่เก็บก้อนที่ผู้ใช้ระบาย "เก็บ" ไว้เสมอ
    return _largest_blob(fg, extra=(mask == cv2.GC_FGD)).astype(np.float32)


# ==============================================================================
# ฟังก์ชันหลัก
# ==============================================================================

def remove_background(img, rect=None, strokes=None, use_ai=True, bg_color=None):
    """ลบพื้นหลัง

    img      : ภาพ (BGR) ความละเอียดเต็ม
    rect     : กรอบที่ผู้ใช้ลาก [x, y, w, h] หน่วย pixel ของรูปจริง (None = ไม่มีกรอบ)
    strokes  : เส้นแปรง [{"type": "keep"/"remove", "r": รัศมี, "points": [[x, y], ...]}, ...]
    use_ai   : ใช้ AI หา "คน" เป็นจุดเริ่ม (False = GrabCut ล้วน ต้องมีกรอบ)
    bg_color : None = พื้นโปร่งใส (คืน BGRA), (B, G, R) = เติมสีพื้น (คืน BGR)
    """
    strokes = strokes or []
    H, W = img.shape[:2]

    # 1) ย่อรูป และย่อพิกัดกรอบ/แปรงตามสัดส่วนเดียวกัน
    s = min(1.0, WORK_SIDE / max(H, W))
    small = cv2.resize(img, (round(W * s), round(H * s)), interpolation=cv2.INTER_AREA) if s < 1 else img
    small_rect = [v * s for v in rect] if rect is not None else None
    small_strokes = [
        {"type": st["type"], "r": max(1, round(st["r"] * s)),
         "points": [[p[0] * s, p[1] * s] for p in st["points"]]}
        for st in strokes
    ]

    # 2) หา alpha ที่รูปย่อ
    person = _person_prob(small) if use_ai else None
    alpha_small = _cut(small, person, small_rect, small_strokes)

    # 3) ประมาณ "สีพื้นหลังเดิม" รอบ ๆ ตัว (ที่รูปย่อ เพราะต้องเบลอแรง ทำที่รูปใหญ่จะช้า)
    #    = ค่าเฉลี่ยถ่วงน้ำหนักเฉพาะ pixel ที่เป็นพื้นหลัง
    bg_w = 1.0 - alpha_small
    bg_small = cv2.GaussianBlur(small.astype(np.float32) * bg_w[:, :, None], (0, 0), 12) / \
        np.maximum(cv2.GaussianBlur(bg_w, (0, 0), 12), 1e-3)[:, :, None]

    # 4) ขยายกลับเป็นขนาดเต็ม + ทำขอบนุ่ม
    alpha = cv2.resize(alpha_small, (W, H), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (0, 0), max(1.0, 1.0 / s))
    bg_old = cv2.resize(bg_small, (W, H), interpolation=cv2.INTER_LINEAR)

    # 5) ลบสีพื้นเดิมที่ติดขอบ จากสมการ  I = a*F + (1-a)*B  ->  F = (I - (1-a)*B) / a
    a = alpha[:, :, None]
    I = img.astype(np.float32)
    F = np.clip((I - (1 - a) * bg_old) / np.maximum(a, 0.15), 0, 255)
    F = np.where(a > 0.95, I, F)                                       # ตรงกลางตัวใช้สีเดิม

    # 6) ประกอบผลลัพธ์
    if bg_color is None:
        return np.dstack([F, alpha * 255]).astype(np.uint8)             # BGRA โปร่งใส
    out = F * a + np.array(bg_color, np.float32) * (1 - a)
    return out.astype(np.uint8)                                          # BGR พร้อมสีพื้น