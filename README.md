# LUMA — AI Image Generation & Processing System

> Project Final · รายวิชา Image Processing (ปี 3 เทอม 1) · ทีม 4 คน

LUMA คือเว็บแอปสำหรับ **สร้างรูปด้วย AI (Text-to-Image)** และ **แต่งรูปด้วย Computer Vision** ในที่เดียว

- **Generate** — พิมพ์ prompt เลือก checkpoint / sampler / ขนาด / steps / CFG / seed แล้วให้ Stable Diffusion สร้างรูป
- **Image Tools** — อัปโหลดรูปแล้วแต่งด้วย OpenCV + MediaPipe
  - เปิดในหน้าเว็บ (หน้า Features): **Spot Blur, Cartoonize, Hand Gesture, Remove Background**
  - มี API ใน Backend แล้ว แต่ยังไม่เปิดในหน้าเว็บ: **Tilt-Shift, HDR Enhancer** (เปิดได้ที่ `frontend/luma-frontend/src/features/active.js`)
- **History** — รูปที่สร้างจาก **Generate** ถูกเก็บพร้อมพารามิเตอร์ ดูย้อนหลัง ดาวน์โหลด ลบ หรือกด "Again" เพื่อสร้างซ้ำได้ (เห็นเฉพาะของตัวเอง)
  ผลจาก Image Tools ส่งกลับมาให้ดาวน์โหลดทันที **ไม่ได้บันทึกลง History**
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

> IP ในแผนภาพเป็นค่าที่ตั้งไว้ใน `nginx/conf/nginx.conf` และ `backend/.env.example`
> วง LAN มหาลัยเป็น DHCP — ถ้า IP เปลี่ยนให้ดูหัวข้อ [ถ้า IP เปลี่ยน ต้องแก้ที่ไหน](#-ถ้า-ip-เปลี่ยน-ต้องแก้ที่ไหน)

```
                 ผู้ใช้ในวง LAN  ──  http://192.168.1.171/
                                     │
          ┌──────────────────────────▼───────────────────────────┐
          │  Nginx  :80   — เครื่อง 192.168.1.171   (ไอซ์)          │
          │   /            → ไฟล์ static จาก frontend/.../dist      │
          │   /api/v1/*    → proxy → Backend  (rate limit)         │
          │   /api/*  อื่น → 404                                    │
          │  Nginx  :8089  — DEV เท่านั้น (allowlist + basic auth)    │
          │                → SD WebUI ของ AI Server                │
          └──────────────────────────┬───────────────────────────┘
                                     ▼
          ┌──────────────────────────────────────────────────────┐
          │  Flask Backend :5000 — เครื่อง 192.168.1.169   (นาย)     │
          │  JWT · Validation · GPU Lock/Queue · OpenCV/MediaPipe │
          └───────────────┬──────────────────────────┬───────────┘
                          ▼                          ▼
             SQLite  database/database.db     AI Server :8088 — 192.168.1.160 (ไอซ์)
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
OpenCV / MediaPipe บนเครื่อง Backend เอง (ไม่ใช้ GPU Server) → ส่ง PNG กลับ (ไม่บันทึกลงฐานข้อมูล)

---

## 🧰 Tech Stack

| ชั้น | เทคโนโลยี | พอร์ต | โฟลเดอร์ |
|---|---|---|---|
| **Gateway** | Nginx for Windows (มีเวอร์ชัน Linux), Cloudflare quick tunnel สำหรับเดโม | 80, 8089 | `nginx/` |
| **Frontend** | React 18, Vite 5, React Router 6, Axios, lucide-react, motion, Vitest + jsdom | 5173 (dev) | `frontend/luma-frontend/` |
| **Backend** | Flask 3, Flask-SQLAlchemy, Flask-CORS, PyJWT, python-dotenv, Werkzeug, Requests, OpenCV, NumPy, MediaPipe, pytest · Gunicorn (Linux, ติดตั้งแยก) | 5000 | `backend/` |
| **Database** | SQLite (ผ่าน SQLAlchemy) | — | `database/` |
| **AI Server** | Stable Diffusion WebUI (AUTOMATIC1111 / Forge) `--api --listen` | 8088 | `Ai Server/` |

---

## 📁 โครงสร้างโปรเจกต์

```
Image_Project/
├── nginx/                          # (ไอซ์) — คู่มือเต็ม: nginx/README.md
│   ├── START.bat / STOP.bat        # เปิด-รีโหลด / ปิด nginx
│   ├── LOGS.bat                    # ดู access log สด ๆ
│   ├── BUILD-WEB.bat               # npm install (ครั้งแรก) + npm run build หน้าเว็บใหม่หลัง git pull
│   ├── conf/
│   │   ├── nginx.conf              # upstream IP, root dist, rate limit, headers, :80 และ :8089
│   │   ├── luma_proxy_backend.conf # ชุด proxy_* ไป Flask (timeout 120s)
│   │   └── dev_allowlist.conf      # IP ทีม DEV ที่เข้าหลังบ้านได้
│   ├── firewall/                   # for-nginx / for-backend / for-ai .ps1 + linux.sh
│   └── extras/                     # Cloudflare demo tunnel, make_htpasswd.sh, คู่มือเดิม
├── Ai Server/                      # (ไอซ์) — ไม่ได้เก็บตัว webui เก็บแค่ config + สคริปต์ + เอกสาร
│   ├── .env.example                # AI_SERVER_URL สำหรับสคริปต์ทดสอบเท่านั้น
│   ├── config/webui-user.bat|.sh   # COMMANDLINE_ARGS: --api --listen --port 8088 ...
│   ├── scripts/check_server.py     # health check: options / sd-models / samplers
│   ├── scripts/test_txt2img.py     # ยิง txt2img ตรง ไม่ผ่าน Backend
│   └── models/                     # วาง checkpoint (ไฟล์จริงไม่ commit)
├── backend/                        # (นาย)
│   ├── run.py                      # entry point (dev) — อ่าน HOST / PORT / FLASK_DEBUG จาก .env
│   ├── gunicorn_conf.py            # production บน Linux (workers=1, threads=8 เพื่อให้ GPU lock ใช้ได้)
│   ├── config.py                   # ค่ากลาง: JWT, CORS, AI_SERVER_URL, upload 16 MB, log
│   ├── .env.example
│   ├── models/                     # โมเดล MediaPipe (.tflite / .task) — commit มาให้แล้ว
│   ├── scripts/
│   │   ├── download_models.py      # โหลดโมเดล MediaPipe ใหม่ (ถ้าไฟล์หาย / --force)
│   │   └── set_admin.py            # ตั้ง / ถอดสิทธิ์ admin, ดูรายชื่อผู้ใช้
│   ├── app/
│   │   ├── __init__.py             # app factory, CORS, ProxyFix, blueprints, /health, auto-migration
│   │   ├── models/                 # user.py (role), generation.py (category, params, image_data)
│   │   ├── routes/                 # auth, profile, sd, history, admin
│   │   ├── services/ai_client.py   # เรียก SD WebUI + GPU lock/queue + ประเมินเวลา
│   │   ├── services/image_filters/ # spot_blur, cartoonize, tilt_shift, hdr_enhancer, gesture, remove_bg + routes
│   │   ├── middleware/jwt_auth.py  # @token_required, @admin_required
│   │   └── utils/error_codes.py    # success / error envelope + error codes
│   ├── tests/                      # test_backend_full.py, test_image_filters_suite.py
│   ├── uploads/                    # (สร้างอัตโนมัติ) ไฟล์ภาพที่ generate — ไม่ commit
│   └── logs/                       # (สร้างอัตโนมัติ) luma_backend.log — ไม่ commit
├── database/                       # (ภีม)
│   ├── schema.sql                  # DDL: users + generations + index
│   ├── init_db.py                  # สร้าง database.db จาก schema.sql
│   ├── clear.py                    # ล้างข้อมูล (เลือกเก็บบาง user_id ได้)
│   └── Test1..3_*.py               # สคริปต์ทดสอบ insert / select (ใช้ไฟล์ app.db แยกจากของจริง)
├── frontend/
│   ├── index.html                  # prototype หน้าเดียว (เวอร์ชันแรก)
│   ├── luma-frontend.zip           # สำเนา zip ของ frontend
│   └── luma-frontend/              # (กร) React + Vite — ตัวจริง
│       ├── .env.example / .env.production
│       └── src/
│           ├── api/                # client.js (axios กลาง), errorMessages.js, mockData.js
│           ├── pages/              # Login, Register, Home, Generate, Features, Result, History, Profile, Setting, Admin
│           ├── components/         # Layout, ProtectedRoute, AuthImage, Toast, SkeletonCard, ErrorBoundary, MockModeBanner
│           ├── components/features/# หน้าเครื่องมือแต่งรูปแต่ละตัว + ImageUploader
│           ├── components/templates/ # ClassicLayout, SoftLayout
│           ├── features/           # registry.js (เครื่องมือทั้งหมด) + active.js (ตัวที่โชว์ในหน้า Features)
│           ├── context/            # Auth, Theme, Layout, Toast
│           ├── themes/ templates/  # สีธีม และ layout template (Classic / Soft)
│           ├── utils/              # modelSizes, roles, settingsStorage
│           └── test/               # Vitest
├── docs/                           # รายงาน Backend + Image Processing (.md / .docx)
└── git-graph.txt / git-history.txt # snapshot ประวัติ git ของโปรเจกต์
```

---

## 📦 สิ่งที่ต้องติดตั้งก่อน (Prerequisites)

| โปรแกรม | เวอร์ชัน | ใช้ที่เครื่อง | หมายเหตุ |
|---|---|---|---|
| Git | ล่าสุด | ทุกเครื่อง | Git Bash ใช้รัน `make_htpasswd.sh` ได้ด้วย |
| Python | 3.10 – 3.13 | Backend | ทดสอบแล้วกับ 3.13 |
| Python 3.10.x | 3.10.6 แนะนำ | AI Server | ตามที่ SD WebUI ต้องการ |
| Node.js | **18 – 22 LTS** | Frontend / Nginx (ใช้ build) | Node 25+ ทำให้ `npm test` พัง — ดู [แก้ปัญหา](#️-แก้ปัญหาที่เจอบ่อย) |
| Nginx for Windows | zip จาก nginx.org | Nginx | |
| NVIDIA GPU + CUDA driver | VRAM ≥ 6 GB | AI Server | VRAM < 8 GB ให้เปิด `--medvram` |

---

## ⚡ Quick Start — รันทุกอย่างในเครื่องเดียว (สำหรับ dev)

ไม่ต้องใช้ Nginx — เปิด Vite dev server แล้วให้ Frontend ยิงหา Backend ตรง ๆ

**1. Backend**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate                 # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                 # Linux/macOS: cp .env.example .env
```

แก้ `backend/.env` ให้เป็นค่าเครื่องเดียว:

```ini
HOST=127.0.0.1
AI_SERVER_URL=http://127.0.0.1:8088    # หรือ IP เครื่อง AI ของทีม
JWT_SECRET_KEY=<สุ่มใหม่ ดูคำสั่งด้านล่าง>
```

```powershell
python run.py                          # → http://127.0.0.1:5000/api/v1/health ต้องได้ "status": "healthy"
```

**2. Frontend** (เปิด terminal ใหม่)

```powershell
cd frontend/luma-frontend
npm install
copy .env.example .env
```

แก้ `frontend/luma-frontend/.env`:

```ini
VITE_API_BASE_URL=http://localhost:5000/api/v1   # ⚠ ค่า default /api/v1 ใช้ได้เฉพาะเมื่ออยู่หลัง Nginx
VITE_MOCK_MODE=false
```

```powershell
npm run dev                            # → http://localhost:5173
```

**3. ใช้งาน**

1. เปิด `http://localhost:5173` → สมัครสมาชิก → login
2. (ถ้าต้องการหน้า Admin) ตั้งตัวเองเป็น admin แล้ว logout / login ใหม่
   ```powershell
   cd backend
   python scripts/set_admin.py you@example.com
   ```
3. Image Tools ใช้ได้ทันทีโดยไม่ต้องมี AI Server · หน้า Generate ต้องมี AI Server ออนไลน์

> **อยากดูแค่หน้าเว็บ ไม่มี Backend:** ตั้ง `VITE_MOCK_MODE=true` ใน `.env` ของ frontend แล้ว `npm run dev` —
> ทุกหน้าใช้ข้อมูลปลอม และมีแถบ Mock Mode แสดงบนจอ

---

## 🚀 Setup แบบใช้งานจริง (3 เครื่องในวง LAN)

**ลำดับเปิดระบบ:** AI Server → Backend → Nginx (Nginx เป็นตัว build + เสิร์ฟ Frontend ให้)

### 1) AI Server — ไอซ์ (เครื่อง 192.168.1.160)

```powershell
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git   # หรือ Forge
cd stable-diffusion-webui
copy "<path>\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat
# วาง checkpoint .safetensors ลง models\Stable-diffusion\
webui-user.bat                         # ครั้งแรกจะติดตั้ง torch นานหน่อย
```

Flag ที่ **ห้ามลบ**: `--api` · `--listen` · `--port 8088`
(ใน `webui-user.bat` ให้แก้ `--cors-allow-origins=` ให้เป็น IP เครื่อง Backend / Nginx ของตัวเอง)

ทดสอบ AI Server โดยไม่ผ่าน Backend:

```powershell
cd "Ai Server"
pip install -r scripts/requirements.txt
copy .env.example .env                 # ตั้ง AI_SERVER_URL (หรือใช้ --url ทุกครั้ง)
python scripts/check_server.py --url http://127.0.0.1:8088
python scripts/test_txt2img.py --url http://127.0.0.1:8088 -p "a cat astronaut" --steps 20 --width 512 --height 512
```

> ถ้า 2 สคริปต์นี้ผ่าน แต่หน้าเว็บสร้างรูปไม่ได้ → ปัญหาอยู่ฝั่ง Backend / Nginx / Frontend
> รายละเอียด + ตารางแก้ปัญหา: [`Ai Server/README.md`](Ai%20Server/README.md)

### 2) Backend — นาย (เครื่อง 192.168.1.169)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env              # แล้วแก้ค่าตามตารางด้านล่าง
python run.py                       # http://0.0.0.0:5000
```

ตอนสตาร์ท `run.py` จะพิมพ์สถานะออกมา — ต้องเห็น `AI Models Status: [READY]`
ถ้าขึ้น `Missing models` ให้รัน `python scripts/download_models.py` (Remove BG / Gesture ใช้โมเดลนี้)

| ตัวแปร `backend/.env` | ความหมาย | ถ้าไม่ตั้ง |
|---|---|---|
| `PORT` | พอร์ต Flask | `5000` |
| `HOST` | `0.0.0.0` เมื่อ Nginx อยู่คนละเครื่อง · `127.0.0.1` เมื่ออยู่เครื่องเดียวกัน | `0.0.0.0` |
| `JWT_SECRET_KEY` | ค่าลับเซ็น JWT — `python -c "import secrets; print(secrets.token_urlsafe(48))"` | ค่า default ใน `config.py` (**ห้ามใช้จริง**) |
| `AI_SERVER_URL` | เช่น `http://192.168.1.160:8088` | `http://172.20.57.0:8088` (มักผิด — ตั้งเสมอ) |
| `FLASK_DEBUG` | `0` เสมอเมื่อเปิดรับจาก LAN | ปิด |
| `CORS_ORIGINS` | คั่นด้วย `,` เช่น `http://192.168.1.171,http://localhost:5173` | localhost:5173 + `*` |
| `UPLOAD_FOLDER` | (ไม่บังคับ) ที่เก็บไฟล์ภาพ | `backend/uploads` |
| `LOG_LEVEL` / `LOG_FILE` | (ไม่บังคับ) ระดับ log / ไฟล์ log | `INFO` / `backend/logs/luma_backend.log` |

ตรวจ: `http://127.0.0.1:5000/api/v1/health` ต้องได้ `"status": "healthy"` (response แสดง `ai_server_url` ที่ใช้อยู่ด้วย)

ตั้งผู้ใช้เป็น admin (ต้องสมัครผ่านหน้าเว็บก่อน · รันจากโฟลเดอร์ไหนก็ได้):

```powershell
python scripts/set_admin.py --list
python scripts/set_admin.py user@example.com
python scripts/set_admin.py --revoke user@example.com
```

> **ฐานข้อมูล:** ไม่ต้องรันอะไรเพิ่ม — Backend สร้างตาราง / เพิ่มคอลัมน์ที่ขาดใน `database/database.db` ให้อัตโนมัติตอนสตาร์ท
> (`python database/init_db.py` ใช้สร้างจาก `schema.sql` ด้วยมือได้ถ้าต้องการ)
>
> **Production บน Linux:** `pip install gunicorn` แล้ว `gunicorn -c gunicorn_conf.py run:app` (ต้อง workers=1 เพื่อให้ GPU lock ทำงาน)

### 3) Frontend — กร

ใช้งานจริงไม่ต้องรัน dev server — Nginx เสิร์ฟไฟล์ที่ build แล้ว (`BUILD-WEB.bat` ทำให้)

```powershell
cd frontend/luma-frontend
npm install
npm run build               # build ไป dist/ (อ่าน .env.production → VITE_API_BASE_URL=/api/v1 เสมอ)
npm run preview             # (ไม่บังคับ) ดูไฟล์ build ในเครื่อง
npm test                    # Vitest
```

| ตัวแปร | ความหมาย |
|---|---|
| `VITE_API_BASE_URL` | `/api/v1` เมื่อผ่าน Nginx · `http://localhost:5000/api/v1` เมื่อ `npm run dev` ต่อ Backend ตรง (Vite ไม่มี proxy) |
| `VITE_MOCK_MODE` | `true` = เดินดูทุกหน้าด้วยข้อมูลปลอม ไม่ต้องมี Backend · `false` = ต่อ Backend จริง |

> `npm run dev` bind `0.0.0.0:5173` แบบ `strictPort` — ถ้าพอร์ตถูกใช้จะ error ทันทีแทนที่จะย้ายพอร์ต

### 4) Nginx — ไอซ์ (เครื่อง 192.168.1.171)

ตั้งค่าครั้งแรก:

1. โหลด Nginx for Windows (zip) จาก nginx.org แตกไว้ที่ `nginx\win\` ให้ได้ `nginx\win\nginx-x.y.z\nginx.exe`
2. แก้ `nginx\conf\nginx.conf`
   - `upstream luma_backend` → IP:พอร์ต ของ Backend
   - `upstream luma_ai_server` → IP:พอร์ต ของ AI Server
   - `root` → path ของ `frontend/luma-frontend/dist` **ในเครื่องตัวเอง** (ค่าใน repo เป็น path เครื่องเพื่อน · ใช้ `/` ไม่ใช่ `\`)
3. (ถ้าจะใช้หลังบ้าน `:8089` / `/_dev/backend/`) ใส่ IP ทีม DEV ใน `conf\dev_allowlist.conf` และสร้างรหัสด้วย Git Bash
   ```bash
   bash nginx/extras/make_htpasswd.sh <username>     # ได้ไฟล์ nginx/luma_dev.htpasswd — START.bat ก๊อปเข้า nginx ให้เอง
   ```
4. รัน firewall ครั้งเดียวต่อเครื่อง (PowerShell แบบ Run as Administrator)
   ```powershell
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-nginx.ps1     # เครื่อง nginx
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-backend.ps1   # เครื่อง Backend
   powershell -ExecutionPolicy Bypass -File nginx\firewall\for-ai.ps1        # เครื่อง AI
   ```
   Linux ใช้ `nginx/firewall/linux.sh`
5. ดับเบิลคลิก `BUILD-WEB.bat` (ครั้งแรกจะ `npm install` ให้) → `START.bat`

ใช้งานประจำวัน:

| ไฟล์ | ใช้ตอนไหน |
|---|---|
| `START.bat` | เปิด nginx หรือกดซ้ำหลังแก้ `conf\` (คัดลอก config → `nginx -t` → start/reload) |
| `STOP.bat` | ปิด nginx |
| `LOGS.bat` | ดูว่าใครเข้าเว็บ ขออะไร |
| `BUILD-WEB.bat` | หลัง `git pull` ที่มีการแก้หน้าเว็บ (ไม่ต้อง restart nginx) |

สิ่งที่ Gateway ทำ:

| เรื่อง | รายละเอียด |
|---|---|
| ประตูเดียว | ผู้ใช้เข้าได้แค่ `:80` — Flask, Vite, SD WebUI ห้ามเข้าตรง |
| จำกัด API | ผ่านเฉพาะ `/api/v1/*` · path อื่นใต้ `/api/` ตอบ 404 |
| Rate limit | login / register 10 ครั้ง/นาที · API อื่น 120 ครั้ง/นาที ต่อ IP → `429` |
| Upload | `client_max_body_size 16m` ให้ตรงกับ Backend |
| Security | ซ่อนเวอร์ชัน nginx, `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, กันเข้าไฟล์ `.env/.db/.py/...` |
| Performance | gzip, cache `/assets/` 1 ปี (ไฟล์ Vite มี hash) |
| Backend ล่ม | ตอบ JSON `{"success":false,"error":{"code":"INTERNAL_SERVER_ERROR",...}}` แทนหน้า 502 |
| DEV gateway | `:8089` → SD WebUI (allowlist IP + basic auth) และ `/_dev/backend/` |
| เดโมนอก LAN | Cloudflare quick tunnel → `:80` อย่างเดียว ได้ HTTPS (ดู `nginx/extras/DEMO-cloudflared.md`) |

ตรวจ: `http://localhost/healthz` → `ok` · `http://localhost/api/v1/health` → `healthy`

> คู่มือเต็ม + แก้ปัญหา: [`nginx/README.md`](nginx/README.md)

### 🔁 ถ้า IP เปลี่ยน ต้องแก้ที่ไหน

| เครื่องที่ IP เปลี่ยน | ไฟล์ที่ต้องแก้ | แล้วทำ |
|---|---|---|
| Backend | `nginx/conf/nginx.conf` → `upstream luma_backend` | `START.bat` |
| AI Server | `backend/.env` → `AI_SERVER_URL` · `nginx.conf` → `upstream luma_ai_server` · `Ai Server/.env` | restart `run.py` + `START.bat` |
| Nginx | `backend/.env` → `CORS_ORIGINS` · `nginx/conf/dev_allowlist.conf` · `--cors-allow-origins` ใน `webui-user.bat` | restart `run.py` / webui + `START.bat` |
| ทุกเครื่อง | รัน `nginx/firewall/*.ps1` ใหม่ (กฎอ้าง IP) | — |

---

## 🔌 API

Base URL: `/api/v1` · 🔒 = ต้องมี `Authorization: Bearer <JWT>` · 👑 = admin เท่านั้น

| Method | Endpoint | Auth | คำอธิบาย |
|---|---|:--:|---|
| GET | `/health` | | สถานะ Backend |
| POST | `/register` | | สมัครสมาชิก (password ≥ 8 ตัว, hash ด้วย Werkzeug) |
| POST | `/login` | | เข้าสู่ระบบ → `access_token` อายุ 24 ชม. + `user` (มี `role`) |
| GET | `/models` | | รายชื่อ checkpoint จาก AI Server |
| POST | `/generate` | 🔒 | สร้างรูป → `generation_id`, `image_url`, `seed`, `estimated_time_seconds`, `actual_time_seconds` |
| GET | `/images/:id` | 🔒 | ไฟล์ PNG (binary) — เช็คเจ้าของกัน IDOR |
| GET | `/history` | 🔒 | ประวัติของตัวเอง `?page=1&limit=20` |
| GET | `/history/:id` | 🔒 | รายละเอียด 1 รายการ |
| DELETE | `/history/:id` | 🔒 | ลบรายการ + ไฟล์ภาพ |
| GET | `/profile` | 🔒 | ข้อมูลผู้ใช้ + `generation_count` |
| POST | `/process/spot-blur` | 🔒 | เบลอเฉพาะจุด (`circles`, `strength`, `soft`) |
| POST | `/process/cartoonize` | 🔒 | ภาพสไตล์การ์ตูน (`num_colors`, `line_thickness`, `smoothness`) |
| POST | `/process/tilt-shift` | 🔒 | จำลองโมเดลจิ๋ว _(ยังไม่เปิดในหน้าเว็บ)_ |
| POST | `/process/hdr-enhancer` | 🔒 | เพิ่มรายละเอียด / คอนทราสต์สไตล์ HDR _(ยังไม่เปิดในหน้าเว็บ)_ |
| POST | `/process/gesture` | 🔒 | จดจำท่ามือ 7 แบบ (MediaPipe) |
| POST | `/process/remove-bg` | 🔒 | ลบพื้นหลัง (MediaPipe + GrabCut) |
| GET | `/admin/users` | 👑 | รายชื่อผู้ใช้ทั้งหมด + จำนวนรูป |
| DELETE | `/admin/users/:id` | 👑 | ลบผู้ใช้ + รูปทั้งหมดของผู้ใช้ (ลบตัวเองไม่ได้) |

`/process/*` รับ `multipart/form-data` (field `image`: .jpg .jpeg .png .webp ≤ 16 MB)

> Backend รับ path แบบไม่มี `/api/v1` ด้วย (เช่น `/login`, `/health`) เพื่อกัน 404 — แต่ผ่าน Nginx ใช้ได้เฉพาะ `/api/v1/*`

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
{ "success": true, "data": { "generation_id": 123, "image_url": "/api/v1/images/123", "seed": 123456789,
  "estimated_time_seconds": 4.5, "actual_time_seconds": 5.1, "created_at": "..." } }
```

### Authentication

- JWT แบบ HS256 อายุ **24 ชั่วโมง** payload มี `user_id`, `email`
- Frontend เก็บใน `localStorage` และแนบผ่าน axios interceptor · ถ้าได้ `UNAUTHORIZED` จะ logout + กลับไป `/login`
- รูปภาพต้องแนบ JWT จึงโหลดผ่าน `AuthImage` (Blob) แทน `<img src>`
- `@admin_required` เช็ค `role` จากฐานข้อมูลทุกครั้ง — เมนู Admin ในหน้าเว็บซ่อนไว้แค่เพื่อ UX

---

## 🗄️ ฐานข้อมูล

ไฟล์จริง: `database/database.db` (SQLite — อยู่ใน `.gitignore` แต่ยังถูก track ใน git อยู่ ระวัง commit ข้อมูลทดสอบติดไป) · `users 1 : N generations` (`ON DELETE CASCADE`) · index ที่ `user_id`, `category`, `created_at`

**`users`** — `id`, `email` (UNIQUE), `password_hash`, `role` (`user` / `admin`), `created_at`

**`generations`**

| Field | Note |
|---|---|
| `id`, `user_id` | PK / FK → `users.id` |
| `category`, `action_type` | แยกประเภท ปัจจุบันมีแค่ `sd_generate` / `txt2img` (เผื่อไว้สำหรับเครื่องมืออื่นในอนาคต) |
| `prompt`, `negative_prompt`, `checkpoint`, `sampler` | พารามิเตอร์ SD |
| `width`, `height`, `steps`, `cfg_scale`, `seed` | พารามิเตอร์ SD |
| `params` | JSON ของ request ทั้งก้อน |
| `source_image_id` | อ้างถึงรูปต้นทาง (สำรองไว้ ยังไม่ได้ใช้) |
| `image_data` / `image_path` | ไบต์ PNG ในฐานข้อมูล + ไฟล์สำเนาบนดิสก์ (`backend/uploads/generations/<id>.png`) |
| `created_at` | |

> Backend เพิ่มคอลัมน์ที่ขาดให้อัตโนมัติตอนสตาร์ท จึงใช้กับฐานข้อมูลเก่าได้โดยข้อมูลไม่หาย

---

## ✅ กติกาที่ตกลงกัน

| Field | Rule | ตรวจที่ |
|---|---|---|
| `width` / `height` | 512, 768 หรือ 1024 | Backend + Frontend |
| `steps` | 1–50 (default 20) | Backend + Frontend |
| `cfg_scale` | 1–20 (default 7) | Backend + Frontend |
| `seed` | -1 (สุ่ม) หรือ 0–2147483647 | Frontend |
| `sampler` | `DPM++ 2M Karras` (default ในหน้าเว็บ) / `Euler a` (default ของ Backend ถ้าไม่ส่งมา) / `Euler` | Frontend |
| `prompt` / `negative_prompt` | prompt required · ทั้งคู่ ≤ 2000 ตัวอักษร | Backend + Frontend |
| `password` | ≥ 8 ตัวอักษร | Backend + Frontend |
| upload | .jpg .jpeg .png .webp, ≤ 16 MB | Backend + Nginx |

**Timeout:** Backend → AI Server 75s · Frontend → `/generate` 90s · Nginx → Backend 120s · รอคิว GPU สูงสุด 40s

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
| AI Server | `python "Ai Server/scripts/check_server.py" --url <url>` / `test_txt2img.py` | API online, checkpoint, sampler, สร้างรูปจริง |
| Backend | `cd backend` แล้ว `python -m pytest tests` (ต้อง activate venv ก่อน) | สมัคร / login / JWT, IDOR, pagination, คิว GPU, profile, health, การเก็บไฟล์, admin, image filters ทุกตัว — ใช้ SQLite in-memory ไม่แตะข้อมูลจริง ไม่ต้องมี AI Server |
| Database | `cd database` แล้ว `python Test1_create_user.py` → `Test2_insert_generation.py` → `Test3_select_all.py` | insert / select (เขียนลง `database/app.db` ไม่ใช่ `database.db`) |
| Frontend | `cd frontend/luma-frontend && npm test` | API contract, admin, ขนาดรูปตามโมเดล, settings, ErrorBoundary |
| ทั้งระบบ | `http://<nginx>/healthz` และ `/api/v1/health` | Nginx → Backend ต่อกันได้ |

> ⚠ Backend ต้องใช้ `python -m pytest` — ถ้าพิมพ์ `pytest tests` เฉย ๆ จะเจอ `ModuleNotFoundError: No module named 'app'`

---

## 🛠️ แก้ปัญหาที่เจอบ่อย

| อาการ | ดูที่ |
|---|---|
| หน้าเว็บขึ้น แต่ login ไม่ได้ / "Backend is unavailable" | Backend ไม่ได้รัน, `HOST` ไม่ใช่ `0.0.0.0`, หรือ firewall เครื่อง Backend ยังไม่อนุญาตเครื่อง Nginx |
| `npm run dev` แล้ว login ไม่ได้ / 404 ที่ `/api/v1/...` | `VITE_API_BASE_URL` ยังเป็น `/api/v1` → เปลี่ยนเป็น `http://localhost:5000/api/v1` |
| CORS error ใน console ของ browser | origin ของหน้าเว็บไม่อยู่ใน `CORS_ORIGINS` ของ `backend/.env` |
| ไม่มีรายชื่อโมเดล / สร้างรูปไม่ได้ | AI Server ไม่ได้รัน, `AI_SERVER_URL` ผิด (เช็คจาก `/api/v1/health`), หรือ firewall เครื่อง AI → `check_server.py` |
| `AI_SERVER_BUSY` | มีคนสร้างรูปอยู่และรอคิวเกิน 40s — ลองใหม่ |
| Remove BG / Gesture ได้ `MODEL_UNAVAILABLE` | ไม่มีโมเดลใน `backend/models/` → `python scripts/download_models.py` |
| `pytest` ขึ้น `No module named 'app'` | ใช้ `python -m pytest tests` จากในโฟลเดอร์ `backend/` |
| `npm test` fail ด้วย `Cannot read properties of undefined (reading 'setItem')` | ใช้ Node 25+ (มี `localStorage` ในตัวไปทับของ jsdom) → ใช้ Node 22 LTS หรือรัน `$env:NODE_OPTIONS="--no-experimental-webstorage"; npm test` |
| หน้า Admin ไม่ขึ้นหลัง `set_admin.py` | logout แล้ว login ใหม่ให้ได้ token / `role` ใหม่ |
| เครื่องอื่นเปิดเว็บไม่ได้ | `nginx/firewall/for-nginx.ps1` และตั้ง Wi-Fi เป็น Private |
| แก้หน้าเว็บแล้วไม่เปลี่ยน | ลืม `BUILD-WEB.bat` |
| `:8089` ได้ 403 | IP ตัวเองไม่อยู่ใน `dev_allowlist.conf` → แก้แล้ว `START.bat` |
| `413` / `429` | ไฟล์เกิน 16 MB / กดถี่เกิน rate limit |

---

## 📚 เอกสารเพิ่มเติม

| ไฟล์ | เนื้อหา |
|---|---|
| [`nginx/README.md`](nginx/README.md) | คู่มือ Nginx Gateway ฉบับเต็ม |
| [`nginx/extras/DEMO-cloudflared.md`](nginx/extras/DEMO-cloudflared.md) | เปิดเดโมให้คนนอกวง LAN |
| [`Ai Server/README.md`](Ai%20Server/README.md) | ติดตั้ง / ทดสอบ / แก้ปัญหา AI Server |
| [`Ai Server/config/README-config.md`](Ai%20Server/config/README-config.md) | อธิบาย flag ใน `webui-user` |
| [`Ai Server/models/README.md`](Ai%20Server/models/README.md) | วาง checkpoint / LoRA / VAE |
| [`frontend/luma-frontend/README.md`](frontend/luma-frontend/README.md) | โครงสร้าง Frontend และ Mock Mode |
| [`docs/BACKEND_CAPABILITIES.md`](docs/BACKEND_CAPABILITIES.md) | ความสามารถทั้งหมดของ Backend |
| [`docs/BACKEND_USER_GUIDE.md`](docs/BACKEND_USER_GUIDE.md) | คู่มือใช้งาน Backend |
| [`docs/BACKEND_REPORT.md`](docs/BACKEND_REPORT.md) · [`docs/BACKEND_CODE_REVIEW.md`](docs/BACKEND_CODE_REVIEW.md) | รายงาน + code review ฝั่ง Backend |
| [`docs/IMAGE_PROCESSING_REPORT.md`](docs/IMAGE_PROCESSING_REPORT.md) | อัลกอริทึมของเครื่องมือแต่งรูป |
| [`docs/FRONTEND_REQUIREMENTS.md`](docs/FRONTEND_REQUIREMENTS.md) | Requirement ฝั่ง Frontend |

---

## 🌿 Git Workflow

- ห้าม push ตรงเข้า `main` — 1 Issue → 1 branch (`<issue>-<type>/<area>-<name>`) → เปิด PR
- Commit แบบ Conventional Commits: `type(scope): description` เช่น `feat(nginx): ...`, `fix(frontend): ...`
- ห้าม commit: `.env`, `*.htpasswd`, `nginx/win/`, checkpoint `.safetensors` / `.ckpt`, `node_modules/`, `dist/`, `backend/uploads/` และไม่ควร commit การเปลี่ยนแปลงของ `database/*.db`

---

## 🔭 Future Features

Image-to-Image · Upscale · Inpainting · ControlNet · Change Password · HTTPS ถาวรบน Nginx ·
เปิด Tilt-Shift / HDR Enhancer ในหน้าเว็บ · บันทึกผล Image Tools ลง History

---

_LUMA — AI Image Generation & Processing System · Image Processing Project Final_
