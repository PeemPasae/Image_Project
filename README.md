# LUMA — AI Image Generation System

ระบบสร้างรูปภาพด้วย AI (Text-to-Image) แบ่งเป็น 3 ชั้นแยกเครื่องกันได้
โดยใช้ **Stable Diffusion WebUI (AUTOMATIC1111 / Forge)** เป็นตัวประมวลผลเบื้องหลัง

ผู้ใช้สมัคร/เข้าสู่ระบบด้วย JWT → ตั้งค่า prompt แล้วสั่งสร้างรูป → รูปถูกเซฟลงดิสก์ฝั่ง Backend
และบันทึกลงฐานข้อมูล ดูย้อนหลังได้ในหน้า History เฉพาะของตัวเอง

---

## 1. สถาปัตยกรรม

```
[Frontend]                    [Backend]                      [AI Server]
React + Vite      ──axios──>  Flask (app factory)  ──HTTP──>  SD WebUI --api
:5173                         :5000  /api/v1/*                :8088
                                  │                               │
                                  │  <──── base64 PNG ────────────┘
                                  ├── เซฟไฟล์ .png ลง backend/app/uploads/
                                  └── เขียน metadata ลง SQLite (SQLAlchemy)
```

| ชั้น | เทคโนโลยี | พอร์ต | โฟลเดอร์ |
|---|---|---|---|
| Frontend | React 18 + Vite 5 + React Router + axios | 5173 | `frontend/luma-frontend/` |
| Backend | Flask 3 + Flask-SQLAlchemy + PyJWT | 5000 | `backend/` |
| Database | SQLite | — | `database/` + `instance/` |
| AI Server | Stable Diffusion WebUI (`--api`) | 8088 | `Ai Server/` (config + สคริปต์ทดสอบ) |

- Frontend คุยกับ Backend เท่านั้น ไม่เคยเรียก AI Server ตรง ๆ
- ทุก response ห่อด้วย envelope `{ success, data }` หรือ `{ success, error }`
- รูปภาพ **ไม่ได้ส่งเป็น base64** แล้ว — `POST /generate` คืน `image_url` ให้ไปดึงต่อแบบ authenticated blob

---

## 2. โครงสร้างโฟลเดอร์

```
Image_Project/
├── backend/
│   ├── run.py                    # จุดรัน: create_app() แล้ว app.run(port=5000)
│   ├── config.py                 # คลาส Config (ยังไม่ถูกเรียกใช้ — ดูหัวข้อ 7)
│   ├── requirements.txt
│   ├── .env                      # JWT_SECRET_KEY, AI_SERVER_URL
│   ├── app/
│   │   ├── __init__.py           # app factory + register blueprint + db.create_all()
│   │   ├── extensions.py         # db = SQLAlchemy()
│   │   ├── models/generation.py  # ตาราง generations
│   │   ├── routes/               # auth, sd, history, images, profile
│   │   ├── services/ai_client.py # ตัวคุยกับ SD WebUI + Mutex กันยิงซ้อน
│   │   ├── middleware/jwt_auth.py# decorator @token_required
│   │   └── utils/error_codes.py  # success_response / error_response
│   └── Testcase/                 # pytest: test_auth, test_history, test_sd
├── frontend/
│   ├── luma-frontend/            # ตัวจริง (React) — มี README ของตัวเอง
│   │   ├── src/api/client.js     # axios client กลาง แกะ envelope + ใส่ JWT
│   │   ├── src/context/          # AuthContext, ThemeContext
│   │   ├── src/pages/            # Login, Register, Home, Generate, Result, History, Profile, Setting
│   │   └── vite.config.js
│   └── index.html                # เวอร์ชันเดโมเก่า (single-file) — เลิกใช้แล้ว
├── database/
│   ├── schema.sql                # users + generations (สำหรับ init_db.py)
│   ├── init_db.py                # สร้าง database/app.db จาก schema.sql
│   └── Test1..3_*.py             # สคริปต์ทดสอบ DB
├── nginx/nginx.conf              # reverse proxy (ยังเป็น config ของเวอร์ชันเก่า)
└── Ai Server/                    # ดู README แยกในโฟลเดอร์นี้
    ├── config/webui-user.bat|sh  # มี --api --listen --port 8088
    ├── scripts/check_server.py   # health check ก่อนแจ้งทีม
    └── models/                   # ที่วาง checkpoint (ไฟล์จริงไม่ commit)
```

---

## 3. การติดตั้งและรัน

### 3.1 AI Server (เครื่อง GPU)

ดูละเอียดที่ [`Ai Server/README.md`](Ai%20Server/README.md) โดยย่อ:

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
copy "..\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat
webui-user.bat
```

**flag ที่ห้ามขาด:** `--api` (ไม่งั้น `/sdapi/v1/*` ได้ 404), `--listen` (ไม่งั้นเครื่องอื่นเรียกไม่ถึง), `--port 8088`

ตรวจว่าพร้อม:

```bash
curl http://127.0.0.1:8088/sdapi/v1/sd-models
python "Ai Server/scripts/check_server.py"
```

### 3.2 Backend

```bash
cd backend
pip install -r requirements.txt
pip install Flask-SQLAlchemy requests
```

บรรทัดที่สองจำเป็น เพราะ 2 แพ็กเกจนี้ยังไม่อยู่ใน `requirements.txt` ทั้งที่โค้ดเรียกใช้จริง

ตั้งค่า `backend/.env`:

```env
PORT=5000
JWT_SECRET_KEY=my_super_secret_key_12345
AI_SERVER_URL=http://127.0.0.1:8088
```

> **ข้อควรระวัง 2 ข้อ**
>
> 1. ยังไม่มีโค้ดตรงไหนเรียก `load_dotenv()` เลย ทำให้ไฟล์ `.env` **ไม่ถูกโหลดจริง**
>    ต้อง set เป็น environment variable เองก่อนรัน ไม่งั้น endpoint ที่ต้องใช้ token จะพัง 500
>
>    ```powershell
>    $env:JWT_SECRET_KEY = "my_super_secret_key_12345"
>    ```
>
> 2. `AI_SERVER_URL` ใน `.env` ยังไม่มีผล เพราะ `app/services/ai_client.py:7` hardcode ไว้เป็น
>    `http://172.20.56.221:8088` ถ้ารัน SD ในเครื่องตัวเองต้องแก้บรรทัดนั้นเป็น `http://127.0.0.1:8088`

รัน:

```bash
python run.py
```

ฟังที่ `0.0.0.0:5000` ตอนสตาร์ท SQLAlchemy จะสร้าง `instance/database.db` ให้เองอัตโนมัติ (`db.create_all()`)

### 3.3 Frontend

ต้องมี **Node.js** ติดตั้งไว้ก่อน

```bash
cd frontend/luma-frontend
npm install
copy .env.example .env
npm run dev
```

เปิด `http://localhost:5173`

ค่าใน `.env` ของ frontend:

| ตัวแปร | ความหมาย |
|---|---|
| `VITE_API_BASE_URL` | ที่อยู่ Backend เช่น `http://localhost:5000/api/v1` |
| `VITE_MOCK_MODE` | `true` = เดินดูทุกหน้าด้วยข้อมูลปลอม ไม่ต้องมี Backend (มีแถบเหลืองเตือน) |

**ถ้า Backend ยังไม่พร้อม** ให้ตั้ง `VITE_MOCK_MODE=true` แล้ว `npm run dev` จะเดินดูได้ครบทุกหน้า
Login/Register กรอกอะไรก็เข้าได้ — วิธีนี้ใช้ทำเดโมหน้าเว็บได้ทันทีโดยไม่ต้องรอฝั่งอื่น

รันเทส contract ของ frontend:

```bash
npm test
```

---

## 4. API (Backend)

Base URL: `http://localhost:5000/api/v1`
🔒 = ต้องส่ง header `Authorization: Bearer <token>`

| Method | Endpoint | สถานะ | คำอธิบาย |
|---|---|---|---|
| POST | `/register` | ยังไม่ register blueprint | สมัครสมาชิก (email + password, hash ด้วย Werkzeug) |
| POST | `/login` | ยังไม่ register blueprint | คืน JWT อายุ 24 ชม. |
| GET | `/profile` 🔒 | ยังไม่ register blueprint | ข้อมูลผู้ใช้ |
| GET | `/models` | ยังไม่มี route | Frontend เรียกอยู่ แต่ Backend ยังไม่ได้ทำ |
| POST | `/generate` 🔒 | ใช้ได้ | สร้างรูป → คืน `{id, prompt, image_url}` |
| GET | `/images/<id>` 🔒 | ใช้ได้ | ส่งไฟล์ PNG binary (เช็ค ownership กัน IDOR) |
| GET | `/history` 🔒 | ใช้ได้ | ประวัติของตัวเอง รองรับ `?page=&limit=` |
| DELETE | `/history/<id>` 🔒 | ใช้ได้ | ลบทั้งไฟล์บนดิสก์และ record ใน DB |

รายละเอียดฝั่ง client อยู่ใน [`frontend/luma-frontend/README.md`](frontend/luma-frontend/README.md)

### รูปแบบ response

```jsonc
// สำเร็จ
{ "success": true,  "data": { "id": 1, "prompt": "...", "image_url": "/api/v1/images/1" } }

// ผิดพลาด
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "Prompt is required" } }
```

### ข้อกำหนดฝั่ง AI Server

- timeout ตอนเรียก SD = **75 วินาที**
- มี **Mutex Lock** ใน `ai_client.py` — ถ้ามีคนกำลังเจนรูปอยู่ request ใหม่จะถูก reject ทันที ไม่เข้าคิว

---

## 5. ฐานข้อมูล

ตาราง `generations` (ผ่าน SQLAlchemy — `app/models/generation.py`)

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER | มาจาก JWT payload |
| `prompt` / `negative_prompt` | VARCHAR(2000) | |
| `checkpoint` / `sampler` | VARCHAR | |
| `width` / `height` / `steps` / `seed` | INTEGER | |
| `cfg_scale` | FLOAT | |
| `image_path` | VARCHAR(500) | path ไฟล์จริงบนดิสก์ ไม่ใช่ base64 |
| `created_at` | DATETIME | |

ตาราง `users` มีนิยามอยู่ใน `database/schema.sql` แต่ยังไม่มี SQLAlchemy model
(`app/models/user.py` เป็นไฟล์ว่าง) — ตอนนี้ `routes/auth.py` ยังเก็บผู้ใช้ไว้ใน `MOCK_USERS_DB` ในหน่วยความจำ

สร้าง DB จาก schema โดยตรง:

```bash
python database/init_db.py
```

---

## 6. แก้ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|---|---|---|
| `ModuleNotFoundError: flask_sqlalchemy` | ขาด dependency ที่ไม่อยู่ใน requirements.txt | `pip install Flask-SQLAlchemy requests` |
| `RuntimeError: JWT_SECRET_KEY is not configured` | `.env` ไม่ถูกโหลด | set environment variable เอง (ดูหัวข้อ 3.2) |
| `ERR_CONNECTION_REFUSED` ที่ `:5000` | Backend ไม่ได้รัน | `python backend/run.py` |
| เปิด `http://localhost:5000/` แล้วได้ 404 | พอร์ต 5000 คือ API ไม่ใช่หน้าเว็บ | หน้าเว็บอยู่ที่ `:5173` |
| `/login`, `/register` ได้ 404 | blueprint ยังไม่ถูก register | ดูหัวข้อ 7 |
| `AI Server is unreachable` | SD ไม่ได้รัน / URL ผิดเครื่อง | เช็ค `ai_client.py:7` + `check_server.py` |
| `AI Server is currently busy` | มี request เจนรูปค้างอยู่ | รอให้รูปก่อนหน้าเสร็จก่อน |
| `AI Server timed out after 75 seconds` | steps สูง / รูปใหญ่ / VRAM ไม่พอ | ลด steps, ลดขนาด, เติม `--medvram` |
| CORS error | origin ไม่ตรงที่อนุญาต | เช็ค `--cors-allow-origins` ใน `webui-user.bat` |

**ลำดับไล่ปัญหา:** AI Server (`/sdapi/v1/sd-models`) → Backend (`python run.py` ขึ้นมั้ย) → Frontend (F12 ดู Console/Network)

---

## 7. สถานะปัจจุบัน / สิ่งที่ยังไม่เสร็จ

รวมจุดที่โค้ดยังไม่ต่อกันสนิท — จำเป็นต้องรู้ก่อนรัน

### ต้องแก้ก่อนถึงจะรันครบวงจรได้

- `requirements.txt` ขาด `Flask-SQLAlchemy` และ `requests` ทั้งที่โค้ดเรียกใช้จริง
- ไม่มีที่ไหนเรียก `load_dotenv()` → ไฟล์ `.env` ไม่เคยถูกอ่าน
- `app/__init__.py` register แค่ `sd_bp` กับ `history_bp` — **`auth_bp`, `profile_bp`, `images_bp` ยังไม่ถูก register**
  ทำให้ล็อกอินไม่ได้ จึงยังไม่มีทางได้ JWT ไปเรียก endpoint อื่นที่ติด 🔒
- ยังไม่มี route `GET /models` ทั้งที่ Frontend เรียก (มีฟังก์ชัน `fetch_available_models()` เตรียมไว้แล้วใน `ai_client.py`)

### ความไม่สอดคล้องที่ควรเก็บกวาด

- `config.py` เขียนไว้ครบแต่ไม่มีใครเรียก (`app.config.from_object(Config)` ไม่ถูกใช้) และชื่อตัวแปรไม่ตรงกัน —
  `config.py` อ่าน `JWT_SECRET` / `AI_SERVER_URL` แต่ `.env` และ `jwt_auth.py` ใช้ `JWT_SECRET_KEY`
- `ai_client.py` hardcode IP ของ AI Server ไว้ในโค้ด แทนที่จะอ่านจาก `.env`
- มีไฟล์ DB 2 ที่: `instance/database.db` (SQLAlchemy สร้างเอง มีแค่ `generations`)
  กับ `database/app.db` (จาก `init_db.py` มีทั้ง `users` และ `generations`)
- `routes/images.py` ยังอ้าง `MOCK_GENERATIONS_DB` ที่ถูกลบไปจาก `sd.py` แล้ว — import จะพังถ้า register blueprint นี้
  (ฟังก์ชันซ้ำกับ `/images/<id>` ใน `sd.py` ที่ใช้ DB จริงแล้ว)
- `routes/auth.py` ยังเก็บ user ใน dict ในหน่วยความจำ ข้อมูลหายทุกครั้งที่ restart
- `frontend/index.html` เวอร์ชันเก่ายังค้างอยู่ ทำให้สับสนกับตัวจริงใน `luma-frontend/`
- `nginx/nginx.conf` ยังชี้ไปโครงสร้างเดิม (proxy `/api/` ไม่ใช่ `/api/v1/` และเสิร์ฟ static html) ยังไม่รองรับ build ของ Vite
- `debug=True` ใน `run.py` เหมาะกับตอนพัฒนาเท่านั้น

### ยังไม่ทำใน V1 (ตั้งใจ)

- เปลี่ยนรหัสผ่าน — ยังไม่มี endpoint ปุ่มถูก disable ไว้
- หน้า Setting เก็บค่าใน `localStorage` อย่างเดียว ไม่ sync ขึ้น Backend

---

## 8. ผู้จัดทำ

| ชื่อ - นามสกุล | ชื่อเล่น | รหัสนักศึกษา | หน้าที่รับผิดชอบ |
|---|---|---|---|
|  | ไอซ์ |  | AI Server — ติดตั้ง/ดูแล Stable Diffusion WebUI, สคริปต์ทดสอบ |
|  | นาย |  | Backend — Flask API, JWT, เชื่อม AI Server |
|  | กร |  | Frontend — React + Vite, หน้า Generate / History / Setting |
|  | ภีม |  | Database — schema, SQLAlchemy model, test script |
|  |  |  |  |

> รายวิชา: Image Processing — โปรเจกต์ปลายภาค ปีการศึกษา 3 เทอม 1
