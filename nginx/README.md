# nginx — ประตูหน้าของ LUMA

คนใช้เว็บเปิดแค่ **`http://192.168.1.171/`** แล้ว nginx จะส่งต่อให้เครื่องอื่นเอง

```
คนเปิดเว็บ ──► nginx (192.168.1.171) ──► Backend (192.168.1.169:5000) ──► AI Server (192.168.1.160:8088)
                 │
                 └─ หน้าเว็บ: ส่งไฟล์จาก frontend/luma-frontend/dist ในเครื่องตัวเอง
```

| คำขอ | nginx ทำอะไร |
|---|---|
| `/` , `/admin`, `/history` … | ส่งหน้าเว็บจากโฟลเดอร์ `dist` |
| `/api/v1/...` | ส่งต่อไป Backend |

---

## ใช้งานประจำวัน (เครื่อง nginx) — ดับเบิลคลิกได้เลย

| ไฟล์ | ใช้ตอนไหน |
|---|---|
| **`START.bat`** | เปิด nginx — หรือกดซ้ำหลังแก้ไฟล์ใน `conf\` (โหลด config ใหม่ ไม่ต้องปิดก่อน) |
| **`STOP.bat`** | ปิด nginx |
| **`LOGS.bat`** | ดูสด ๆ ว่าใครเข้าเว็บ ขออะไร (กด `Ctrl+C` เพื่อหยุด) |
| **`BUILD-WEB.bat`** | หลัง `git pull` ที่มีการแก้หน้าเว็บ → build ใหม่ แล้ว refresh เบราว์เซอร์ |

ลำดับเปิดระบบ: **AI Server → Backend → `START.bat`**
เช็คว่าครบ: เปิด `http://localhost/api/v1/health` ต้องเห็น `healthy`

---

## โฟลเดอร์นี้มีอะไร

```
nginx/
├── START.bat  STOP.bat  LOGS.bat  BUILD-WEB.bat   ← ใช้ทุกวัน
├── conf/        ← ตั้งค่า (แก้แล้วกด START.bat)
│   ├── nginx.conf               IP ของ Backend/AI, ที่อยู่ dist, rate limit, ขนาดอัปโหลด
│   ├── luma_proxy_backend.conf  วิธีส่งต่อไป Backend (timeout ฯลฯ) — แทบไม่ต้องแตะ
│   └── dev_allowlist.conf       IP ที่เข้าหน้าหลังบ้าน :8089 ได้
├── firewall/    ← รันครั้งเดียวต่อเครื่อง (คลิกขวา PowerShell → Run as Administrator)
│   ├── for-nginx.ps1    เครื่อง nginx   : เปิดพอร์ต 80 ให้คนในวง LAN
│   ├── for-backend.ps1  เครื่อง Backend : พอร์ต 5000 รับจากเครื่อง nginx เท่านั้น
│   ├── for-ai.ps1       เครื่อง AI      : พอร์ต 8088 รับจากเครื่อง Backend เท่านั้น
│   └── linux.sh         เวอร์ชัน Linux
├── extras/      ← ไม่ค่อยได้ใช้
│   ├── DEMO-cloudflared.md + demo-tunnel.ps1   เปิดให้คนนอกวง LAN เข้าชั่วคราว (เดโมให้อาจารย์)
│   ├── make_htpasswd.sh                        ตั้งรหัสผ่านหน้าหลังบ้าน :8089
│   └── README-old-2machines.md                 คู่มือเดิม (ตอนใช้ 2 เครื่อง วง 172.20.x.x)
└── win/         ← ตัวโปรแกรม nginx + log (ไม่ขึ้น GitHub)
    └── nginx-x.y.z/logs/  luma.access.log (ใครเข้า), luma.error.log (ข้อผิดพลาด)
```

> ⚠ อย่าแก้ไฟล์ใน `win\nginx-x.y.z\conf\` — `START.bat` จะก๊อปจาก `conf\` ทับทุกครั้ง

---

## ตั้งค่าครั้งแรก (ทำครั้งเดียว)

**เครื่อง nginx**
1. โหลด nginx สำหรับ Windows (zip) จาก nginx.org แตกไว้ใน `nginx\win\` ให้ได้ `nginx\win\nginx-x.y.z\nginx.exe`
2. แก้ `conf\nginx.conf` บรรทัด `root` ให้ชี้ไปที่ `frontend/luma-frontend/dist` ในเครื่องตัวเอง (ใช้ `/` ไม่ใช่ `\`)
3. `BUILD-WEB.bat` → `START.bat`
4. ถ้าเครื่องอื่นเข้าไม่ได้: `firewall\for-nginx.ps1`

**เครื่อง Backend** — `backend\.env` ต้องมี `HOST=0.0.0.0` แล้วรัน `firewall\for-backend.ps1`

**เครื่อง AI** — รัน `firewall\for-ai.ps1`

```powershell
powershell -ExecutionPolicy Bypass -File nginx\firewall\for-backend.ps1
```

---

## IP เปลี่ยน ต้องแก้ที่ไหน

| อะไรเปลี่ยน | แก้ |
|---|---|
| เครื่อง **nginx** | `firewall\for-backend.ps1 -NginxIp <ใหม่>` บนเครื่อง Backend, `CORS_ORIGINS` ใน `backend\.env`, `conf\dev_allowlist.conf` |
| เครื่อง **Backend** | `conf\nginx.conf` → `upstream luma_backend`, `firewall\for-ai.ps1 -BackendIp <ใหม่>` บนเครื่อง AI |
| เครื่อง **AI** | `AI_SERVER_URL` ใน `backend\.env` (แล้ว restart backend), `conf\nginx.conf` → `upstream luma_ai_server` |

แก้ `conf\` แล้วกด `START.bat` ทุกครั้ง

---

## แก้ปัญหา

| อาการ | สาเหตุที่พบบ่อย |
|---|---|
| หน้าเว็บขึ้น แต่ login ไม่ได้ / "Backend is unavailable" | Backend ไม่ได้รัน หรือ firewall เครื่อง Backend ยังไม่อนุญาตเครื่อง nginx |
| ไม่มีรายชื่อโมเดล / สร้างรูปไม่ได้ | AI Server ไม่ได้รัน หรือ firewall เครื่อง AI ยังไม่อนุญาตเครื่อง Backend |
| `localhost` เปิดได้ แต่เครื่องอื่นเปิดไม่ได้ | Windows Firewall เครื่อง nginx → `firewall\for-nginx.ps1` / Wi‑Fi ต้องเป็น Private |
| `START.bat` บอก port 80 ถูกใช้ | มีโปรแกรมอื่นจองพอร์ต 80 (เช่น IIS) — `netstat -ano \| findstr :80` ดู PID |
| แก้หน้าเว็บแล้วไม่เปลี่ยน | ลืม `BUILD-WEB.bat` |
| อัปโหลดรูปแล้วได้ 413 | ไฟล์ใหญ่เกิน 16 MB (`client_max_body_size` ใน `conf\nginx.conf`) |
| 429 Too Many Requests | กดถี่เกิน (login 10 ครั้ง/นาที, API 120 ครั้ง/นาที ต่อคน) |
