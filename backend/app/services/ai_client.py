# นำเข้า threading สำหรับจัดการ Mutex Lock เพื่อเช็กสถานะการทำงานของ AI Server
import threading
# นำเข้า requests สำหรับส่ง HTTP Call ไปยัง AI Server
import requests

# URL ของ AI Server อัปเดตตาม IP ใหม่: 172.20.56.221:8088
AI_SERVER_URL = "http://172.20.56.221:8088"

# สร้าง Mutex Lock วัตถุส่วนกลางสำหรับเช็กว่ามี Request กำลังเจนรูปอยู่หรือไม่
_ai_lock = threading.Lock()


class AIServerBusyException(Exception):
    """Exception กำหนดขึ้นเองเมื่อ AI Server กำลังติดงานอื่นอยู่"""
    pass


class AIServerTimeoutException(Exception):
    """Exception กำหนดขึ้นเองเมื่อ AI Server ประมวลผลเกินเวลาที่กำหนด"""
    pass


class AIServerErrorException(Exception):
    """Exception กำหนดขึ้นเองเมื่อ AI Server คืนค่าข้อผิดพลาดกลับมา"""
    pass


def fetch_available_models():
    """ฟังก์ชันดึงรายชื่อ Checkpoints/Models จาก AI Server"""
    try:
        response = requests.get(f"{AI_SERVER_URL}/sdapi/v1/sd-models", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            # ดึง title และ model_name ป้องกันค่า None
            return [
                {
                    "name": m.get("model_name") or m.get("title"),
                    "title": m.get("title") or m.get("model_name")
                } 
                for m in models_data
            ]
        raise AIServerErrorException("Failed to fetch models from AI Server")
    except requests.exceptions.RequestException:
        raise AIServerErrorException("AI Server is unreachable")


def generate_sd_image(payload):
    """ฟังก์ชันส่งพารามิเตอร์ไปสั่งสร้างรูปภาพที่ AI Server"""
    # พยายามขอถือ Lock แบบไม่รอคอย (blocking=False) ถ้าถือ Lock ไม่ได้แสดงว่ามีงานค้างอยู่
    acquired = _ai_lock.acquire(blocking=False)
    # ถ้าไม่ได้ Lock ให้ Reject ทันทีด้วย Exception (ไม่ทำ Queue)
    if not acquired:
        raise AIServerBusyException("AI Server is currently busy with another request")

    try:
        # ยิง POST Request ไปที่ /sdapi/v1/txt2img พร้อมตั้งค่า Timeout 75 วินาที
        response = requests.post(
            f"{AI_SERVER_URL}/sdapi/v1/txt2img",
            json=payload,
            timeout=75
        )
        # หากได้ HTTP Status 200
        if response.status_code == 200:
            # แปลง Response เป็น JSON
            data = response.json()
            # ดึงรายการรูปภาพในรูป Base64 string
            images = data.get("images", [])
            # หากมีรูปส่งมา ให้คืนค่า Base64 ของรูปแรก
            if images:
                return images[0]
            # ถ้าไม่มีรูปส่งกลับมา ให้โยนข้อผิดพลาด
            raise AIServerErrorException("No image generated from AI Server")
        # กรณีได้ Status Code อื่นๆ
        raise AIServerErrorException(f"AI Server returned status code {response.status_code}")
    except requests.exceptions.Timeout:
        # หากเกิด Timeout เกิน 75 วินาที
        raise AIServerTimeoutException("AI Server timed out after 75 seconds")
    except requests.exceptions.RequestException as e:
        # หากเกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย
        raise AIServerErrorException(f"AI Server connection error: {str(e)}")
    finally:
        # ปลดปล่อย Lock ทุกครั้ง ไม่ว่าจะทำงานสำเร็จหรือเกิด Exception เพื่อเปิดรับ Request ถัดไป
        _ai_lock.release()