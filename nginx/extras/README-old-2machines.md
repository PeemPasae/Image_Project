# nginx — ประตูเดียวของ LUMA (ป้องกันคนนอกทีมเข้าหลังบ้าน)

> โฟลเดอร์นี้คือ config + สคริปต์สำหรับวาง nginx บน **เครื่อง Backend** (172.20.56.158)
> ให้ nginx เป็นทางเข้าเดียวของระบบ ส่วน Flask / Vite / SD WebUI ถูกซ่อนไว้ข้างหลัง

## ภาพรวมหลังวาง nginx

```
                    ┌──────────── เครื่อง Backend 172.20.56.158 ────────────┐
 ทุกคนใน LAN ──:80──▶ nginx ──┬── /            → frontend/luma-frontend/dist │
                    │        └── /api/v1/*    → 127.0.0.1:5000 (Flask)      │
 ทีม DEV ────:8089──▶ nginx ──── allowlist IP + รหัสผ่าน ──┐                │
                    │                                      │                │
                    │  :5000 Flask  bind 127.0.0.1 ← LAN เข้าตรงไม่ได้      │
                    │  :5173 Vite   bind localhost ← LAN เข้าตรงไม่ได้      │
                    └──────────────────────────────────────┼────────────────┘
                                                           ▼
                    ┌──────────── เครื่อง AI Server 172.20.56.221 ──────────┐
                    │  :8088 SD WebUI  ← firewall รับจาก 172.20.56.158 เท่านั้น │
                    └───────────────────────────────────────────────────────┘
```

| ใคร | เข้าได้ที่ | เห็นอะไร |
|---|---|---|
| ผู้ใช้ทั่วไปในวง LAN | `http://172.20.56.158/` | หน้าเว็บ + API 9 endpoint (ต้องมี JWT) |
| ทีม DEV (IP ใน `dev_allowlist.conf` + รหัส) | `http://172.20.56.158:8089/` | SD WebUI / `/sdapi/v1/*` ตรง ๆ |
| ทีม DEV | `http://172.20.56.158/_dev/backend/...` | ยิง Flask ตรงโดยไม่ผ่าน rate limit |
| คนนอก allowlist | `:8089`, `/_dev/` | **403** |
| ใครก็ตาม | `:5000`, `:5173`, `172.20.56.221:8088` | **connection refused / timeout** |

## ไฟล์ในโฟลเดอร์นี้

| ไฟล์ | หน้าที่ |
|---|---|
| `nginx.conf` | config ทั้งไฟล์ (มี `events`/`http`) — server :80 สาธารณะ + server :8089 DEV |
| `luma_proxy_backend.conf` | ชุด `proxy_pass` ไป Flask ที่ถูก include ซ้ำทุก location `/api/v1/*` |
| `dev_allowlist.conf` | รายชื่อ IP ทีม DEV (`allow …; deny all;`) — **แก้ไฟล์นี้เมื่อ IP เปลี่ยน** |
| `luma_dev.htpasswd` | รหัสผ่าน basic auth ของ `:8089` / `/_dev/` — สร้างด้วยสคริปต์ ไม่ commit |
| `scripts/make_htpasswd.sh` | สร้าง/เพิ่ม user ใน `luma_dev.htpasswd` |
| `scripts/firewall-backend.ps1` | Windows Firewall เครื่อง Backend: เปิด 80/8089, ปิด 5000/5173 |
| `scripts/firewall-ai-server.ps1` | Windows Firewall เครื่อง AI: 8088 รับจาก Backend เท่านั้น |
| `scripts/firewall-linux.sh` | เวอร์ชัน `ufw` ของสองไฟล์ข้างบน |

## ขั้นตอนวาง (ทำตามลำดับ)

### 0) สิ่งที่ต้องแก้ใน config ก่อน

1. `nginx.conf` → `upstream luma_ai_server` ใส่ IP ของเครื่อง AI ให้ตรงกับ `backend/.env` (`AI_SERVER_URL`)
2. `nginx.conf` → `root` ชี้ไปโฟลเดอร์ `dist` ของ frontend (Windows ต้องใส่ `"..."` เพราะ path มีช่องว่าง)
3. `dev_allowlist.conf` → IP ของทีม 4 คน (`ipconfig` / `ip a` ดูเอา)

### 1) Backend (นาย) — เครื่อง 172.20.56.158

```bash
cd backend
# .env ต้องมี 3 บรรทัดนี้เพิ่ม (มีให้แล้วใน .env ของ repo)
#   HOST=127.0.0.1        ← Flask รับเฉพาะจาก nginx บนเครื่องเดียวกัน
#   FLASK_DEBUG=0         ← ปิด Werkzeug debugger
#   CORS_ORIGINS=http://localhost:5173
python run.py
# ต้องเห็น:  Running on http://127.0.0.1:5000   (ไม่ใช่ 0.0.0.0)
```

### 2) Frontend (กร) — build แล้วส่งให้ nginx เสิร์ฟ

```bash
cd frontend/luma-frontend
npm run build        # อ่าน .env.production → VITE_API_BASE_URL=/api/v1 (relative ผ่าน nginx)
# ได้โฟลเดอร์ dist/ → ก๊อปไปวางบนเครื่อง Backend แล้วชี้ root ใน nginx.conf มาที่นี่
```

> ตอน dev ปกติ `npm run dev` จะเปิดแค่ `localhost:5173` แล้ว — ถ้าอยากให้เพื่อนเปิดดูจากเครื่องอื่นชั่วคราว
> ใช้ `npm run dev -- --host` (และต้องเติม IP เพื่อนใน `CORS_ORIGINS` + ตั้ง `HOST=0.0.0.0` ฝั่ง backend)

### 3) nginx — เครื่อง 172.20.56.158

**Windows** (โหลด zip จาก nginx.org แตกไว้ เช่น `C:\nginx`)

```powershell
# ก๊อป config
Copy-Item nginx\nginx.conf, nginx\luma_proxy_backend.conf, nginx\dev_allowlist.conf C:\nginx\conf\

# สร้างรหัสผ่าน DEV (Git Bash)  → ได้ nginx\luma_dev.htpasswd
bash nginx/scripts/make_htpasswd.sh nai
bash nginx/scripts/make_htpasswd.sh korn
Copy-Item nginx\luma_dev.htpasswd C:\nginx\conf\

cd C:\nginx
.\nginx.exe -t              # ต้องขึ้น "syntax is ok" + "test is successful"
.\nginx.exe                 # start   (ครั้งต่อไป: .\nginx.exe -s reload / -s stop)
```

**Linux (Ubuntu)**

```bash
sudo apt install nginx
sudo cp nginx/nginx.conf nginx/luma_proxy_backend.conf nginx/dev_allowlist.conf /etc/nginx/
bash nginx/scripts/make_htpasswd.sh nai && sudo cp nginx/luma_dev.htpasswd /etc/nginx/
sudo mkdir -p /var/www/luma && sudo cp -r frontend/luma-frontend/dist /var/www/luma/
sudo nginx -t && sudo systemctl restart nginx
```

> `nginx.conf` ใช้ `access_log logs/luma.access.log` ซึ่งเป็น path relative กับ prefix ของ nginx
> (Windows = `C:\nginx\logs\`, Linux = `/usr/share/nginx/logs/` หรือแก้เป็น `/var/log/nginx/…`)

### 4) Firewall — ทำทั้ง 2 เครื่อง (Run as Administrator)

```powershell
# เครื่อง Backend 172.20.56.158
powershell -ExecutionPolicy Bypass -File nginx\scripts\firewall-backend.ps1

# เครื่อง AI Server 172.20.56.221  (ใส่ IP ของ backend ให้ตรง)
powershell -ExecutionPolicy Bypass -File nginx\scripts\firewall-ai-server.ps1 -BackendIp 172.20.56.158
```

Linux: `sudo bash nginx/scripts/firewall-linux.sh backend` / `sudo bash nginx/scripts/firewall-linux.sh ai 172.20.56.158`

> ⚠ สคริปต์ AI Server ทำให้ **เครื่อง AI เองก็เปิด `http://172.20.56.221:8088` จากเครื่องอื่นไม่ได้** —
> ไอซ์ใช้ `http://127.0.0.1:8088` บนเครื่องตัวเอง หรือเข้าผ่าน `http://172.20.56.158:8089`

## Checklist ทดสอบว่าปิดหลังบ้านได้จริง

ยิงจาก **เครื่องที่ไม่อยู่ใน allowlist** (ยืมเครื่องเพื่อนนอกทีม หรือลบ IP ตัวเองออกชั่วคราว):

| # | คำสั่ง | ผลที่ต้องได้ |
|---|---|---|
| 1 | `curl -i http://172.20.56.158/healthz` | `200 ok` |
| 2 | `curl -i http://172.20.56.158/api/v1/models` | `200` JSON จาก Flask ผ่าน nginx |
| 3 | `curl -i http://172.20.56.158/api/v1/history` | `401 UNAUTHORIZED` (JWT ยังทำงาน) |
| 4 | `curl -i http://172.20.56.158/api/v2/x` | `404` (ไม่ถึง Flask) |
| 5 | `curl -i http://172.20.56.158/.env` | `403` |
| 6 | `curl -i http://172.20.56.158:8089/` | `403` |
| 7 | `curl -i http://172.20.56.158/_dev/backend/api/v1/models` | `403` |
| 8 | `curl -m 3 http://172.20.56.158:5000/api/v1/models` | timeout / connection refused |
| 9 | `curl -m 3 http://172.20.56.158:5173/` | timeout / connection refused |
| 10 | `curl -m 3 http://172.20.56.221:8088/sdapi/v1/sd-models` | timeout (firewall) |
| 11 | `for i in $(seq 1 20); do curl -s -o /dev/null -w "%{http_code} " -X POST http://172.20.56.158/api/v1/login -H 'Content-Type: application/json' -d '{}'; done` | มี `429` โผล่หลัง ~15 ครั้ง |

จาก **เครื่องทีม DEV** (IP อยู่ใน allowlist):

| # | คำสั่ง | ผลที่ต้องได้ |
|---|---|---|
| 12 | `curl -i http://172.20.56.158:8089/sdapi/v1/sd-models` | `401` (ขอรหัส) |
| 13 | `curl -i -u nai:<รหัส> http://172.20.56.158:8089/sdapi/v1/sd-models` | `200` รายชื่อ model |
| 14 | เปิด `http://172.20.56.158:8089/` ในเบราว์เซอร์ | หน้า SD WebUI ใช้งานได้ (websocket ผ่าน) |

ใครพยายามเข้าหลังบ้าน ดูได้ที่ `logs/luma.access.log` (มี IP ต้นทางทุกบรรทัด)

## เมื่อ IP เปลี่ยน (DHCP)

| อะไรเปลี่ยน | แก้ที่ |
|---|---|
| IP เครื่อง AI Server | `nginx.conf` → `upstream luma_ai_server`, `backend/.env` → `AI_SERVER_URL`, รัน `firewall-ai-server.ps1` ใหม่ไม่ต้อง (มันดู IP backend) |
| IP เครื่อง Backend | รัน `firewall-ai-server.ps1 -BackendIp <ใหม่>` บนเครื่อง AI, `dev_allowlist.conf` |
| IP เครื่องทีม DEV | `dev_allowlist.conf` แล้ว `nginx -s reload` |

## สิ่งที่ยัง "ไม่" ได้ทำ (ตัดสินใจกันในทีม)

- **HTTPS** — ในวง LAN มหาลัยไม่มี domain/cert; JWT วิ่งเป็น plain HTTP ใครดัก Wi‑Fi เดียวกันเห็น token ได้
  ถ้าจะทำ: self-signed cert + `listen 443 ssl` แล้วให้ทีมกด trust cert เอง
- **`--api-auth` / `--gradio-auth` บน SD WebUI** — ชั้นป้องกันเพิ่มบนเครื่อง AI เอง (ตอนนี้พึ่ง firewall อย่างเดียว)
  ถ้าเปิด ต้องแก้ `backend/app/services/ai_client.py` ให้ส่ง basic auth ไปด้วย
- **ถอด `--enable-insecure-extension-access`** ออกจาก `webui-user.*` — ใครเข้า WebUI ได้ = ติดตั้ง extension (รันโค้ด) ได้
  ตอนนี้ปิดทางเข้าไว้แล้วแต่ถ้าไม่ได้ใช้ก็ควรเอาออก
