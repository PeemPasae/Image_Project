# ==============================================================================
# ชื่อไฟล์: backend/app/services/image_filters/cartoonize.py
# หน้าที่: ฟังก์ชันแปลงภาพถ่ายเป็นการ์ตูน/อนิเมะ (Anime / Comic Stylization)
# ==============================================================================

import cv2
import numpy as np


def cartoonize(
    img: np.ndarray,
    num_colors: int = 8,
    line_thickness: int = 2,
    smoothness: int = 5,
) -> np.ndarray:
    """แปลงภาพถ่ายเป็นสไตล์การ์ตูน/อนิเมะ (Anime / Comic Stylization)

    :param img: ภาพต้นฉบับ BGR (np.ndarray)
    :param num_colors: จำนวนสีหลักที่ต้องการจัดกลุ่ม (K-Means clusters: 4 - 32)
    :param line_thickness: ความหนาของเส้นขอบหมึก (1 - 5)
    :param smoothness: ความเนียนของพื้นผิวด้วย Bilateral Filter (1 - 10)
    :return: ภาพสไตล์การ์ตูน BGR
    """
    # 1. เกลี่ยผิวภาพแบบรักษาเส้นขอบ (Bilateral Filtering)
    d = max(3, int(smoothness) * 2 + 1)
    sigma = int(smoothness) * 15
    color = img.copy()
    for _ in range(max(1, int(smoothness) // 2)):
        color = cv2.bilateralFilter(color, d=d, sigmaColor=sigma, sigmaSpace=sigma)

    # 2. ลดทอนจำนวนเฉดสีด้วย K-Means Clustering (Machine Learning)
    pixels = np.float32(color.reshape((-1, 3)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
    k = max(2, min(32, int(num_colors)))
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    quantized = np.uint8(centers)[labels.flatten()].reshape(img.shape)

    # 3. สกัดเส้นโครงร่างหมึก (Cartoon Ink Outlines)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray_blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize=9, C=2
    )

    thickness = int(line_thickness)
    if thickness > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (thickness, thickness))
        edges = cv2.erode(edges, kernel)

    # 4. รวมเส้นขอบสีดำเข้ากับเลเยอร์สี
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.bitwise_and(quantized, edges_bgr)
