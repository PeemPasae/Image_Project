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
    # 2. อ่านค่าพอร์ตจากตัวแปรสภาพแวดล้อม (.env) หรือใช้ค่าเริ่มต้นคือพอร์ต 5000
    port = int(os.getenv("PORT", 5000))
    
    # 3. แสดงข้อความแจ้งเตือนสถานะการเริ่มทำงานของเซิร์ฟเวอร์
    print("=" * 65)
    print(f"[*] LUMA Backend API Server is running on: http://0.0.0.0:{port}")
    print(f"[*] Local Access:    http://127.0.0.1:{port}/api/v1")
    print(f"[*] Network Access:  Ready to receive requests from Nginx Gateway")
    print("=" * 65)
    
    # 4. สั่งเริ่มทำงานบน Host '0.0.0.0' 
    # เหตุผลที่ต้องใช้ '0.0.0.0': 
    # เนื่องจาก Nginx อยู่บน "เครื่องอื่น" การตั้งเป็น 0.0.0.0 จะทำให้ Flask 
    # ยอมรับการเชื่อมต่อข้ามเครื่องผ่าน IP ของวงแลนหรือเน็ตเวิร์กได้
    app.run(host="0.0.0.0", port=port, debug=True)