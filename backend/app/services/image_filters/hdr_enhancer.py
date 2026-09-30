import cv2
import numpy as np


def hdr_enhancer(
    img: np.ndarray,
    clahe_clip_limit: float = 3.0,
    clahe_grid_size: int = 8,
    detail_strength: float = 1.5,
    color_balance: bool = True,
) -> np.ndarray:
    """เพิ่มมิติและรายละเอียดภาพถ่ายสไตล์ HDR (CLAHE & Multi-scale Detail Enhancement)

    img              : ภาพต้นฉบับ (BGR)
    clahe_clip_limit : ขีดจำกัดคอนทราสต์ ป้องกัน Noise แตก (1.0 - 5.0)
    clahe_grid_size  : ขนาด Grid ย่อยของการคำนวณ (4 - 16)
    detail_strength  : น้ำหนักการขับเน้น Texture และความคมชัด (0.0 - 3.0)
    color_balance    : ปรับสมดุลสีขาวอัตโนมัติด้วย Gray World Algorithm
    """
    result = img.copy()

    # 1. Gray World Auto White Balance
    if color_balance:
        f = result.astype(np.float32)
        b_avg, g_avg, r_avg = np.mean(f[:, :, 0]), np.mean(f[:, :, 1]), np.mean(f[:, :, 2])
        gray_mean = (b_avg + g_avg + r_avg) / 3.0
        if b_avg > 0 and g_avg > 0 and r_avg > 0:
            f[:, :, 0] = np.clip(f[:, :, 0] * (gray_mean / b_avg), 0, 255)
            f[:, :, 1] = np.clip(f[:, :, 1] * (gray_mean / g_avg), 0, 255)
            f[:, :, 2] = np.clip(f[:, :, 2] * (gray_mean / r_avg), 0, 255)
            result = f.astype(np.uint8)

    # 2. แปลงเป็น CIE L*a*b* เพื่อปรับเฉพาะมิติความสว่าง (Luminance)
    lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # 3. ใช้ CLAHE บน L-channel
    grid = max(2, clahe_grid_size)
    clahe = cv2.createCLAHE(clipLimit=float(clahe_clip_limit), tileGridSize=(grid, grid))
    l_enhanced = clahe.apply(l_channel)

    # ประกอบช่องสัญญาณกลับ
    lab_merged = cv2.merge([l_enhanced, a_channel, b_channel])
    tone_mapped = cv2.cvtColor(lab_merged, cv2.COLOR_LAB2BGR)

    # 4. Multi-scale Unsharp Masking เสริม Micro-contrast
    if detail_strength > 0:
        low_freq = cv2.GaussianBlur(tone_mapped, (0, 0), sigmaX=3.0)
        high_freq = cv2.subtract(tone_mapped, low_freq)
        return cv2.addWeighted(tone_mapped, 1.0, high_freq, float(detail_strength), 0)

    return tone_mapped
