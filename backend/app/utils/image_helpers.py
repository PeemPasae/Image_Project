# ==============================================================================
# ชื่อไฟล์: backend/app/utils/image_helpers.py
# หน้าที่: ฟังก์ชันตัวช่วยสำหรับตรวจสอบไฟล์ภาพ, แปลงข้อมูลภาพ (Decode/Encode) 
#         และส่งไฟล์ภาพกลับไปยัง Frontend ด้วย OpenCV
# ==============================================================================

from io import BytesIO
from typing import Optional, Tuple
import cv2
import numpy as np
from flask import Response, send_file
from werkzeug.datastructures import FileStorage

from app.utils.error_codes import (
    error_response,
    VALIDATION_ERROR,
    UNSUPPORTED_FILE_TYPE,
    INVALID_IMAGE,
)

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def extract_uploaded_image(
    file: Optional[FileStorage],
    field_name: str = "image",
    allowed_extensions: Tuple[str, ...] = ALLOWED_IMAGE_EXTENSIONS,
) -> Tuple[Optional[np.ndarray], Optional[Response]]:
    """
    ตรวจสอบความถูกต้องของไฟล์รูปภาพที่อัปโหลด และถอดรหัสเป็น OpenCV BGR Image (np.ndarray)
    
    :param file: ไฟล์ที่ดึงมาจาก request.files.get(field_name)
    :param field_name: ชื่อ Field ของไฟล์ (ใช้แสดงในข้อความแจ้งเตือน)
    :param allowed_extensions: นามสกุลไฟล์ที่อนุญาต
    :return: (img_bgr, None) หากสำเร็จ หรือ (None, error_response) หากพบข้อผิดพลาด
    """
    # 1. ตรวจสอบว่ามีการแนบไฟล์มาหรือไม่
    if not file:
        return None, error_response(VALIDATION_ERROR, f"{field_name} file is required", 400)

    # 2. ตรวจสอบนามสกุลไฟล์
    filename = (file.filename or "").lower()
    if not filename.endswith(allowed_extensions):
        ext_str = ", ".join(allowed_extensions)
        return None, error_response(UNSUPPORTED_FILE_TYPE, f"Only {ext_str} are supported", 415)

    # 3. ถอดรหัส (Decode) ข้อมูลภาพเป็น BGR (3 Channels)
    try:
        data = file.read()
        if not data:
            return None, error_response(INVALID_IMAGE, "The uploaded file is empty", 400)
        
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return None, error_response(INVALID_IMAGE, "Unable to decode the uploaded image", 400)
        
        return img, None
    except Exception as e:
        return None, error_response(INVALID_IMAGE, f"Failed to process image: {str(e)}", 400)


def send_image_png(img: np.ndarray, download_name: Optional[str] = None) -> Response:
    """
    แปลงภาพ OpenCV (BGR หรือ BGRA) เป็นสตรีม PNG และส่งกลับเป็น HTTP Response
    
    :param img: รูปภาพ OpenCV (np.ndarray)
    :param download_name: ชื่อไฟล์หากต้องการให้ดาวน์โหลด (Optional)
    :return: Flask send_file Response พร้อม mimetype='image/png'
    """
    success, encoded = cv2.imencode(".png", img)
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    
    return send_file(
        BytesIO(encoded.tobytes()),
        mimetype="image/png",
        as_attachment=bool(download_name),
        download_name=download_name,
    )
