# LUMA — AI Image Generation & Processing System

> Project Final · รายวิชา Image Processing (ปี 3 เทอม 1) · ทีม 4 คน

LUMA คือเว็บแอปสำหรับ **สร้างรูปด้วย AI (Text-to-Image)** และ **แต่งรูปด้วย Computer Vision** ในที่เดียว

- **Generate** — พิมพ์ prompt เลือก checkpoint / sampler / ขนาด / steps / CFG / seed แล้วให้ Stable Diffusion สร้างรูป
- **Image Tools** — อัปโหลดรูปแล้วใช้เครื่องมือ OpenCV + MediaPipe: Spot Blur, Cartoonize, Tilt-Shift, HDR Enhancer, Hand Gesture, Remove Background
- **History** — รูปทุกใบถูกเก็บพร้อมพารามิเตอร์ ดูย้อนหลัง ดาวน์โหลด ลบ หรือกด "Again" เพื่อสร้างซ้ำได้ (เห็นเฉพาะของตัวเอง)
- **Admin** — ผู้ดูแลระบบดูรายชื่อผู้ใช้ + จำนวนรูปที่สร้าง และลบบัญชีได้

**หลักการที่ทั้งทีมยึด:** ผู้ใช้เข้าผ่าน **Nginx** ประตูเดียว → Frontend คุยกับ Backend เท่านั้น →
Backend เป็นตัวกลางเดียวที่แตะ Database และ AI Server

---

## 👥 ทีมผู้จัดทำ

| ชื่อเล่น | บทบาท | ความรับผิดชอบหลัก | โฟลเดอร์ |
|---|---|---|---|
| **นาย** | Backend Developer | Flask REST API, JWT + Role (admin), เชื่อม Database + AI Server, GPU queue, Image Processing API (`/process/*`), Error Handling, Test suite | `backend/`, `docs/` |
| **ไอซ์** | AI Engineer + Infra (Nginx) | Stable Diffusion WebUI (`--api`), จัดการ Checkpoint, สคริปต์ health-check / ทดสอบ txt2img, **Nginx Reverse Proxy Gateway** (rate limit, security headers, DEV gateway `:8089`, firewall scripts, Cloudflare demo tunnel) | `Ai Server/`, `nginx/` |
| **ภีม** | Database Developer | ออกแบบ Schema `users` / `generations`, Relationship + Index, สคริปต์สร้าง / ทดสอบ / ล้างฐานข้อมูล | `database/` |
| **กร** | Frontend Developer | UI/UX, React + Vite, ทุกหน้า (Login → Admin), Feature Registry ของเครื่องมือแต่งรูป, Theme + Layout Template, Mock Mode, Vitest | `frontend/luma-frontend/` |

> เติม ชื่อ-นามสกุล และ รหัสนักศึกษา ของแต่ละคนได้ตามสะดวก

---

## 🏗️ สถาปัตยกรรม (แยก 3 เครื่องในวง LAN)

```
                 ผู้ใช้ในวง LAN  ──  http://172.20.57.12/
                                     │
          ┌──────────────────────────▼───────────────────────────┐
          │  Nginx  :80   — เครื่อง 172.20.57.12   (ไอซ์)          │
          │   /            → ไฟล์ static จาก frontend/.../dist      │
          │   /api/v1/*    → proxy → Backend  (rate limit)         │
          │   /api/*  อื่น → 404                                    │
          │  Nginx  :8089  — DEV เท่านั้น (allowlist + basic auth)    │
          │                → SD WebUI ของ AI Server                │
          └──────────────────────────┬───────────────────────────┘
                                     ▼
          ┌──────────────────────────────────────────────────────┐
          │  Flask Backend :5000 — เครื่อง 172.20.57.16   (นาย)     │
          │  JWT · Validation · GPU Lock/Queue · OpenCV/MediaPipe │
          └───────────────┬──────────────────────────┬───────────┘
                          ▼                          ▼
             SQLite  database/database.db     AI Server :8088 — 172.20.57.10 (ไอซ์)
             users / generations  (ภีม)        SD WebUI --api (A1111 / Forge)
             + ไฟล์ภาพ backend/uploads/         POST /sdapi/v1/txt2img → Base64 PNG
```

**Firewall:** Flask `:5000` รับจากเครื่อง Nginx เท่านั้น · SD `:8088` รับจากเครื่อง Backend เท่านั้น ·
ผู้ใช้ทั่วไปเข้าได้แค่พอร์ต `80` (สคริปต์อยู่ใน `nginx/firewall/`)

**Generation flow**

```
User → Frontend → POST /api/v1/generate (Bearer JWT) → Nginx → Flask
     → เข้าคิว GPU Lock (รอได้สูงสุด 40s ไม่งั้น AI_SERVER_BUSY)
     → POST /sdapi/v1/txt2img → AI Server (timeout 75s)
     → Base64 PNG → Flask บันทึก generations (image_data + ไฟล์บนดิสก์)
     → ตอบ generation_id + image_url → Frontend โหลดรูปผ่าน GET /api/v1/images/:id (แนบ JWT)
```

**Image Tool flow:** Frontend อัปโหลดรูป (multipart) → `POST /api/v1/process/<tool>` → Flask ประมวลผลด้วย
OpenCV / MediaPipe บนเครื่อง Backend เอง (ไม่ใช้ GPU Server) → ส่ง PNG กลับ

---

## 🧰 Tech Stack

| ชั้น | เทคโนโลยี | พอร์ต | โฟลเดอร์ |
|---|---|---|---|
| **Gateway** | Nginx for Windows (มีเวอร์ชัน Linux), Cloudflare quick tunnel สำหรับเดโม | 80, 8089 | `nginx/` |
| **Frontend** | React 18, Vite 5, React Router 6, Axios, lucide-react, motion, Vitest | 5173 (dev) | `frontend/luma-frontend/` |
| **Backend** | Flask 3, Flask-SQLAlchemy, Flask-CORS, PyJWT, Werkzeug, Requests, OpenCV, NumPy, MediaPipe, Gunicorn (Linux) | 5000 | `backend/` |
| **Database** | SQLite | — | `database/` |
| **AI Server** | Stable Diffusion WebUI (AUTOMATIC1111 / Forge) `--api --listen` | 8088 | `Ai Server/` |

---

## 📁 โครงสร้างโปรเจกต์

```
Image_Project/
├── nginx/                          # (ไอซ์) — คู่มือเต็ม: nginx/README.md
│   ├── START.bat / STOP.bat        # เปิด-รีโหลด / ปิด nginx
│   ├── LOGS.bat                    # ดู access log สด ๆ
│   ├── BUILD-WEB.bat               # npm run build หน้าเว็บใหม่หลัง git pull
│   ├── conf/
│   │   ├── nginx.conf              # upstream IP, root dist, rate limit, headers, :80 และ :8089
│   │   ├── luma_proxy_backend.conf # ชุด proxy_* ไป Flask (timeout 120s)
│   │   └── dev_allowlist.conf      # IP ทีม DEV ที่เข้าหลังบ้านได้
│   ├── firewall/                   # for-nginx / for-backend / for-ai .ps1 + linux.sh
│   └── extras/                     # Cloudflare demo tunnel, make_htpasswd.sh, คู่มือเดิม
├── Ai Server/                      # (ไอซ์) — ไม่ได้เก็บตัว webui เก็บแค่ config + สคริปต์ + เอกสาร
│   ├── config/webui-user.bat|.sh   # COMMANDLINE_ARGS: --api --listen --port 8088 ...
│   ├── scripts/check_server.py     # health check: options / sd-models / samplers
│   ├── scripts/test_txt2img.py     # ยิง txt2img ตรง ไม่ผ่าน Backend
│   └── models/                     # วาง checkpoint (ไฟล์จริงไม่ commit)
├── backend/                        # (นาย)
│   ├── run.py                      # entry point (dev) — อ่าน HOST / PORT / FLASK_DEBUG จาก .env
│   ├── gunicorn_conf.py            # production บน Linux (workers=1, threads=8 เพื่อให้ GPU lock ใช้ได้)
│   ├── config.py                   # ค่ากลาง: JWT, CORS, AI_SERVER_URL, upload 16 MB, log
│   ├── .env.example
│   ├── models/                     # โมเดล MediaPipe (.tflite / .task)
│   ├── scripts/
│   │   ├── download_models.py      # โหลดโมเดล MediaPipe ล่วงหน้า
│   │   └── set_admin.py            # ตั้ง / ถอดสิทธิ์ admin, ดูรายชื่อผู้ใช้
│   ├── app/
│   │   ├── __init__.py             # app factory, CORS, ProxyFix, blueprints, /health, auto-migration
│   │   ├── models/                 # user.py (role), generation.py (category, params, image_data)
│   │   ├── routes/                 # auth, profile, sd, history, admin
│   │   ├── services/ai_client.py   # เรียก SD WebUI + GPU lock/queue + ประเมินเวลา
│   │   ├── services/image_filters/ # spot_blur, cartoonize, tilt_shift, hdr_enhancer, gesture, remove_bg + routes
│   │   ├── middleware/jwt_auth.py  # @token_required, @admin_required
│   │   └── utils/error_codes.py    # success / error envelope + error codes
│   └── tests/                      # test_backend_full.py, test_image_filters_suite.py
├── database/                       # (ภีม)
│   ├── init_db.py                  # สร้างตารางจากโมเดลใน backend/app/models (สำรอง .bak ก่อน ข้อมูลเดิมไม่หาย)
│   ├── clear.py                    # ล้างข้อมูล (เลือกเก็บบาง user_id ได้)
│   └── Test1..3_*.py               # สคริปต์ทดสอบ insert / select
├── frontend/
│   ├── index.html                  # prototype หน้าเดียว (เวอร์ชันแรก)
│   └── luma-frontend/              # (กร) React + Vite — ตัวจริง
│       └── src/
│           ├── api/                # client.js (axios กลาง), errorMessages.js, mockData.js
│           ├── pages/              # Login, Register, Home, Generate, Features, Result, History, Profile, Setting, Admin
│           ├── components/         # Layout, ProtectedRoute, AuthImage, Toast, SkeletonCard, ErrorBoundary
│           ├── components/features/# หน้าเครื่องมือแต่งรูปแต่ละตัว + ImageUploader
│           ├── components/templates/ # ClassicLayout, SoftLayout
│           ├── features/           # registry.js + active.js — เปิด/ปิดเครื่องมือจากที่เดียว
│           ├── context/            # Auth, Theme, Layout, Toast
│           ├── themes/ templates/  # สีธีม และ layout template (Classic / Soft)
│           └── test/               # Vitest
└── docs/                           # รายงาน Backend + Image Processing (.md / .docx)
```

---

## 🚀 วิธีรัน

**ลำดับเปิดระบบ:** AI Server → Backend → Nginx

**สิ่งที่ต้องมี:** Python 3.10+, Node.js 18+, Nginx for Windows (zip), NVIDIA GPU ≥ 6 GB VRAM บนเครื่อง AI

> รันทุกอย่างในเครื่องเดียวก็ได้ — แค่เปลี่ยน IP ใน `backend/.env` และ `nginx/conf/nginx.conf` เป็น `127.0.0.1`

### 1) AI Server — ไอซ์ (เครื่อง 172.20.57.10)

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
copy "..\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat
# วาง checkpoint .safetensors ลง models/Stable-diffusion/
webui-user.bat
```

Flag ที่ **ห้ามลบ**: `--api` · `--listen` · `--port 8088`

```bash
cd "Ai Server"
pip install -r scripts/requirements.txt
python scripts/check_server.py --url http://127.0.0.1:8088
python scripts/test_txt2img.py -p "a cat astronaut" --steps 20
```

> ถ้า 2 สคริปต์นี้ผ่าน แต่หน้าเว็บสร้างรูปไม่ได้ → ปัญหาอยู่ฝั่ง Backend / Nginx / Frontend
> รายละเอียด + ตารางแก้ปัญหา: [`Ai Server/README.md`](Ai%20Server/README.md)

### 2) Backend — นาย (เครื่อง 172.20.57.16)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py   # โหลดโมเดล MediaPipe (ถ้ายังไม่มีใน backend/models/)
copy .env.example .env              # แล้วแก้ค่าในไฟล์
python run.py                       # http://0.0.0.0:5000
```

| ตัวแปร `backend/.env` | ความหมาย |
|---|---|
| `PORT` | พอร์ต Flask (default `5000`) |
| `HOST` | `0.0.0.0` เมื่อ Nginx อยู่คนละเครื่อง · `127.0.0.1` เมื่ออยู่เครื่องเดียวกัน |
| `JWT_SECRET_KEY` | ค่าลับเซ็น JWT — `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `AI_SERVER_URL` | เช่น `http://172.20.57.10:8088` |
| `FLASK_DEBUG` | `0` เสมอเมื่อเปิดรับจาก LAN |
| `CORS_ORIGINS` | เช่น `http://172.20.57.12,http://localhost:5173` |

ตรวจ: `http://127.0.0.1:5000/api/v1/health` ต้องได้ `"status": "healthy"`

ตั้งผู้ใช้เป็น admin (ต้องสมัครผ่านหน้าเว็บก่อน):

```bash
python scripts/set_admin.py --list
python scripts/set_admin.py user@example.com
python scripts/set_admin.py --revoke user@example.com
```

> ตารางในฐานข้อมูลถูกสร้าง/เพิ่มคอลัมน์ให้อัตโนมัติตอนสตาร์ท (`database/database.db`)
> Production บน Linux: `gunicorn -c gunicorn_conf.py run:app`

### 3) Frontend — กร

```bash
cd frontend/luma-frontend
npm install
copy .env.example .env      # Linux/macOS: cp .env.example .env
npm run dev                 # dev: http://localhost:5173
npm run build               # build ไป dist/ (ใช้ .env.production → VITE_API_BASE_URL=/api/v1)
npm test                    # Vitest
```

| ตัวแปร | ความหมาย |
|---|---|
| `VITE_API_BASE_URL` | `/api/v1` เมื่อผ่าน Nginx · `http://localhost:5000/api/v1` เมื่อ dev ต่อ Backend ตรง |
| `VITE_MOCK_MODE` | `true` = เดินดูทุกหน้าด้วยข้อมูลปลอม ไม่ต้องมี Backend · `false` = ต่อ Backend จริง |

### 4) Nginx — ไอซ์ (เครื่อง 172.20.57.12)

ตั้งค่าครั้งแรก:

1. โหลด Nginx for Windows (zip) จาก nginx.org แตกไว้ที่ `nginx\win\` ให้ได้ `nginx\win\nginx-x.y.z\nginx.exe`
2. แก้ `nginx\conf\nginx.conf`
   - `upstream luma_backend` → IP:พอร์ต ของ Backend
   - `upstream luma_ai_server` → IP:พอร์ต ของ AI Server
   - `root` → path ของ `frontend/luma-frontend/dist` ในเครื่องตัวเอง (ใช้ `/` ไม่ใช่ `\`)
3. ใส่ IP ทีม DEV ใน `conf\dev_allowlist.conf` และสร้างรหัสหลังบ้านด้วย `extras/make_htpasswd.sh` (ถ้าจะใช้ `:8089`)
4. รัน firewall ครั้งเดียวต่อเครื่อง (PowerShell แบบ Run as Administrator)
   ```powershell
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-nginx.ps1     # เครื่อง nginx
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-backend.ps1   # เครื่อง Backend
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-ai.ps1        # เครื่อง AI
   ```
5. ดับเบิลคลิก `BUILD-WEB.bat` → `START.bat`

ใช้งานประจำวัน:

| ไฟล์ | ใช้ตอนไหน |
|---|---|
| `START.bat` | เปิด nginx หรือกดซ้ำหลังแก้ `conf\` (คัดลอก config → `nginx -t` → start/reload) |
| `STOP.bat` | ปิด nginx |
| `LOGS.bat` | ดูว่าใครเข้าเว็บ ขออะไร |
| `BUILD-WEB.bat` | หลัง `git pull` ที่มีการแก้หน้าเว็บ |

สิ่งที่ Gateway ทำ:

| เรื่อง | รายละเอียด |
|---|---|
| ประตูเดียว | ผู้ใช้เข้าได้แค่ `:80` — Flask, Vite, SD WebUI ห้ามเข้าตรง |
| จำกัด API | ผ่านเฉพาะ `/api/v1/*` · path อื่นใต้ `/api/` ตอบ 404 |
| Rate limit | login / register 10 ครั้ง/นาที · รูปภาพ 600 ครั้ง/นาที · API อื่น 120 ครั้ง/นาที ต่อ IP → `429` |
| Upload | `client_max_body_size 16m` ให้ตรงกับ Backend |
| Security | ซ่อนเวอร์ชัน nginx, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, กันเข้าไฟล์ `.env/.db/.py/...` |
| Performance | gzip, cache `/assets/` 1 ปี (ไฟล์ Vite มี hash) |
| Backend ล่ม | ตอบ JSON `{"success":false,"error":{"code":"INTERNAL_SERVER_ERROR",...}}` แทนหน้า 502 |
| DEV gateway | `:8089` → SD WebUI (allowlist IP + basic auth) และ `/_dev/backend/` |
| เดโมนอก LAN | Cloudflare quick tunnel → `:80` อย่างเดียว ได้ HTTPS (ดู `nginx/extras/DEMO-cloudflared.md`) |

ตรวจ: `http://localhost/healthz` → `ok` · `http://localhost/api/v1/health` → `healthy`

> คู่มือเต็ม + ตาราง "IP เปลี่ยนต้องแก้ที่ไหน" + แก้ปัญหา: [`nginx/README.md`](nginx/README.md)

---

## 🔌 API

Base URL: `/api/v1` · 🔒 = ต้องมี `Authorization: Bearer <JWT>` · 👑 = admin เท่านั้น

| Method | Endpoint | Auth | คำอธิบาย |
|---|---|:--:|---|
| GET | `/health` | | สถานะ Backend |
| POST | `/register` | | สมัครสมาชิก (password ≥ 8 ตัว, hash ด้วย Werkzeug) |
| POST | `/login` | | เข้าสู่ระบบ → `access_token` อายุ 24 ชม. + `user` (มี `role`) |
| GET | `/models` | | รายชื่อ checkpoint จาก AI Server |
| POST | `/generate` | 🔒 | สร้างรูป → `generation_id`, `image_url`, `seed` |
| GET | `/images/:id` | 🔒 | ไฟล์ PNG (binary) — เช็คเจ้าของกัน IDOR |
| GET | `/history` | 🔒 | ประวัติของตัวเอง `?page=1&limit=20` |
| GET | `/history/:id` | 🔒 | รายละเอียด 1 รายการ |
| DELETE | `/history/:id` | 🔒 | ลบรายการ + ไฟล์ภาพ |
| GET | `/profile` | 🔒 | ข้อมูลผู้ใช้ + `generation_count` |
| POST | `/process/spot-blur` | 🔒 | เบลอเฉพาะจุด (`circles`, `strength`, `soft`) |
| POST | `/process/cartoonize` | 🔒 | ภาพสไตล์การ์ตูน (`num_colors`, `line_thickness`, `smoothness`) |
| POST | `/process/tilt-shift` | 🔒 | จำลองโมเดลจิ๋ว |
| POST | `/process/hdr-enhancer` | 🔒 | เพิ่มรายละเอียด / คอนทราสต์สไตล์ HDR |
| POST | `/process/gesture` | 🔒 | จดจำท่ามือ 7 แบบ (MediaPipe) |
| POST | `/process/remove-bg` | 🔒 | ลบพื้นหลัง (MediaPipe + GrabCut) |
| GET | `/admin/users` | 👑 | รายชื่อผู้ใช้ทั้งหมด + จำนวนรูป |
| DELETE | `/admin/users/:id` | 👑 | ลบผู้ใช้ (ลบตัวเองไม่ได้) |

`/process/*` รับ `multipart/form-data` (field `image`: .jpg .jpeg .png .webp ≤ 16 MB)

```jsonc
// JSON response ทุกตัวใช้ envelope เดียวกัน
{ "success": true,  "data": { ... } }
{ "success": false, "error": { "code": "VALIDATION_ERROR", "message": "..." } }
```

**ตัวอย่าง `POST /generate`**

```jsonc
// request
{ "prompt": "A girl in a cyberpunk city", "negative_prompt": "blurry, low quality",
  "checkpoint": "anypastel", "width": 512, "height": 512,
  "steps": 20, "cfg_scale": 7, "sampler": "DPM++ 2M Karras", "seed": -1 }

// response 201
{ "success": true, "data": { "generation_id": 123, "image_url": "/api/v1/images/123", "seed": 123456789, ... } }
```

### Authentication

- JWT แบบ HS256 อายุ **24 ชั่วโมง** payload มี `user_id`, `email`
- Frontend เก็บใน `localStorage` และแนบผ่าน axios interceptor · ถ้าได้ `UNAUTHORIZED` จะ logout + กลับไป `/login`
- รูปภาพต้องแนบ JWT จึงโหลดผ่าน `AuthImage` (Blob) แทน `<img src>`
- `@admin_required` เช็ค `role` จากฐานข้อมูลทุกครั้ง — เมนู Admin ในหน้าเว็บซ่อนไว้แค่เพื่อ UX

---

## 🗄️ ฐานข้อมูล

`users 1 : N generations` (`ON DELETE CASCADE`) · index ที่ `user_id`, `category`, `created_at`

**`users`** — `id`, `email` (UNIQUE), `password_hash`, `role` (`user` / `admin`), `created_at`

**`generations`**

| Field | Note |
|---|---|
| `id`, `user_id` | PK / FK → `users.id` |
| `category`, `action_type` | แยกประเภท เช่น `sd_generate` / `txt2img` หรือรายการจากเครื่องมือแต่งรูป |
| `prompt`, `negative_prompt`, `checkpoint`, `sampler` | พารามิเตอร์ SD |
| `width`, `height`, `steps`, `cfg_scale`, `seed` | พารามิเตอร์ SD |
| `params` | JSON พารามิเตอร์ของเครื่องมืออื่น ๆ |
| `source_image_id` | อ้างถึงรูปต้นทาง (ถ้ามี) |
| `image_data` / `image_path` | ไบต์ PNG ในฐานข้อมูล + ไฟล์สำเนาบนดิสก์ (`backend/uploads/generations/`) |
| `created_at` | |

> โครงตารางกำหนดไว้ที่เดียวคือ `backend/app/models/` (`user.py`, `generation.py`) Backend สร้างตาราง + เพิ่มคอลัมน์ที่ขาดให้อัตโนมัติตอนสตาร์ท จึงใช้กับฐานข้อมูลเก่าได้โดยข้อมูลไม่หาย
> อยากสร้างตารางล่วงหน้าโดยไม่เปิด backend: `python database/init_db.py` (ใช้ Python ตัวเดียวกับ backend)

---

## ✅ กติกาที่ตกลงกัน

| Field | Rule |
|---|---|
| `width` / `height` | 512, 768 หรือ 1024 |
| `steps` | 1–50 (default 20) |
| `cfg_scale` | 1–20 (default 7) |
| `seed` | -1 (สุ่ม) หรือ 0–2147483647 |
| `sampler` | `Euler a` (default) / `Euler` / `DPM++ 2M Karras` |
| `prompt` | required, ≤ 2000 ตัวอักษร |
| `password` | ≥ 8 ตัวอักษร |
| upload | .jpg .jpeg .png .webp, ≤ 16 MB |

**Timeout:** Backend → AI Server 75s · รอคิว GPU สูงสุด 40s · Nginx → Backend 120s · Frontend → `/generate` 125s, `/process/*` 120s

| HTTP | Error Code |
|---|---|
| 400 | `VALIDATION_ERROR` · `INVALID_IMAGE` · `CANNOT_DELETE_SELF` |
| 401 | `INVALID_CREDENTIALS` · `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `GENERATION_NOT_FOUND` · `IMAGE_NOT_FOUND` · `USER_NOT_FOUND` |
| 409 | `EMAIL_EXISTS` · `AI_SERVER_BUSY` |
| 413 | `FILE_TOO_LARGE` |
| 415 | `UNSUPPORTED_FILE_TYPE` |
| 429 | (จาก Nginx) ส่งคำขอถี่เกิน |
| 500 | `GENERATION_FAILED` · `INTERNAL_SERVER_ERROR` |
| 502/503 | `AI_SERVER_ERROR` · `MODEL_UNAVAILABLE` |
| 504 | `AI_SERVER_TIMEOUT` |

---

## 🧪 การทดสอบ

| ส่วน | คำสั่ง | ครอบคลุม |
|---|---|---|
| AI Server | `python "Ai Server/scripts/check_server.py"` / `test_txt2img.py` | API online, checkpoint, sampler, สร้างรูปจริง |
| Backend | `cd backend && pytest tests` | สมัคร / login / JWT, IDOR, pagination, คิว GPU, profile, health, การเก็บไฟล์, admin, image filters ทุกตัว |
| Database | `python database/Test1_create_user.py` ฯลฯ | insert / select |
| Frontend | `cd frontend/luma-frontend && npm test` | API contract, admin, ขนาดรูปตามโมเดล, settings, ErrorBoundary |
| ทั้งระบบ | `http://<nginx>/healthz` และ `/api/v1/health` | Nginx → Backend ต่อกันได้ |

---

## 🛠️ แก้ปัญหาที่เจอบ่อย

| อาการ | ดูที่ |
|---|---|
| หน้าเว็บขึ้น แต่ login ไม่ได้ / "Backend is unavailable" | Backend ไม่ได้รัน, `HOST` ไม่ใช่ `0.0.0.0`, หรือ firewall เครื่อง Backend ยังไม่อนุญาตเครื่อง Nginx |
| ไม่มีรายชื่อโมเดล / สร้างรูปไม่ได้ | AI Server ไม่ได้รัน หรือ firewall เครื่อง AI → `check_server.py` |
| `AI_SERVER_BUSY` | มีคนสร้างรูปอยู่และรอคิวเกิน 40s — ลองใหม่ |
| Remove BG / Gesture ได้ `MODEL_UNAVAILABLE` | ยังไม่มีโมเดลใน `backend/models/` → `python scripts/download_models.py` |
| เครื่องอื่นเปิดเว็บไม่ได้ | `nginx/firewall/for-nginx.ps1` และตั้ง Wi-Fi เป็น Private |
| แก้หน้าเว็บแล้วไม่เปลี่ยน | ลืม `BUILD-WEB.bat` |
| `413` / `429` | ไฟล์เกิน 16 MB / กดถี่เกิน rate limit |

---

## 📚 เอกสารเพิ่มเติม

| ไฟล์ | เนื้อหา |
|---|---|
| [`nginx/README.md`](nginx/README.md) | คู่มือ Nginx Gateway ฉบับเต็ม |
| [`nginx/extras/DEMO-cloudflared.md`](nginx/extras/DEMO-cloudflared.md) | เปิดเดโมให้คนนอกวง LAN |
| [`Ai Server/README.md`](Ai%20Server/README.md) | ติดตั้ง / ทดสอบ / แก้ปัญหา AI Server |
| [`frontend/luma-frontend/README.md`](frontend/luma-frontend/README.md) | โครงสร้าง Frontend และ Mock Mode |
| [`docs/BACKEND_CAPABILITIES.md`](docs/BACKEND_CAPABILITIES.md) | ความสามารถทั้งหมดของ Backend |
| [`docs/BACKEND_USER_GUIDE.md`](docs/BACKEND_USER_GUIDE.md) | คู่มือใช้งาน Backend |
| [`docs/IMAGE_PROCESSING_REPORT.md`](docs/IMAGE_PROCESSING_REPORT.md) | อัลกอริทึมของเครื่องมือแต่งรูป |
| [`docs/FRONTEND_REQUIREMENTS.md`](docs/FRONTEND_REQUIREMENTS.md) | Requirement ฝั่ง Frontend |

---

## 🌿 Git Workflow

- ห้าม push ตรงเข้า `main` — 1 Issue → 1 branch (`<issue>-<type>/<area>-<name>`) → เปิด PR
- Commit แบบ Conventional Commits: `type(scope): description` เช่น `feat(nginx): ...`, `fix(frontend): ...`
- ห้าม commit: `.env`, `*.htpasswd`, `nginx/win/`, checkpoint `.safetensors` / `.ckpt`, `node_modules/`, `dist/`

---

## 🔭 Future Features

Image-to-Image · Upscale · Inpainting · ControlNet · Change Password · HTTPS ถาวรบน Nginx

---

_LUMA — AI Image Generation & Processing System · Image Processing Project Final_
