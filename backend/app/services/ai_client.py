# ==============================================================================
# ชื่อไฟล์: backend/app/services/ai_client.py
# หน้าที่: บริการติดต่อสื่อสารกับ AI Server (Stable Diffusion WebUI / Forge API)
#         พร้อมระบบจัดการคิวงานพร้อมกัน (Concurrency Queue) และระบบคำนวณเวลาโดยประมาณ (Time Estimation)
# เกี่ยวข้องกับหน้าเว็บ: หน้า Generate (สร้างภาพ), หน้า Result (แสดงผลลัพธ์)
# ==============================================================================

import os
import time
import logging
import threading
import requests
from flask import current_app, has_app_context
from config import Config

logger = logging.getLogger("luma.ai_client")

# ==============================================================================
# ตัวแปรระดับส่วนกลางสำหรับการจัดการ Concurrency Lock และ Queue
# ==============================================================================
# Mutex Lock สำหรับให้คำขอประมวลผลบน GPU เข้าคิวทีละงานอย่างเป็นระเบียบ (Thread-Safe)
_gpu_lock = threading.Lock()

# ตัวนับจำนวนคำขอที่กำลังรอคิวอยู่ในระบบขณะนี้
_waiting_counter_lock = threading.Lock()
_waiting_jobs_count = 0


def get_ai_server_url() -> str:
    """
    ฟังก์ชันดึง Base URL ของ AI Server จาก Flask App Config หรือ Environment Variables (.env)
    
    :return: สตริง URL ของ AI Server เช่น 'http://172.20.57.0:8088'
    """
    if has_app_context() and current_app.config.get("AI_SERVER_URL"):
        return str(current_app.config["AI_SERVER_URL"]).rstrip("/")
    return (os.getenv("AI_SERVER_URL") or getattr(Config, "AI_SERVER_URL", "http://172.20.57.0:8088")).rstrip("/")


def get_ai_server_timeout() -> int:
    """ดึงค่า Timeout ของ AI Server จาก Config (ค่าเริ่มต้น 75 วินาที)"""
    if has_app_context() and current_app.config.get("AI_SERVER_TIMEOUT_SECONDS"):
        return int(current_app.config["AI_SERVER_TIMEOUT_SECONDS"])
    return int(getattr(Config, "AI_SERVER_TIMEOUT_SECONDS", 75))


# ==============================================================================
# นิยาม Custom Exceptions สำหรับข้อผิดพลาดเฉพาะทางของ AI Server
# ==============================================================================
class AIServerBusyException(Exception):
    """ข้อยกเว้นเมื่อ AI Server มีคิวงานแน่นเกินเวลาที่กำหนดให้รอได้"""
    pass


class AIServerTimeoutException(Exception):
    """ข้อยกเว้นเมื่อ AI Server ใช้เวลาประมวลผลนานเกิน 75 วินาที"""
    pass


class AIServerErrorException(Exception):
    """ข้อยกเว้นเมื่อ AI Server ตอบกลับข้อผิดพลาด หรือไม่สามารถเชื่อมต่อได้"""
    pass


# ==============================================================================
# ฟังก์ชันประเมินเวลา (Time Estimation System)
# ==============================================================================
def calculate_estimated_time(width: int = 512, height: int = 512, steps: int = 20) -> dict:
    """
    ฟังก์ชันคำนวณเวลาโดยประมาณที่ต้องใช้ในการสร้างภาพ (หน่วย: วินาที)
    คำนวณจาก:
    1. ขนาดของภาพ (Width x Height เทียบกับขนาดมาตรฐาน 512x512)
    2. จำนวนรอบการประมวลผล (Sampling Steps)
    3. จำนวนคิวงานที่กำลังรออยู่ข้างหน้าในระบบขณะนี้
    
    :param width: ความกว้างของภาพ (พิกเซล)
    :param height: ความสูงของภาพ (พิกเซล)
    :param steps: จำนวน Sampling Steps
    :return: Dictionary สรุปเวลาโดยประมาณและสถานะคิว
    """
    # 1. กำหนดอัตราเวลาเฉลี่ยต่อ Step และเวลา Overhead ขั้นต่ำจาก Config
    if has_app_context() and current_app.config.get("ESTIMATED_SECONDS_PER_STEP"):
        seconds_per_step = float(current_app.config["ESTIMATED_SECONDS_PER_STEP"])
    else:
        seconds_per_step = float(getattr(Config, "ESTIMATED_SECONDS_PER_STEP", 0.15))

    if has_app_context() and current_app.config.get("ESTIMATED_BASE_OVERHEAD_SECONDS"):
        base_overhead = float(current_app.config["ESTIMATED_BASE_OVERHEAD_SECONDS"])
    else:
        base_overhead = float(getattr(Config, "ESTIMATED_BASE_OVERHEAD_SECONDS", 1.5))
    
    # 2. ปัจจัยตัวคูณตามขนาดความละเอียดของภาพ
    resolution_factor = (width * height) / (512.0 * 512.0)
    
    # 3. เวลาประมวลผลของภาพนี้เอง (Base Generation Time)
    base_generation_seconds = round(max(base_overhead, steps * seconds_per_step * resolution_factor), 1)
    
    # 4. ดึงจำนวนงานที่กำลังรอคิวอยู่ในระบบ
    with _waiting_counter_lock:
        current_waiting = _waiting_jobs_count

    # 5. เวลาที่ต้องรอคิว (สมมติงานเฉลี่ยในคิวใช้เวลาประมาณ 4.5 วินาทีต่องาน)
    queue_wait_seconds = round(current_waiting * 4.5, 1)
    
    # 6. เวลารวมทั้งหมดโดยประมาณ (เวลาในคิว + เวลาสร้างภาพจริง)
    total_estimated_seconds = round(base_generation_seconds + queue_wait_seconds, 1)

    return {
        "estimated_generation_seconds": base_generation_seconds,
        "queue_position": current_waiting,
        "queue_wait_seconds": queue_wait_seconds,
        "total_estimated_seconds": total_estimated_seconds,
    }


# ==============================================================================
# ฟังก์ชันติดต่อกับ AI Server (Models & txt2img)
# ==============================================================================
def fetch_available_models() -> list:
    """
    ฟังก์ชันดึงรายชื่อโมเดล Checkpoints ทั้งหมดจาก Stable Diffusion AI Server
    ยิงคำขอแบบ GET ไปที่ /sdapi/v1/sd-models
    
    :return: รายการโมเดลในรูปแบบ [{'title': '...', 'model_name': '...'}]
    """
    server_url = get_ai_server_url()
    try:
        # ยิงคำขอไปยัง AI Server ด้วย Timeout 10 วินาที
        response = requests.get(f"{server_url}/sdapi/v1/sd-models", timeout=10)
        
        # หาก AI Server ตอบกลับ HTTP 200 OK
        if response.status_code == 200:
            models_data = response.json()
            # จัดรูปแบบให้อยู่ในโครงสร้างมาตรฐาน LUMA
            return [
                {
                    "title": m.get("title") or m.get("model_name", "unknown"),
                    "model_name": m.get("model_name") or m.get("title", "unknown")
                }
                for m in models_data
            ]
        # กรณี AI Server ตอบสถานะข้อผิดพลาด
        raise AIServerErrorException(f"AI Server returned status code {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        # ปัญหาการเชื่อมต่อเครือข่ายไปยัง AI Server
        raise AIServerErrorException(f"Cannot connect to AI Server at {server_url}: {str(e)}")


def generate_sd_image(payload: dict) -> tuple:
    """
    ฟังก์ชันส่งคำขอสร้างรูปภาพไปยัง Stable Diffusion AI Server (/sdapi/v1/txt2img)
    
    ✨ ระบบจัดการคิวงานพร้อมกัน (Concurrency Queue Management):
    - เมื่อผู้ใช้หลายคนกดสร้างภาพพร้อมกัน คำขอจะถูกนำเข้าคิว
    - คำขอแต่ละงานจะรอเข้า GPU อย่างเป็นระเบียบ ไม่ชนกัน และไม่สูญหาย
    - จับเวลาจริงในการทำงานเพื่อส่งกลับเป็นค่าสถิติ
    
    :param payload: ข้อมูลพารามิเตอร์การสร้างภาพจากผู้ใช้งาน
    :return: Tuple ของ (base64_image_string, actual_duration_seconds, estimated_duration_seconds)
    """
    global _waiting_jobs_count
    server_url = get_ai_server_url()

    # 1. คำนวณเวลาประเมินล่วงหน้าก่อนเข้าคิว
    width = int(payload.get("width", 512))
    height = int(payload.get("height", 512))
    steps = int(payload.get("steps", 20))
    est_info = calculate_estimated_time(width=width, height=height, steps=steps)
    estimated_duration = est_info["total_estimated_seconds"]

    # 2. บันทึกเพิ่มจำนวนคิวงานที่กำลังรอในระบบ
    with _waiting_counter_lock:
        _waiting_jobs_count += 1
        current_queue_pos = _waiting_jobs_count

    logger.info("New generation request queued (Position: %d, Estimated: %.1fs)", current_queue_pos, estimated_duration)

    # 3. รอเข้าคิวเพื่อขอสิทธิ์การใช้งาน GPU (กำหนดไว้ 40 วินาที เพื่อให้รวมกับ HTTP Timeout 75s แล้วไม่เกิน 115s < Nginx 120s)
    lock_acquired = _gpu_lock.acquire(blocking=True, timeout=40)

    # 4. เมื่อได้รับสิทธิ์หรือหลุดจากคิว ให้ลดจำนวนงานที่รอลง
    with _waiting_counter_lock:
        _waiting_jobs_count = max(0, _waiting_jobs_count - 1)

    # หากรอคิวนานเกิน 40 วินาทีแล้วยังไม่ได้คิว ให้ตอบกลับ AI_SERVER_BUSY (409) ก่อน Nginx ตัด 504
    if not lock_acquired:
        logger.warning("Generation request timed out waiting for GPU lock (Server Busy)")
        raise AIServerBusyException("AI Server queue wait time exceeded (Server is busy)")

    logger.info("Acquired GPU lock. Sending txt2img request to AI Server: %s", server_url)

    # 5. เริ่มจับเวลาการประมวลผลจริง
    start_time = time.time()

    try:
        # 6. แปลงโครงสร้างพารามิเตอร์ให้ตรงตามที่ Stable Diffusion WebUI API กำหนด
        sd_payload = {
            "prompt": payload.get("prompt", ""),
            "negative_prompt": payload.get("negative_prompt", ""),
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": float(payload.get("cfg_scale", 7.0)),
            "seed": int(payload.get("seed", -1)),
            "sampler_name": payload.get("sampler") or payload.get("sampler_name") or "Euler a",
        }

        # หากมีการระบุชื่อโมเดล Checkpoint ให้ส่งไปใน override_settings
        checkpoint_name = payload.get("checkpoint")
        if checkpoint_name:
            sd_payload["override_settings"] = {
                "sd_model_checkpoint": checkpoint_name
            }

        # 7. ส่ง HTTP POST Request ไปยัง AI Server
        timeout_seconds = get_ai_server_timeout()
        response = requests.post(
            f"{server_url}/sdapi/v1/txt2img",
            json=sd_payload,
            timeout=timeout_seconds
        )

        # 8. ตรวจสอบผลลัพธ์จาก AI Server
        if response.status_code == 200:
            result_data = response.json()
            images_list = result_data.get("images", [])
            
            if images_list and len(images_list) > 0:
                # คำนวณเวลาที่ใช้ไปจริง (หน่วย: วินาที)
                actual_duration = round(time.time() - start_time, 2)
                logger.info("Image generated successfully in %.2fs (Estimated was: %.1fs)", actual_duration, estimated_duration)
                # ส่งคืน Base64 ของภาพแรก, เวลาที่ใช้จริง, และเวลาประเมิน
                return images_list[0], actual_duration, estimated_duration
                
            logger.error("AI Server returned HTTP 200 but image data array was empty")
            raise AIServerErrorException("AI Server returned empty image data")

        logger.error("AI Server returned unexpected HTTP status %d", response.status_code)
        raise AIServerErrorException(f"AI Server returned status code {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error("AI Server request timed out after %d seconds", get_ai_server_timeout())
        # กรณี AI Server ใช้เวลาเจนภาพนานเกินกำหนด
        raise AIServerTimeoutException(f"AI Server timed out after {get_ai_server_timeout()} seconds")
    except requests.exceptions.RequestException as e:
        logger.error("Network communication error with AI Server: %s", str(e))
        # กรณีเกิดปัญหาเครือข่ายเชื่อมต่อไม่ได้
        raise AIServerErrorException(f"AI Server communication error: {str(e)}")
    finally:
        # 9. ปลดปล่อย Lock บน GPU ทุกครั้ง เพื่อให้คำขอในคิวถัดไปเริ่มทำงานต่อได้ทันที
        _gpu_lock.release()
        logger.debug("GPU lock released")