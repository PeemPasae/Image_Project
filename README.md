# Luma — AI Image Generation Studio

เว็บแอปสร้างรูปภาพด้วย AI (Text-to-Image) ที่แยกเป็น 3 ส่วนคนละเครื่อง
โดยใช้ **Stable Diffusion WebUI (AUTOMATIC1111 / Forge)** เป็นเครื่องประมวลผลเบื้องหลัง

ผู้ใช้สมัครสมาชิก → เข้าสู่ระบบ → เลือก checkpoint + ตั้งค่า prompt → กด Generate
รูปที่ได้จะถูกเก็บลงประวัติของผู้ใช้แต่ละคน และย้อนกลับมาดูได้

---

## 1. สถาปัตยกรรม

```
[Frontend]                [Backend]                     [AI Server]
index.html      ──HTTP──> Flask :5000            ──API──> SD WebUI :8088
(static / nginx)          172.20.57.59                    172.20.57.51
                              │                               │
                              │  <────── base64 PNG ──────────┘
                              ▼
                        SQLite (database/app.db)
```

| ส่วน | เทคโนโลยี | เครื่อง / พอร์ต | หน้าที่ |
|---|---|---|---|
| Frontend | HTML + CSS + Vanilla JS (ไฟล์เดียว) | เสิร์ฟผ่าน nginx :80 | หน้า Login / Register / Generate / History |
| Backend | Python + Flask + flask-cors | `172.20.57.59:5000` | Auth, เรียก AI Server, บันทึกประวัติลง SQLite |
| Database | SQLite | ไฟล์ `database/app.db` | ตาราง `users`, `history` |
| AI Server | Stable Diffusion WebUI (`--api`) | `172.20.57.51:8088` | สร้างรูปจริงด้วย GPU |
| Reverse proxy | nginx | `172.20.57.59:80` | เสิร์ฟ frontend + proxy `/api/` ไป Flask |

> Frontend ไม่ได้คุยกับ AI Server ตรง ๆ — ทุกอย่างวิ่งผ่าน Backend เสมอ

---

## 2. โครงสร้างโฟลเดอร์

```
Image_Project/
├── frontend/
│   └── index.html          # ทั้งแอปอยู่ในไฟล์เดียว (5 หน้า + JS)
├── backend/
│   ├── app.py              # Flask API ทั้งหมด
│   ├── .env                # AI_SERVER_IP (ไม่ commit ค่าจริง)
│   └── ggg.py              # ไฟล์ว่าง (ยังไม่ได้ใช้)
├── database/
│   ├── schema.sql          # (ยังว่าง — ตารางถูกสร้างโดย init_db() ใน app.py)
│   └── app.db              # สร้างอัตโนมัติตอนรัน backend ครั้งแรก
├── nginx/
│   └── nginx.conf          # config สำหรับเครื่อง Backend
├── Ai Server/              # ค่าตั้ง + สคริปต์ทดสอบของเครื่อง GPU
│   ├── config/             # webui-user.sh / .bat (มี --api --listen --port 8088)
│   ├── scripts/            # check_server.py, test_txt2img.py
│   ├── models/             # ที่วาง checkpoint (ไฟล์จริงไม่ commit)
│   └── README.md           # ⭐ คู่มือฝั่ง AI Server อย่างละเอียด
└── README.md
```

---

## 3. การติดตั้งและรัน

### 3.1 AI Server (เครื่อง GPU — `172.20.57.51`)

ดูรายละเอียดเต็มที่ [`Ai Server/README.md`](Ai%20Server/README.md) โดยย่อคือ:

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
# ก๊อป config ทับ (Windows)
copy "..\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat
# วาง checkpoint .safetensors ลง models/Stable-diffusion/
webui-user.bat
```

ต้องเห็นบรรทัด `Running on local URL: http://0.0.0.0:8088` ถึงจะพร้อมใช้งาน

ตรวจสอบจากเครื่องอื่น:

```bash
curl http://172.20.57.51:8088/sdapi/v1/sd-models
# หรือ
python "Ai Server/scripts/check_server.py"
```

**ห้ามลบ flag `--api`, `--listen`, `--port 8088`** เพราะ Backend พึ่งพาโดยตรง

### 3.2 Backend (เครื่อง `172.20.57.59`)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (Linux: source venv/bin/activate)
pip install flask flask-cors requests python-dotenv
```

สร้างไฟล์ `backend/.env`:

```env
AI_SERVER_IP=http://172.20.57.51:8088
```

รัน:

```bash
python app.py          # ฟังที่ 0.0.0.0:5000
```

ตารางใน SQLite ถูกสร้างเองอัตโนมัติตอนสตาร์ท (`init_db()`) ไม่ต้องรัน `schema.sql`

ตรวจสอบ: `curl http://172.20.57.59:5000/health` → `{"status":"ok"}`

### 3.3 Frontend

ทดสอบเร็ว ๆ: เปิด `frontend/index.html` ด้วยเบราว์เซอร์บนเครื่อง Backend ได้เลย

ใช้งานจริงผ่าน nginx — แก้ `root` ใน `nginx/nginx.conf` ให้ชี้ path จริงของ `frontend/`
แล้วก๊อปไปวางใน `sites-available/` (Linux) หรือ `conf/` (Windows) จากนั้น reload

```nginx
location / { root /path/to/your/frontend; }   # ← แก้บรรทัดนี้
```

> Frontend คำนวณ URL ของ Backend อัตโนมัติจาก
> `` const API_BASE = `http://${window.location.hostname}:5000` ``
> ดังนั้นต้องเปิดเว็บด้วย **IP ของเครื่อง Backend** (`http://172.20.57.59`)
> ไม่ใช่ `file://` ถ้าจะให้เรียก API ได้ถูกเครื่อง

---

## 4. API ของ Backend

Base URL: `http://172.20.57.59:5000`

| Method | Endpoint | Body / Param | คำอธิบาย |
|---|---|---|---|
| GET | `/health` | — | เช็คว่า Backend รันอยู่ |
| POST | `/api/register` | `{username, password}` | สมัครสมาชิก (username ห้ามซ้ำ) |
| POST | `/api/login` | `{username, password}` | คืน `{id, username}` ถ้าถูกต้อง |
| GET | `/api/models` | — | รายชื่อ checkpoint จาก AI Server |
| POST | `/api/generate` | ดูด้านล่าง | สร้างรูป + บันทึกลงประวัติ |
| GET | `/api/history/<user_id>` | — | ประวัติของผู้ใช้คนนั้น (ใหม่→เก่า) |

### `POST /api/generate`

```json
{
  "user_id": 1,
  "prompt": "a cute cat, highly detailed",
  "negative_prompt": "blurry, bad quality",
  "checkpoint": "sd_xl_base_1.0",
  "width": 1024,
  "height": 1024,
  "steps": 20,
  "cfg_scale": 7,
  "sampler_name": "Euler a"
}
```

ตอบกลับ:

```json
{ "status": "success", "image": "data:image/png;base64,iVBORw0KG..." }
```

Backend เป็นคนเติม prefix `data:image/png;base64,` เอง — AI Server ส่งมาเป็น base64 เปล่า ๆ
timeout ของการเรียก AI Server ตั้งไว้ที่ **300 วินาที**

---

## 5. โครงสร้างฐานข้อมูล

```sql
users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT UNIQUE NOT NULL,
    password  TEXT NOT NULL
)

history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    prompt           TEXT NOT NULL,
    negative_prompt  TEXT,
    checkpoint       TEXT,
    image_base64     TEXT NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 6. แก้ปัญหาที่เจอบ่อย

| อาการ | สาเหตุที่พบบ่อย | วิธีแก้ |
|---|---|---|
| หน้าเว็บขึ้น "กำลังโหลด Models..." ค้าง | Backend ต่อ AI Server ไม่ได้ | รัน `python "Ai Server/scripts/check_server.py"` |
| `ไม่สามารถดึง Model จาก AI Server ได้` | webui ไม่ได้รัน / ลืม `--api` | ดู [`Ai Server/README.md`](Ai%20Server/README.md) ข้อ 6 |
| กด Generate แล้วไม่มีอะไรเกิดขึ้น | เปิดหน้าเว็บด้วย `file://` ทำให้ `API_BASE` ผิด | เปิดผ่าน `http://172.20.57.59` |
| CORS error ใน console | AI Server / Backend ไม่ได้อนุญาต origin นั้น | เช็ค `--cors-allow-origins` ใน `webui-user.bat` |
| `AI Server ใช้เวลานานเกินไป (Timeout)` | steps สูง / รูปใหญ่ / VRAM ไม่พอ | ลด steps, ลด 1024→512, เติม `--medvram` |
| ประวัติไม่ขึ้น | ยังไม่ login หรือ `user_id` ไม่ถูกส่ง | login ใหม่ |

**ลำดับการไล่ปัญหา:** AI Server (`check_server.py`) → Backend (`/health`) → Frontend (console ในเบราว์เซอร์)

---

## 7. หมายเหตุ / สิ่งที่ยังไม่เสร็จ

- **รหัสผ่านเก็บเป็น plain text** ใน SQLite และเทียบตรง ๆ ตอน login — ยังไม่มีการ hash และไม่มี session/token
- ยังไม่มี `backend/requirements.txt` (ตอนนี้ต้อง `pip install` เองตามข้อ 3.2)
- `database/schema.sql` ยังว่าง — ตารางถูกสร้างจาก `init_db()` ใน `app.py` แทน
- `backend/ggg.py` เป็นไฟล์ว่าง ยังไม่มีการใช้งาน
- IP ของ AI Server และ Backend ถูก hardcode ไว้ในหลายที่ (`app.py`, `nginx.conf`, `webui-user.bat`) — ถ้าเปลี่ยน IP ต้องแก้ทุกจุด
- รูปภาพถูกเก็บเป็น base64 ลงฐานข้อมูลโดยตรง ฐานข้อมูลจะโตเร็วเมื่อใช้งานมาก
- `debug=True` ใน `app.py` เหมาะกับการพัฒนาเท่านั้น ไม่ควรใช้ตอน deploy จริง

---

## 8. ผู้จัดทำ

| ชื่อ - นามสกุล | ชื่อเล่น | รหัสนักศึกษา | หน้าที่รับผิดชอบ |
|---|---|---|---|
|  | ไอซ์ |  | AI Server — ติดตั้ง/ดูแล Stable Diffusion WebUI, สคริปต์ทดสอบ |
|  | นาย |  | Backend — Flask API, ฐานข้อมูล SQLite, nginx |
|  | กร |  | Frontend — หน้าเว็บ Login / Generate / History |
|  |  |  |  |
|  |  |  |  |

> รายวิชา: Image Processing — โปรเจกต์ปลายภาค ปีการศึกษา 3 เทอม 1
