# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/gesture.py
# หน้าที่: อัลกอริทึมจดจำท่าทางมือ (Hand Gesture Recognition) ด้วย MediaPipe Tasks
# ==============================================================================

import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, Any

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)

# ค้นหาโมเดลจาก ai_models หรือ models เพื่อความยืดหยุ่น
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    _BACKEND_ROOT / "ai_models" / "gesture_recognizer.task"
    if (_BACKEND_ROOT / "ai_models" / "gesture_recognizer.task").is_file()
    else _BACKEND_ROOT / "models" / "gesture_recognizer.task"
)

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

_model_lock = threading.Lock()
_image_lock = threading.Lock()
_image_recognizers: Dict[Any, Any] = {}


def _model_path() -> str:
    """ตรวจสอบไฟล์โมเดล หากยังไม่มีให้ดาวน์โหลดอัตโนมัติ"""
    with _model_lock:
        if not MODEL_PATH.is_file():
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = MODEL_PATH.with_suffix(".part")
            urllib.request.urlretrieve(MODEL_URL, tmp)
            tmp.replace(MODEL_PATH)
    return str(MODEL_PATH)


def _create_recognizer(running_mode, num_hands: int, min_confidence: float):
    """สร้าง MediaPipe GestureRecognizer instance"""
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
    """แปลง OpenCV BGR เป็น MediaPipe RGB Image"""
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)


def _format(result, inference_ms: float) -> Dict[str, Any]:
    """แปลงผลลัพธ์ของ MediaPipe ให้เป็น Dict มาตรฐานสำหรับ API"""
    hands = []
    for i, landmarks in enumerate(result.hand_landmarks):
        top = result.gestures[i][0] if i < len(result.gestures) and result.gestures[i] else None
        side = result.handedness[i][0] if i < len(result.handedness) and result.handedness[i] else None
        name = top.category_name if top else "None"
        hands.append({
            "gesture": name,
            "gesture_th": GESTURE_NAMES.get(name, name),
            "confidence": round(float(top.score) * 100, 2) if top else 0.0,
            "handedness": side.category_name if side else "Unknown",
            "landmarks": [{"x": round(p.x, 4), "y": round(p.y, 4)} for p in landmarks],
        })

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


def recognize_gesture(img, num_hands: int = 2, min_confidence: float = 0.5) -> Dict[str, Any]:
    """
    จดจำท่ามือจากรูปภาพนิ่ง
    
    :param img: ภาพ OpenCV BGR (np.ndarray)
    :param num_hands: จำนวนมือสูงสุดที่ตรวจจับ (1-4)
    :param min_confidence: ค่าความมั่นใจขั้นต่ำ (0.1 - 1.0)
    :return: ผลลัพธ์การจดจำท่ามือ
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