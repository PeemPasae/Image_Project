import cv2
import numpy as np


def tilt_shift(
    img: np.ndarray,
    focus_position: float = 0.5,
    focus_width: float = 0.2,
    blur_strength: int = 15,
    saturation_boost: float = 1.4,
    contrast_boost: float = 1.2,
) -> np.ndarray:
    """สร้างเอฟเฟกต์ภาพถ่ายโมเดลจำลอง (Tilt-Shift / Miniature Diorama Effect)

    img              : ภาพต้นฉบับ (BGR)
    focus_position   : ตำแหน่งระนาบโฟกัสในแนวดิ่ง (0.0 = บนสุด, 1.0 = ล่างสุด)
    focus_width      : ความกว้างของช่วงโฟกัสที่คมชัด (0.05 - 0.5)
    blur_strength    : ความแรงของการเบลอฉากหลัง (1 - 30)
    saturation_boost : ตัวคูณความสดของสีในระบบ HSV (1.0 - 2.0)
    contrast_boost   : ตัวคูณความเปรียบต่าง (1.0 - 1.8)
    """
    h, w = img.shape[:2]

    # 1. เร่งสีและคอนทราสต์ให้เหมือนสีโมเดลของเล่น
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
    boosted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    boosted = np.clip((boosted - 128.0) * contrast_boost + 128.0, 0, 255)

    # 2. สร้างภาพเบลอเตรียมไว้
    k = blur_strength * 2 + 1
    blurred = cv2.GaussianBlur(boosted, (k, k), 0)

    # 3. คำนวณ Progressive Depth Map ในแนวดิ่ง
    y_indices = np.arange(h, dtype=np.float32)
    center_y = focus_position * h
    band_half_width = (focus_width * h) / 2.0
    dist = np.abs(y_indices - center_y)

    transition_width = h * 0.25
    weight = np.clip((dist - band_half_width) / max(transition_width, 1.0), 0.0, 1.0)
    weight = 0.5 * (1.0 - np.cos(weight * np.pi))  # Smoothstep transition
    mask = np.repeat(weight[:, np.newaxis, np.newaxis], w, axis=1)

    # 4. ผสมผสานภาพชัดกับภาพเบลอตามระยะความลึก
    output = boosted * (1.0 - mask) + blurred * mask
    return np.clip(output, 0, 255).astype(np.uint8)
