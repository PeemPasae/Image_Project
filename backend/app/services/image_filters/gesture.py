import threading
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)
# backend/models/gesture_recognizer.task
MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "gesture_recognizer.task"

# ชื่อท่าที่โมเดลมาตรฐานของ MediaPipe รู้จัก -> ข้อความที่โชว์บนหน้าเว็บ
GESTURE_NAMES = {
    "None": "ไม่ตรงกับท่าที่รู้จัก",
    "Closed_Fist": "กำมือ",
    "Open_Palm": "แบมือ",
    "Pointing_Up": "ชี้นิ้วขึ้น",
    "Thumb_Down": "คว่ำนิ้วโป้ง",
    "Thumb_Up": "ชูนิ้วโป้ง",
    "Victory": "ชูสองนิ้ว",
    "ILoveYou": "I Love You",
}

# webcam ของ user ที่ไม่ส่งเฟรมมาเกินเวลานี้ ถือว่าปิดกล้องไปแล้ว คืนหน่วยความจำ
SESSION_IDLE_SECONDS = 60

# MediaPipe ใช้พร้อมกันหลาย thread ไม่ได้ แต่ Flask รับ request หลาย thread จึงต้องล็อก
# แยก lock ของโหมดรูปกับโหมด webcam ไว้ จะได้ไม่ต้องรอกัน
_model_lock = threading.Lock()
_image_lock = threading.Lock()
_video_lock = threading.Lock()

_image_recognizers = {}  # (num_hands, min_confidence) -> recognizer ใช้ร่วมกันทุกคน
_sessions = {}           # user_id -> recognizer โหมด VIDEO ของ user คนนั้น


# ==============================================================================
# ส่วนกลาง
# ==============================================================================

def _model_path():
    """หาไฟล์โมเดล ถ้ายังไม่มีให้ดาวน์โหลด (ทำตอนใช้ครั้งแรก ไม่ใช่ตอนเปิดแอป)"""
    with _model_lock:
        if not MODEL_PATH.is_file():
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = MODEL_PATH.with_suffix(".part")
            urllib.request.urlretrieve(MODEL_URL, tmp)
            tmp.replace(MODEL_PATH)
    return str(MODEL_PATH)


def _create_recognizer(running_mode, num_hands, min_confidence):
    """สร้าง recognizer ใหม่ (ช้าหลายร้อย ms และเปลี่ยนค่าหลังสร้างไม่ได้ เลยต้องเก็บไว้ใช้ซ้ำ)"""
    options = vision.GestureRecognizerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=_model_path()),
        running_mode=running_mode,
        num_hands=num_hands,
        min_hand_detection_confidence=min_confidence,
        min_hand_presence_confidence=min_confidence,
        min_tracking_confidence=min_confidence,
    )
    return vision.GestureRecognizer.create_from_options(options)


def _to_mp_image(img):
    """OpenCV อ่านภาพเป็น BGR แต่ MediaPipe ต้องการ RGB"""
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)


def _format(result, inference_ms):
    """แปลงผลดิบของ MediaPipe เป็น dict ที่ส่งเป็น JSON ได้"""
    hands = []
    # แต่ละมือมีท่าของตัวเอง จึงต้องอ่านตาม index i ไม่ใช่ [0] ตลอด
    for i, landmarks in enumerate(result.hand_landmarks):
        top = result.gestures[i][0] if i < len(result.gestures) and result.gestures[i] else None
        side = result.handedness[i][0] if i < len(result.handedness) and result.handedness[i] else None
        name = top.category_name if top else "None"
        hands.append({
            "gesture": name,
            "gesture_th": GESTURE_NAMES.get(name, name),
            "confidence": round(float(top.score) * 100, 2) if top else 0.0,
            "handedness": side.category_name if side else "Unknown",
            # พิกัด 21 จุดแบบ 0-1 ให้หน้าเว็บเอาไปวาดโครงมือเอง
            "landmarks": [{"x": round(p.x, 4), "y": round(p.y, 4)} for p in landmarks],
        })

    # มือที่มั่นใจที่สุด ใช้เป็นผลหลักที่โชว์บนหน้าเว็บ
    best = max(hands, key=lambda h: h["confidence"]) if hands else None
    return {
        "found": bool(hands),
        "hand_count": len(hands),
        "gesture": best["gesture"] if best else None,
        "gesture_th": best["gesture_th"] if best else "ไม่พบมือในภาพ",
        "confidence": best["confidence"] if best else 0.0,
        "handedness": best["handedness"] if best else None,
        "inference_time_ms": round(inference_ms, 2),
        "hands": hands,
    }


# ==============================================================================
# โหมดรูปนิ่ง (IMAGE)
# ==============================================================================

def recognize_gesture(img, num_hands=2, min_confidence=0.5):
    """จดจำท่ามือจากรูปนิ่ง

    img            : ภาพ (BGR)
    num_hands      : จำนวนมือสูงสุดที่จะหา 1-4
    min_confidence : ความมั่นใจขั้นต่ำที่จะนับว่าเจอมือ 0.1-1.0
    """
    mp_image = _to_mp_image(img)
    key = (num_hands, round(min_confidence, 1))

    with _image_lock:
        if key not in _image_recognizers:
            _image_recognizers[key] = _create_recognizer(vision.RunningMode.IMAGE, *key)
        start = time.perf_counter()
        result = _image_recognizers[key].recognize(mp_image)
        inference_ms = (time.perf_counter() - start) * 1000

    return _format(result, inference_ms)


# ==============================================================================
# โหมด webcam (VIDEO)
# ==============================================================================
#
# โหมด VIDEO จำตำแหน่งมือจากเฟรมก่อนไว้ ทำให้ไม่ต้องหามือใหม่ทุกเฟรม (เร็วกว่าและนิ่งกว่า)
# แต่เพราะมัน "จำ" จึงแชร์ข้ามคนไม่ได้ ไม่งั้นมือของ user A จะไปปนกับเฟรมของ user B
# -> แต่ละ user ต้องมี recognizer ของตัวเอง

def _close_idle_sessions(now):
    """ปิด recognizer ของคนที่เลิกใช้กล้องไปนานแล้ว (ต้องเรียกภายใน _video_lock)"""
    for user_id in list(_sessions):
        if now - _sessions[user_id]["last_used"] > SESSION_IDLE_SECONDS:
            _sessions.pop(user_id)["recognizer"].close()


def recognize_gesture_frame(img, user_id, num_hands=2, min_confidence=0.5):
    """จดจำท่ามือจากเฟรม webcam ของ user คนหนึ่ง

    img     : เฟรมภาพ (BGR)
    user_id : เจ้าของกล้อง ใช้แยก recognizer ของแต่ละคน
    """
    mp_image = _to_mp_image(img)
    key = (num_hands, round(min_confidence, 1))
    now = time.monotonic()

    with _video_lock:
        _close_idle_sessions(now)

        # 1) หา recognizer ของ user นี้ ถ้ายังไม่มีหรือเลื่อน slider เปลี่ยนค่า ให้สร้างใหม่
        session = _sessions.get(user_id)
        if session is None or session["key"] != key:
            if session is not None:
                session["recognizer"].close()
            session = {
                "key": key,
                "recognizer": _create_recognizer(vision.RunningMode.VIDEO, *key),
                "last_ts": 0,
            }
            _sessions[user_id] = session

        # 2) โหมด VIDEO บังคับว่า timestamp ต้องเพิ่มขึ้นทุกเฟรม ใช้เวลาฝั่ง server
        #    (+1 กันกรณีสองเฟรมมาใน ms เดียวกัน เช่นเปิดสองแท็บ)
        timestamp_ms = max(session["last_ts"] + 1, int(now * 1000))
        session["last_ts"] = timestamp_ms
        session["last_used"] = now

        # 3) ให้โมเดลทาย และจับเวลาเฉพาะช่วง inference
        start = time.perf_counter()
        result = session["recognizer"].recognize_for_video(mp_image, timestamp_ms)
        inference_ms = (time.perf_counter() - start) * 1000

    return _format(result, inference_ms)


def close_gesture_session(user_id):
    """ปิดกล้องแล้ว -> คืน recognizer ของ user นี้ทันที ไม่ต้องรอให้หมดเวลาเอง"""
    with _video_lock:
        session = _sessions.pop(user_id, None)
    if session is not None:
        session["recognizer"].close()