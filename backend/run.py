# โหลด backend/.env เข้า environment ก่อนอ่านค่าใด ๆ
# (Flask โหลด .env ให้เองตอน app.run() แต่เราต้องอ่าน HOST/DEBUG ก่อนหน้านั้น)
from dotenv import load_dotenv
load_dotenv()

import os

# นำเข้าฟังก์ชัน create_app จากโมดูล app
from app import create_app

# สร้าง App Instance
app = create_app()

# คำสั่งสั่งรันโปรเจกต์
if __name__ == "__main__":
    # ค่า default = 127.0.0.1 → Flask รับได้เฉพาะจาก nginx บนเครื่องเดียวกัน
    # คนอื่นในวง LAN เข้าพอร์ต 5000 ตรง ๆ ไม่ได้ ต้องผ่าน nginx :80 เท่านั้น
    # ถ้าทดสอบข้ามเครื่องโดยไม่มี nginx ให้ตั้ง HOST=0.0.0.0 ใน .env (ชั่วคราวเท่านั้น)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))

    # debug=True เปิด Werkzeug debugger (รัน Python บนเซิร์ฟเวอร์ได้จากหน้าเว็บ)
    # ห้ามเปิดตอน bind 0.0.0.0 หรือตอนอยู่หลัง nginx → เปิดได้ด้วย FLASK_DEBUG=1 ใน .env
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    app.run(host=host, port=port, debug=debug)
