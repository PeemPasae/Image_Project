# นำเข้าฟังก์ชัน create_app จากโมดูล app
from app import create_app

# สร้าง App Instance
app = create_app()

# คำสั่งสั่งรันโปรเจกต์
if __name__ == "__main__":
    # รันบน host 0.0.0.0 เพื่อเปิดรับ request จาก Frontend IP 172.20.56.225 ที่พอร์ต 5000
    app.run(host="0.0.0.0", port=5000, debug=True)