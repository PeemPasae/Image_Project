# ==============================================================================
# ชื่อไฟล์: backend/run.py
# หน้าที่: จุดเริ่มต้นการทำงานของระบบ Backend (Application Entry Point)
# เกี่ยวข้องกับหน้าเว็บ: รันเซิร์ฟเวอร์เพื่อให้ Frontend และระบบทั้งหมดติดต่อสื่อสารได้
# ==============================================================================

import os
from app import create_app

# 1. สร้าง Flask Application Instance ผ่าน Factory Function
app = create_app()

if __name__ == "__main__":
    # 2. อ่านค่าพอร์ตจากตัวแปรสภาพแวดล้อม (.env) หรือใช้ค่าเริ่มต้นคือพอร์ต 5000
    port = int(os.getenv("PORT", 5000))
    
    # 3. แสดงข้อความแจ้งเตือนสถานะการเริ่มทำงานของเซิร์ฟเวอร์
    print(f"🚀 LUMA Backend Server is running on http://0.0.0.0:{port}")
    print(f"📡 API Base URL: http://localhost:{port}/api/v1")
    
    # 4. สั่งเริ่มทำงานบน Host '0.0.0.0' เพื่อรองรับการเชื่อมต่อทั้งจาก localhost และเครื่องอื่นในวง LAN
    app.run(host="0.0.0.0", port=port, debug=True)