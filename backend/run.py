# ==============================================================================
# ชื่อไฟล์: backend/run.py
# หน้าที่: จุดเริ่มต้นการทำงานของระบบ Backend (Application Entry Point)
# สถาปัตยกรรม: รันบน "เครื่อง Backend แยกต่างหาก" เพื่อรอรับคำขอจาก Nginx Gateway
# ==============================================================================

import os
import sys
from app import create_app

# รองรับการแสดงผลข้อความภาษาไทย/UTF-8 บน Windows Console ป้องกันปัญหาฟอนต์เพี้ยน
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. สร้าง Flask Application Instance ผ่าน Factory Function
app = create_app()

if __name__ == "__main__":
    # 2. อ่านค่า host และ port จากตัวแปรสภาพแวดล้อม (.env) หรือใช้ค่าเริ่มต้น
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))

    # ปิด Debug Mode เพื่อความปลอดภัย (ห้ามเปิด Werkzeug debugger เมื่อเปิดรับทราฟฟิกข้าม LAN)
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1")
    
    # 3. แสดงข้อความแจ้งเตือนสถานะการเริ่มทำงานของเซิร์ฟเวอร์
    print("=" * 65)
    print(f"[*] LUMA Backend API Server is running on: http://{host}:{port}")
    print(f"[*] Debug Mode:      {'ON (Development only)' if debug else 'OFF (Production / Behind Proxy)'}")
    print(f"[*] Local Access:    http://127.0.0.1:{port}/api/v1")
    print(f"[*] Network Access:  Ready to receive requests from Nginx Gateway ({host}:{port})")
    print("=" * 65)
    
    # 4. สั่งเริ่มทำงานบน Host '0.0.0.0' เพื่อรับการเชื่อมต่อจาก Nginx ที่อยู่คนละเครื่อง
    app.run(host=host, port=port, debug=debug)