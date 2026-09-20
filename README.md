# LUMA — AI Image Generation System

> Project Specification **v1.4** · รายวิชา Image Processing (ปี 3 เทอม 1) · ทีม 4 คน

ระบบสร้างรูปภาพด้วย AI (Text-to-Image) แบบ **web-based** แยกเป็นชั้น ๆ ตามหน้าที่
ผู้ใช้สมัคร/เข้าสู่ระบบ → ตั้งค่า prompt แล้วสั่งสร้างรูปผ่าน **Flask backend** ซึ่งส่งต่อไปยัง
**Stable Diffusion AI server** → รูปที่ได้ถูกเซฟลงดิสก์ + บันทึกประวัติไว้ดูย้อนหลัง
ดาวน์โหลด ลบ หรือสร้างซ้ำได้ (เฉพาะของตัวเอง)

**หลักการที่ล็อกไว้ทั้งทีม:** Frontend คุยกับ Backend เท่านั้น — Backend เป็นตัวกลางเดียวที่แตะ Database และ AI Server

---

## 👥 ทีมผู้จัดทำ (Team)

| ชื่อเล่น | บทบาท | ความรับผิดชอบหลัก |
|---|---|---|
| **นาย** | Backend Developer | Flask REST API, JWT Authentication, เชื่อม Database + AI Server, Generation / History API, Error Handling |
| **ไอซ์** | AI Engineer | Stable Diffusion / AI Server, จัดการ Model / Checkpoint, `/sdapi/v1/*`, GPU Processing, ทดสอบ Model |
| **ภีม** | Database Developer | ออกแบบ Schema, ตาราง `users` / `generations`, Relationship, SQLAlchemy Models, CRUD, Data Integrity |
| **กร** | Frontend Developer | UI/UX, React + Vite, หน้า Login / Register / Home / Generate / Result / History / Profile / Setting, API Integration, Responsive Design |

> เติม ชื่อ-นามสกุล และ รหัสนักศึกษา ของแต่ละคนได้ตามสะดวก

---

## 🏗️ สถาปัตยกรรม (Architecture)

Frontend ไม่เคยคุยกับ Database หรือ AI Server ตรง ๆ — Flask Backend เป็นจุดประสานงานจุดเดียว

```
                         ┌─────────────────────────┐
   Browser ──HTTP──▶ Nginx (Reverse Proxy :80)     │
                         │   / ────────▶ Frontend (React + Vite :5173)
                         │   /api/* ───▶ Flask Backend :5000
                         └───────────┬─────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                                ▼
              SQLite Database                  AI Server (Stable Diffusion)
              users / generations              SD WebUI --api  (Forge / AUTOMATIC1111)
                                               POST /sdapi/v1/txt2img → Base64 PNG
```

**Generation flow (end-to-end):**

```
User → Frontend → POST /api/v1/generate → Flask Backend
     → POST /sdapi/v1/txt2img → AI Server (Stable Diffusion)
     → Base64 image → Backend เซฟไฟล์ + บันทึก DB
     → Frontend แสดงภาพผ่าน GET /api/v1/images/:id
```

---

## 🧰 Tech Stack

| ชั้น | เทคโนโลยี | พอร์ต | โฟลเดอร์ |
|---|---|---|---|
| **Frontend** | React 18 + Vite 5 + React Router + Axios | 5173 | `frontend/luma-frontend/` |
| **Backend** | Python + Flask 3 + Flask-SQLAlchemy + PyJWT | 5000 | `backend/` |
| **Database** | SQLite (V1 — ออกแบบให้ย้ายไป PostgreSQL ได้) | — | `database/` |
| **AI Server** | Stable Diffusion WebUI (AUTOMATIC1111 / Forge) `--api` | 8088 | `Ai Server/` |
| **Infra** | Nginx (Reverse Proxy, LAN) | 80 | `nginx/` |

---

## 📁 โครงสร้างโปรเจกต์

```
Image_Project/
├── backend/                    # Flask REST API (นาย)
│   ├── run.py                  # entry point: create_app() → app.run(:5000)
│   ├── requirements.txt
│   ├── .env                    # JWT_SECRET_KEY, AI_SERVER_URL (ห้าม commit)
│   └── app/
│       ├── __init__.py         # app factory + register blueprints + db.create_all()
│       ├── extensions.py       # db = SQLAlchemy()
│       ├── models/             # user.py, generation.py  (ภีม)
│       ├── routes/             # auth, sd, history, profile, images
│       ├── services/           # ai_client.py (คุยกับ SD WebUI + lock กันยิงซ้อน)
│       ├── middleware/         # jwt_auth.py — @token_required
│       └── utils/              # error_codes.py — success/error envelope
├── frontend/luma-frontend/     # React + Vite (กร)
│   └── src/
│       ├── api/client.js       # axios กลาง: แกะ envelope + แนบ JWT + timeout 90s
│       ├── context/            # AuthContext, ThemeContext
│       ├── pages/              # Login, Register, Home, Generate, Result, History, Profile, Setting
│       └── components/         # Layout, ProtectedRoute, AuthImage
├── database/                   # SQLite (ภีม)
│   ├── schema.sql              # DDL: users + generations
│   └── init_db.py
├── Ai Server/                  # Stable Diffusion config + สคริปต์ทดสอบ (ไอซ์)
└── nginx/nginx.conf            # reverse proxy config
```

---

## 🚀 เริ่มใช้งาน (Quick Start)

รันได้ทั้งแบบ **เครื่องเดียว** (dev) และ **แยกเครื่องในวง LAN** (integrate) — ต่างกันแค่ค่า IP ใน `.env`

### สิ่งที่ต้องมีก่อน
- Python 3.10+ , Node.js 18+
- เครื่องที่มี GPU สำหรับรัน Stable Diffusion (AI Server)

### 1) AI Server (ไอซ์)
เปิด Stable Diffusion WebUI (Forge / AUTOMATIC1111) ด้วย flag ที่ห้ามขาด:

```
--api      # เปิด REST API /sdapi/v1/*  (ไม่มี = ได้ 404)
--listen   # ให้เครื่องอื่นในวง LAN เรียกถึง
--port 8088
```

ตรวจว่าพร้อม:
```bash
curl http://127.0.0.1:8088/sdapi/v1/sd-models
```

### 2) Backend (นาย)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

สร้าง `backend/.env`:
```env
PORT=5000
JWT_SECRET_KEY=<สุ่มค่าลับของตัวเอง>      # python -c "import secrets; print(secrets.token_urlsafe(48))"
AI_SERVER_URL=http://127.0.0.1:8088       # เครื่องเดียว; แยกเครื่องใส่ IP ของ AI Server
```

รัน:
```bash
python run.py     # ฟังที่ http://localhost:5000
```

> SQLite จะถูกสร้างให้อัตโนมัติตอนสตาร์ท (`db.create_all()`)

### 3) Frontend (กร)
```bash
cd frontend/luma-frontend
npm install
copy .env.example .env
npm run dev       # เปิด http://localhost:5173
```

ค่าใน `frontend/.env`:

| ตัวแปร | ความหมาย |
|---|---|
| `VITE_API_BASE_URL` | ที่อยู่ Backend เช่น `http://localhost:5000/api/v1` |
| `VITE_MOCK_MODE` | `true` = เดินดูทุกหน้าด้วยข้อมูลปลอมโดยไม่ต้องมี Backend / `false` = ต่อ Backend จริง |

---

## 🔌 API Contract

Base URL: `/api/v1/` · ทุก response ห่อด้วย envelope เดียวกันทั้งระบบ · 🔒 = ต้องมี `Authorization: Bearer <JWT>`

| Method | Endpoint | Auth | คำอธิบาย |
|---|---|:--:|---|
| POST | `/register` | | สมัครสมาชิก (hash password ด้วย Werkzeug) |
| POST | `/login` | | เข้าสู่ระบบ → คืน JWT อายุ 24 ชม. |
| GET | `/models` | | รายชื่อ checkpoint จาก AI Server |
| POST | `/generate` | 🔒 | สร้างรูป → คืน `image_url` (ไม่ใช่ Base64) |
| GET | `/history` | 🔒 | ประวัติของตัวเอง รองรับ `?page=1&limit=20` |
| GET | `/history/:id` | 🔒 | รายละเอียด generation หนึ่งรายการ |
| DELETE | `/history/:id` | 🔒 | ลบไฟล์ภาพก่อน แล้วค่อยลบ record (rollback ถ้าลบไฟล์ไม่สำเร็จ) |
| GET | `/profile` | 🔒 | ข้อมูลผู้ใช้ + จำนวนรูปที่สร้าง |
| GET | `/images/:generation_id` | 🔒 | ส่งไฟล์ PNG (binary) — เช็ค ownership กัน IDOR |

### รูปแบบ Response

```jsonc
// สำเร็จ
{ "success": true,  "data": { "...": "..." } }

// ผิดพลาด
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "..." } }
```

**ตัวอย่าง `POST /generate`:**
```jsonc
// request
{ "prompt": "A girl in a cyberpunk city", "negative_prompt": "blurry, low quality",
  "checkpoint": "anypastel", "width": 512, "height": 512,
  "steps": 20, "cfg_scale": 7, "sampler": "DPM++ 2M Karras", "seed": -1 }

// response
{ "success": true, "data": {
    "generation_id": 123, "image_url": "/api/v1/images/123",
    "seed": 123456789, "created_at": "2026-08-24T16:30:00" } }
```

---

## 🔐 Authentication (JWT)

- Login สำเร็จ → Backend ออก JWT (อายุ **24 ชั่วโมง**) → Frontend เก็บใน `localStorage`
- แนบทุก request ที่ต้อง auth ด้วย header `Authorization: Bearer <JWT_TOKEN>`
- ถ้า API ตอบ `UNAUTHORIZED` → Frontend logout + redirect ไปหน้า login
- Secret อ่านจาก `.env` เท่านั้น **ห้าม hardcode / commit ขึ้น Git**
- ทุก endpoint ที่มี `:id` ต้องเช็ค `resource.user_id == token.user_id` ก่อนเสมอ (กัน IDOR)

---

## 🗄️ ฐานข้อมูล (Database)

สองตาราง หนึ่งความสัมพันธ์ — `users 1 : N generations` (ON DELETE CASCADE)

**`users`**

| Field | Type | Note |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `email` | VARCHAR | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR | เก็บ hash เท่านั้น (ห้าม plain text) |
| `created_at` | DATETIME | |

**`generations`**

| Field | Type | Note |
|---|---|---|
| `id` | INTEGER | Primary Key |
| `user_id` | INTEGER | Foreign Key → `users.id` |
| `prompt` / `negative_prompt` | TEXT | |
| `checkpoint` / `sampler` | VARCHAR | |
| `width` / `height` / `steps` / `seed` | INTEGER | `seed` เป็น BIGINT |
| `cfg_scale` | FLOAT | |
| `image_path` | TEXT | path ไฟล์บนดิสก์ (ไม่เก็บ Base64) |
| `created_at` | DATETIME | |

---

## ✅ กติกาที่ล็อกไว้ (Team Standards)

**Validation (ต้องตรงกันทั้ง Frontend + Backend):**

| Field | Rule |
|---|---|
| `width` / `height` | 512, 768 หรือ 1024 เท่านั้น |
| `steps` | 1–50 (default 20) |
| `cfg_scale` | 1–20 (default 7) |
| `seed` | -1 หรือ 0–2147483647 |
| `sampler` | `"DPM++ 2M Karras"` / `"Euler a"` / `"Euler"` เท่านั้น |
| `prompt` | required, ≤ 2000 ตัวอักษร |
| `password` | ≥ 8 ตัวอักษร |

**อื่น ๆ:** snake_case ทุก field ทั้ง API/DB · timeout Backend→AI = 75s, Frontend→Backend = 90s ·
เจนซ้อนกัน → reject ทันทีด้วย `AI_SERVER_BUSY` (ไม่ทำ queue)

### Error Codes

| HTTP | Code |
|---|---|
| 400 | `VALIDATION_ERROR` |
| 401 | `INVALID_CREDENTIALS` / `UNAUTHORIZED` |
| 409 | `EMAIL_EXISTS` / `AI_SERVER_BUSY` |
| 404 | `GENERATION_NOT_FOUND` / `IMAGE_NOT_FOUND` |
| 503 | `MODEL_UNAVAILABLE` |
| 502/503 | `AI_SERVER_ERROR` |
| 504 | `AI_SERVER_TIMEOUT` |
| 500 | `GENERATION_FAILED` / `INTERNAL_SERVER_ERROR` |

---

## 🌿 Git Workflow

Feature-branch workflow — **ห้าม push ตรงเข้า `main`**

```
main                    stable / พร้อมใช้งาน
 └─ Front_end           ฐานงานทีม Frontend
     └─ feature/<area>-<short-name>   แตกจาก Issue เสมอ
```

- 1 Issue → 1 Feature Branch → เปิด PR กลับเข้า `Front_end` (Backend/AI/Database มี branch ฐานของตัวเอง)
- Commit แบบ Conventional Commits: `type(scope): description`
  เช่น `feat(frontend): add theme swatch picker` · scope = `frontend` / `backend` / `database` / `ai-server` / `docs`

---

## 🔭 Future Features (ยังไม่ทำใน V1)

Image-to-Image · Image Upscale · Inpainting · ControlNet · Change Password

> ฟีเจอร์เหล่านี้ **ไม่อยู่ใน 9 endpoints ที่ล็อกไว้** — จะทำจริงต้องเพิ่ม endpoint ใหม่ (ห้าม Frontend fake API เอง)

---

_LUMA — AI Image Generation System · Project Specification v1.4_
