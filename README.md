# LUMA — AI Image Generation System

> Project Final · รายวิชา Image Processing (ปี 3 เทอม 1) · ทีม 4 คน

ระบบสร้างรูปภาพด้วย AI (Text-to-Image) แบบ **web-based** ผู้ใช้สมัคร/เข้าสู่ระบบ → พิมพ์ prompt
และตั้งค่า (checkpoint, sampler, ขนาด, steps, CFG, seed) → **Flask Backend** ส่งต่อไปยัง
**Stable Diffusion AI Server** → รูปที่ได้ถูกเซฟลงดิสก์ + บันทึกประวัติไว้ในฐานข้อมูล
ผู้ใช้ดูย้อนหลัง ดาวน์โหลด ลบ หรือสร้างซ้ำได้ (เฉพาะรูปของตัวเอง)

**หลักการที่ทั้งทีมยึด:** Browser คุยผ่าน **Nginx** → Frontend คุยกับ Backend เท่านั้น —
Backend เป็นตัวกลางเดียวที่แตะ Database และ AI Server

---

## 👥 ทีมผู้จัดทำ

| ชื่อเล่น | บทบาท | ความรับผิดชอบหลัก | โฟลเดอร์ |
|---|---|---|---|
| **นาย** | Backend Developer | Flask REST API, JWT Authentication, เชื่อม Database + AI Server, Generate / History / Images API, Error Handling, Testcase (pytest) | `backend/` |
| **ไอซ์** | AI Engineer + Infra (Nginx) | Stable Diffusion WebUI (`--api`), จัดการ Model / Checkpoint, สคริปต์ health-check / ทดสอบ txt2img, **ตั้งค่า Nginx Reverse Proxy** (เสิร์ฟ Frontend + proxy `/api/` ไป Flask) | `Ai Server/`, `nginx/` |
| **ภีม** | Database Developer | ออกแบบ Schema `users` / `generations`, Relationship + Foreign Key, สคริปต์สร้าง/ทดสอบ DB, SQLAlchemy Models | `database/` |
| **กร** | Frontend Developer | UI/UX, React + Vite, หน้า Login / Register / Home / Generate / Result / History / Profile / Setting, Theme, Mock Mode, API Integration | `frontend/luma-frontend/` |

> เติม ชื่อ-นามสกุล และ รหัสนักศึกษา ของแต่ละคนได้ตามสะดวก

---

## 🏗️ สถาปัตยกรรม

```
                    ┌──────────────────────────────────────────┐
  Browser ──HTTP──▶ │  Nginx :80  (ไอซ์)                        │
                    │   /       → ไฟล์ static ของ Frontend (dist) │
                    │   /api/   → proxy → Flask 127.0.0.1:5000   │
                    └───────────────────┬──────────────────────┘
                                        ▼
                            Flask Backend :5000  (นาย)
                             JWT · Validation · Lock
                      ┌─────────────────┴─────────────────┐
                      ▼                                   ▼
            SQLite Database (ภีม)              AI Server :8088 (ไอซ์)
            users / generations                SD WebUI --api (A1111 / Forge)
            + ไฟล์ PNG ใน app/uploads/          POST /sdapi/v1/txt2img → Base64 PNG
```

**Generation flow (end-to-end)**

```
User → Frontend → POST /api/v1/generate (Bearer JWT) → Nginx → Flask
     → POST /sdapi/v1/txt2img → AI Server (Stable Diffusion)
     → Base64 PNG → Flask decode + เซฟไฟล์ลง app/uploads/ + INSERT generations
     → ตอบ image_url → Frontend ดึงรูปผ่าน GET /api/v1/images/:id (แนบ JWT, โหลดเป็น Blob)
```

---

## 🧰 Tech Stack

| ชั้น | เทคโนโลยี | พอร์ต | โฟลเดอร์ |
|---|---|---|---|
| **Reverse Proxy** | Nginx | 80 | `nginx/` |
| **Frontend** | React 18 + Vite 5 + React Router 6 + Axios, ทดสอบด้วย Vitest | 5173 (dev) | `frontend/luma-frontend/` |
| **Backend** | Python + Flask 3 + Flask-SQLAlchemy + Flask-CORS + PyJWT + Werkzeug | 5000 | `backend/` |
| **Database** | SQLite | — | `database/`, `backend/instance/` |
| **AI Server** | Stable Diffusion WebUI (AUTOMATIC1111 / Forge) `--api --listen` | 8088 | `Ai Server/` |

---

## 📁 โครงสร้างโปรเจกต์

```
Image_Project/
├── nginx/                          # (ไอซ์)
│   ├── nginx.conf                  # server :80 — เสิร์ฟ Frontend + proxy /api/ → Flask
│   └── luma_dev.htpasswd           # บัญชี basic-auth สำหรับ dev (ยังไม่ได้ผูกใน nginx.conf)
├── Ai Server/                      # (ไอซ์) — ไม่ได้เก็บตัว webui เก็บแค่ config + สคริปต์ + เอกสาร
│   ├── config/webui-user.bat|.sh   # COMMANDLINE_ARGS: --api --listen --port 8088 ...
│   ├── scripts/check_server.py     # health check: options / sd-models / samplers
│   ├── scripts/test_txt2img.py     # ยิง txt2img ตรง ไม่ผ่าน Backend
│   ├── models/                     # วาง checkpoint (ไฟล์จริงไม่ commit)
│   └── README.md                   # คู่มือ AI Server ฉบับเต็ม
├── backend/                        # (นาย)
│   ├── run.py                      # entry point: create_app() → :5000
│   ├── config.py
│   ├── requirements.txt
│   ├── .env                        # JWT_SECRET_KEY, AI_SERVER_URL (ห้าม commit)
│   ├── app/
│   │   ├── __init__.py             # app factory + register blueprints + db.create_all()
│   │   ├── extensions.py           # db = SQLAlchemy()
│   │   ├── models/generation.py    # Generation model (+ to_dict)
│   │   ├── routes/                 # auth, sd (generate/images), history, profile, images
│   │   ├── services/ai_client.py   # เรียก SD WebUI + threading.Lock กันเจนซ้อน
│   │   ├── middleware/jwt_auth.py  # @token_required
│   │   └── utils/error_codes.py    # success_response / error_response + error codes
│   └── Testcase/                   # pytest: auth, sd, history
├── database/                       # (ภีม)
│   ├── schema.sql                  # DDL: users + generations + index
│   ├── init_db.py                  # สร้าง app.db จาก schema.sql
│   └── Test1..3_*.py               # สคริปต์ทดสอบ insert / select
└── frontend/
    ├── index.html                  # prototype หน้าเดียว (เวอร์ชันแรก ก่อนย้ายไป React)
    └── luma-frontend/              # (กร) React + Vite — ตัวจริง
        └── src/
            ├── api/client.js       # axios กลาง: แนบ JWT, แกะ envelope, timeout generate 90s
            ├── api/mockData.js     # ข้อมูลปลอมสำหรับ Mock Mode
            ├── context/            # AuthContext, ThemeContext
            ├── components/         # Layout, ProtectedRoute, AuthImage, MockModeBanner
            ├── pages/              # Login, Register, Home, Generate, Result, History, Profile, Setting
            ├── themes/presets.js   # ธีมสี
            └── test/contract.test.js
```

---

## 🚀 วิธีรัน (Quick Start)

รันได้ทั้งแบบ **เครื่องเดียว** และ **แยกเครื่องในวง LAN** — ต่างกันแค่ IP ใน `.env` / `nginx.conf`

**สิ่งที่ต้องมี:** Python 3.10+, Node.js 18+, Nginx, เครื่องที่มี NVIDIA GPU (≥ 6 GB VRAM) สำหรับ AI Server

### 1) AI Server — ไอซ์

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
copy "..\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat   # Linux: cp .../webui-user.sh ./
# วาง checkpoint .safetensors ลง models/Stable-diffusion/
webui-user.bat                                                          # Linux: ./webui.sh
```

Flag ที่ **ห้ามลบ**: `--api` (เปิด `/sdapi/v1/*`) · `--listen` (ให้เครื่องอื่นเรียกได้) · `--port 8088`

ตรวจความพร้อม:

```bash
cd "Ai Server"
pip install -r scripts/requirements.txt
python scripts/check_server.py --url http://127.0.0.1:8088
python scripts/test_txt2img.py -p "a cat astronaut" --steps 20
```

> ถ้า 2 สคริปต์นี้ผ่าน แต่หน้าเว็บสร้างรูปไม่ได้ → ปัญหาอยู่ฝั่ง Backend/Frontend
> รายละเอียดเต็ม + ตารางแก้ปัญหา ดู [`Ai Server/README.md`](Ai%20Server/README.md)

### 2) Database — ภีม (ไม่บังคับ)

Backend สร้างตารางให้อัตโนมัติตอนสตาร์ท (`db.create_all()` → `backend/instance/database.db`)
ถ้าต้องการสร้าง DB แยกจาก schema ต้นฉบับเพื่อทดสอบ:

```bash
cd database
python init_db.py          # สร้าง/อัปเดต database/app.db จาก schema.sql
python Test1_create_user.py
python Test3_select_all.py
```

### 3) Backend — นาย

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                 # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install flask-sqlalchemy requests  # ยังไม่ได้อยู่ใน requirements.txt
```

สร้าง `backend/.env`:

```env
PORT=5000
JWT_SECRET_KEY=<ค่าลับของตัวเอง>   # python -c "import secrets; print(secrets.token_urlsafe(48))"
AI_SERVER_URL=http://127.0.0.1:8088
```

```bash
python run.py              # ฟังที่ http://0.0.0.0:5000
```

### 4) Frontend — กร

```bash
cd frontend/luma-frontend
npm install
copy .env.example .env     # Linux/macOS: cp .env.example .env
npm run dev                # dev server: http://localhost:5173
npm run build              # สร้าง dist/ ไว้ให้ Nginx เสิร์ฟ
npm test                   # Vitest — contract test ของ api/client.js
```

| ตัวแปร `.env` | ความหมาย |
|---|---|
| `VITE_API_BASE_URL` | ที่อยู่ Backend เช่น `http://localhost:5000/api/v1` (ถ้าผ่าน Nginx ใช้ `/api/v1` ได้เลย) |
| `VITE_MOCK_MODE` | `true` = เดินดูทุกหน้าด้วยข้อมูลปลอม ไม่ต้องมี Backend (มีแบนเนอร์เหลืองเตือน) · `false` = ต่อ Backend จริง |

### 5) Nginx — ไอซ์

`nginx/nginx.conf` เป็นบล็อก `server` ที่รวม Frontend และ Backend ไว้หลังพอร์ต 80 เดียว:

```nginx
server {
    listen 80;
    server_name 172.20.57.59;          # IP เครื่องที่รัน Nginx + Backend

    client_max_body_size 100M;
    proxy_read_timeout 600s;           # เผื่อ /generate ที่ใช้เวลานาน

    location / {                       # Frontend (React build)
        root /path/to/your/frontend;   # ← เปลี่ยนเป็น path ของ frontend/luma-frontend/dist
        index index.html;
        try_files $uri $uri/ /index.html;   # SPA fallback ให้ React Router
    }

    location /api/ {                   # Backend
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

ขั้นตอนใช้งาน:

1. `npm run build` ใน `frontend/luma-frontend` แล้วแก้ `root` ให้ชี้ไปที่โฟลเดอร์ `dist`
2. ตั้ง `VITE_API_BASE_URL=/api/v1` ก่อน build เพื่อให้ Frontend เรียก API ผ่าน origin เดียวกัน (ไม่ติด CORS)
3. นำไฟล์ไปไว้ใน config ของ Nginx (เช่น `include` ใน `nginx.conf` หลัก หรือวางใน `conf.d/` / `sites-enabled/`)
4. ตรวจและโหลด config ใหม่:
   ```bash
   nginx -t
   nginx -s reload
   ```
5. เปิด `http://<server_name>/` จากเครื่องในวง LAN

> `luma_dev.htpasswd` เตรียมไว้สำหรับล็อกหน้าเว็บช่วง dev ด้วย basic auth — ถ้าต้องการใช้ ให้เพิ่มใน `location /`:
> `auth_basic "LUMA dev"; auth_basic_user_file /path/to/nginx/luma_dev.htpasswd;`

---

## 🔌 API Contract

Base URL: `/api/v1` · ทุก JSON response ใช้ envelope เดียวกัน · 🔒 = ต้องมี `Authorization: Bearer <JWT>`

| Method | Endpoint | Auth | คำอธิบาย |
|---|---|:--:|---|
| POST | `/register` | | สมัครสมาชิก (hash password ด้วย Werkzeug, password ≥ 8 ตัว) |
| POST | `/login` | | เข้าสู่ระบบ → คืน `access_token` อายุ 24 ชม. |
| GET | `/models` | | รายชื่อ checkpoint จาก AI Server |
| POST | `/generate` | 🔒 | สร้างรูป → คืน `image_url` (ไม่ส่ง Base64) |
| GET | `/history` | 🔒 | ประวัติของตัวเอง รองรับ `?page=1&limit=20` |
| GET | `/history/:id` | 🔒 | รายละเอียด generation หนึ่งรายการ |
| DELETE | `/history/:id` | 🔒 | ลบไฟล์ภาพบนดิสก์ แล้วลบ record |
| GET | `/profile` | 🔒 | ข้อมูลผู้ใช้ |
| GET | `/images/:id` | 🔒 | ส่งไฟล์ PNG (binary) — เช็ค ownership กัน IDOR |

```jsonc
// สำเร็จ
{ "success": true,  "data": { ... } }
// ผิดพลาด
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "..." } }
```

**ตัวอย่าง `POST /generate`**

```jsonc
// request
{ "prompt": "A girl in a cyberpunk city", "negative_prompt": "blurry, low quality",
  "checkpoint": "anypastel", "width": 512, "height": 512,
  "steps": 20, "cfg_scale": 7, "sampler": "DPM++ 2M Karras", "seed": -1 }

// response (201)
{ "success": true, "data": { "id": 123, "prompt": "...", "image_url": "/api/v1/images/123" } }
```

### Authentication (JWT)

- Login สำเร็จ → Backend ออก JWT (HS256, อายุ **24 ชั่วโมง**, payload มี `user_id`, `email`)
- Frontend เก็บใน `localStorage` (`luma_token`) และแนบทุก request ผ่าน axios interceptor
- API ตอบ `UNAUTHORIZED` → Frontend ล้าง token + redirect ไป `/login` อัตโนมัติ
- รูปภาพต้องแนบ JWT จึงโหลดผ่าน `AuthImage` / `api.getImageBlob()` แทน `<img src>` ตรง ๆ
- Secret อ่านจาก `.env` เท่านั้น — **ห้าม hardcode / commit**

---

## 🗄️ ฐานข้อมูล

`users 1 : N generations` (`ON DELETE CASCADE`) + index `idx_generations_user_id`

**`users`**

| Field | Type | Note |
|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | เก็บ hash เท่านั้น |
| `created_at` | DATETIME | default `CURRENT_TIMESTAMP` |

**`generations`**

| Field | Type | Note |
|---|---|---|
| `id` | INTEGER | PK |
| `user_id` | INTEGER | FK → `users.id` |
| `prompt` / `negative_prompt` | TEXT | prompt ≤ 2000 ตัวอักษร |
| `checkpoint` / `sampler` | VARCHAR | |
| `width` / `height` / `steps` | INTEGER | |
| `cfg_scale` | FLOAT | |
| `seed` | BIGINT | |
| `image_path` | TEXT | path ไฟล์บนดิสก์ (ไม่เก็บ Base64) |
| `created_at` | DATETIME | |

---

## ✅ กติกาที่ตกลงกันในทีม

| Field | Rule |
|---|---|
| `width` / `height` | 512, 768 หรือ 1024 |
| `steps` | 1–50 (default 20) |
| `cfg_scale` | 1–20 (default 7) |
| `seed` | -1 (สุ่ม) หรือ 0–2147483647 |
| `sampler` | `DPM++ 2M Karras` / `Euler a` / `Euler` |
| `prompt` | required, ≤ 2000 ตัวอักษร |
| `password` | ≥ 8 ตัวอักษร |

- snake_case ทุก field ทั้ง API และ DB
- Timeout: Backend → AI Server **75s** · Frontend → Backend (`/generate`) **90s** · Nginx `proxy_read_timeout` **600s**
- เจนซ้อนกัน → reject ทันทีด้วย `AI_SERVER_BUSY` (ใช้ `threading.Lock`, ไม่ทำ queue)

| HTTP | Error Code |
|---|---|
| 400 | `VALIDATION_ERROR` |
| 401 | `INVALID_CREDENTIALS` / `UNAUTHORIZED` |
| 404 | `GENERATION_NOT_FOUND` / `IMAGE_NOT_FOUND` |
| 409 | `EMAIL_EXISTS` / `AI_SERVER_BUSY` |
| 502/503 | `AI_SERVER_ERROR` / `MODEL_UNAVAILABLE` |
| 504 | `AI_SERVER_TIMEOUT` |
| 500 | `GENERATION_FAILED` / `INTERNAL_SERVER_ERROR` |

---

## 🧪 การทดสอบ

| ส่วน | คำสั่ง | ครอบคลุม |
|---|---|---|
| AI Server | `python scripts/check_server.py` / `test_txt2img.py` | API online, checkpoint, sampler, สร้างรูปจริง |
| Backend | `cd backend && pytest Testcase` | register/login, validation, generate (mock AI), AI busy, history IDOR |
| Database | `python database/Test1..3_*.py` | insert user / generation, select |
| Frontend | `cd frontend/luma-frontend && npm test` | contract ของ `api/client.js` กับ envelope |

---

## 🚧 สถานะปัจจุบัน / สิ่งที่ยังต้องเชื่อมให้ครบ

จากการอ่านโค้ด ณ ตอนนี้ ยังมีจุดที่ไม่ตรงกับ contract ข้างบน:

- **Backend** — `app/__init__.py` register แค่ `sd_bp` และ `history_bp` ยังไม่ได้ register `auth`, `profile` (และ `images.py` ซ้ำกับ route `/images/:id` ใน `sd.py`)
- **Backend** — `auth.py` / `profile.py` ยังใช้ `MOCK_USERS_DB` ในหน่วยความจำ และ `models/user.py` ยังว่าง → ต้องย้ายไปใช้ตาราง `users` จริง
- **Backend** — ยังไม่มี `GET /models` และ `GET /history/:id`; validation ใน `/generate` ยังเช็คแค่ `prompt`
- **Backend** — `services/ai_client.py` hardcode `AI_SERVER_URL` แทนที่จะอ่านจาก `.env`; `config.py` อ่าน `JWT_SECRET` แต่ middleware ใช้ `JWT_SECRET_KEY` (และยังไม่ถูกเรียกใช้)
- **Backend** — `requirements.txt` ขาด `flask-sqlalchemy`, `requests`; Testcase ยัง import `MOCK_GENERATIONS_DB` ที่ไม่มีแล้ว
- **Contract** — `/generate` ตอบ `id` แต่ Frontend คาดหวัง `generation_id`, `seed`, `created_at`
- **Nginx** — ต้องแก้ `root` ให้ชี้ `dist` จริง และเลือกว่าจะเปิด basic auth หรือไม่

---

## 🔭 Future Features (ยังไม่ทำใน V1)

Image-to-Image · Upscale · Inpainting · ControlNet · Change Password · HTTPS บน Nginx

---

_LUMA — AI Image Generation System · Image Processing Project Final_
