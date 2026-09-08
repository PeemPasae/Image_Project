# Ai Server — Luma (👤 ไอซ์)

AI Server ของโปรเจกต์ Luma คือ **AUTOMATIC1111 Stable Diffusion WebUI (หรือ Forge)**
ที่เปิดโหมด `--api` ไว้ให้ Backend เรียก โฟลเดอร์นี้ **ไม่ได้เก็บตัว webui**
แต่เก็บ *ค่าตั้งต้น + สคริปต์ทดสอบ + เอกสาร* ที่ทีมต้องใช้ร่วมกัน

```
[Frontend :5173] → [Backend Flask 172.20.57.59:5000] → [AI Server 172.20.57.51:8088]
                                                        ← base64 PNG
```

---

## 1. สเปกเครื่อง (ขั้นต่ำ)

| หัวข้อ | ขั้นต่ำ | แนะนำ |
|---|---|---|
| GPU | NVIDIA 6 GB VRAM | NVIDIA 12 GB+ (SDXL 1024×1024) |
| Driver | รองรับ CUDA 12.1 | ล่าสุด |
| RAM | 16 GB | 32 GB |
| Disk | 30 GB ว่าง | 100 GB (หลาย checkpoint) |
| Python | 3.10.x | 3.10.11 |

> VRAM < 8 GB ให้เติม `--medvram` หรือ `--lowvram` ใน `COMMANDLINE_ARGS`
> และบอก Frontend ให้ลดขนาด default จาก 1024 → 512

---

## 2. ติดตั้งครั้งแรก

```bash
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
```

ก๊อปไฟล์ config ทับ:

```bash
# Linux
cp "../Image_Project/Ai Server/config/webui-user.sh"  ./webui-user.sh
# Windows
copy "..\Image_Project\Ai Server\config\webui-user.bat" webui-user.bat
```

วาง checkpoint (`.safetensors`) ลงใน `stable-diffusion-webui/models/Stable-diffusion/`
รายละเอียดว่าใช้ตัวไหน ดู [`models/README.md`](models/README.md)

---

## 3. Start server

```bash
# Linux
./webui.sh
# Windows
webui-user.bat
```

พร้อมใช้งานเมื่อเห็นบรรทัด:

```
Running on local URL:  http://0.0.0.0:8088
```

เช็คจากอีกเครื่อง:

```bash
curl http://172.20.57.51:8088/sdapi/v1/sd-models
```

---

## 4. ทดสอบด้วยสคริปต์ (ไม่ผ่าน Backend)

```bash
pip install -r scripts/requirements.txt

# 4.1 เช็คว่า API ออนไลน์ + มี checkpoint + มี sampler 'Euler a'
python scripts/check_server.py

# 4.2 ยิงสร้างรูปจริง ผลลัพธ์ลง outputs/
python scripts/test_txt2img.py
python scripts/test_txt2img.py -p "a cat astronaut" --steps 30 --width 768 --height 768
python scripts/test_txt2img.py --checkpoint "sd_xl_base_1.0"
```

ชี้ไปเครื่องอื่นได้ด้วย `--url` หรือ env `AI_SERVER_URL` (ดู `.env.example`)

> **กติกา debug กับพี่นาย:** ถ้า Frontend สร้างรูปไม่ได้ ให้รัน 2 สคริปต์นี้ก่อนเสมอ
> - ผ่านทั้งคู่ → ปัญหาอยู่ฝั่ง Backend/Frontend
> - ไม่ผ่าน → ปัญหาอยู่ฝั่ง AI Server (งานเรา)

---

## 5. API contract ที่ Backend ใช้

Backend (`backend/app.py`) เรียกแค่ 2 endpoint นี้ **ห้ามเปลี่ยนพอร์ต/ปิด `--api` โดยไม่แจ้ง**

### `GET /sdapi/v1/sd-models`
Backend map เป็น `GET /api/models` แล้วดึงเฉพาะฟิลด์ `model_name`

```json
[{ "title": "sd_xl_base_1.0.safetensors [31e35c80fc]",
   "model_name": "sd_xl_base_1.0",
   "hash": "31e35c80fc" }]
```

### `POST /sdapi/v1/txt2img`
Backend map เป็น `POST /api/generate` ส่ง payload หน้าตานี้ (timeout 300s):

```json
{
  "prompt": "...",
  "negative_prompt": "...",
  "steps": 20,
  "width": 1024,
  "height": 1024,
  "cfg_scale": 7,
  "sampler_name": "Euler a",
  "override_settings": { "sd_model_checkpoint": "<model_name>" }
}
```

ตอบกลับ:

```json
{ "images": ["<base64 ไม่มี data URI prefix>"], "info": "{...json string...}" }
```

> Backend เป็นคนเติม `data:image/png;base64,` เองก่อนส่งให้ Frontend — **AI Server ไม่ต้องเติม**

`override_settings` ทำให้ webui สลับ checkpoint ระหว่าง request
รูปแรกหลังสลับจะช้าขึ้น ~10–30s เพราะต้องโหลด model เข้า VRAM

---

## 6. แก้ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|---|---|---|
| Backend ตอบ `ไม่สามารถดึง Model จาก AI Server ได้` | webui ไม่ได้รัน / ผิดพอร์ต | `python scripts/check_server.py` |
| ต่อ `127.0.0.1:8088` ได้ แต่เครื่องอื่นไม่ได้ | ลืม `--listen` หรือ firewall ปิด | เติม `--listen` + เปิดพอร์ต 8088 ขาเข้า |
| HTTP 404 ที่ `/sdapi/v1/*` | ลืม `--api` | เติมใน `COMMANDLINE_ARGS` แล้ว restart |
| `Timeout` ที่ 300s | steps สูง / รูปใหญ่ / VRAM ไม่พอ | ลด steps หรือ 1024→512, เติม `--medvram` |
| `CUDA out of memory` | VRAM ไม่พอ | `--medvram` / `--lowvram`, ลดขนาดรูป |
| `Sampler not found` | ชื่อ sampler ไม่ตรง | ดูรายชื่อจริงจาก `check_server.py` |
| เพิ่ม checkpoint แล้วไม่ขึ้นใน dropdown | webui ยัง cache อยู่ | `POST /sdapi/v1/refresh-checkpoints` หรือ restart |

---

## 7. โครงสร้างโฟลเดอร์

```
Ai Server/
├── config/
│   ├── webui-user.sh       # ค่าตั้ง Linux
│   ├── webui-user.bat      # ค่าตั้ง Windows
│   └── README-config.md
├── scripts/
│   ├── check_server.py     # health check ก่อนแจ้งทีม
│   ├── test_txt2img.py     # ยิงสร้างรูปตรง ไม่ผ่าน Backend
│   └── requirements.txt
├── models/                 # checkpoint (ไฟล์จริงไม่ commit)
│   └── README.md
├── outputs/                # ผลทดสอบ (gitignore)
├── .env.example
├── .gitignore
└── README.md
```

---

## 8. ข้อตกลงกับทีม

- เปลี่ยน IP/พอร์ตของ AI Server → แจ้งพี่นายทันที (แก้ `AI_SERVER_IP` ใน `backend/.env`)
- เพิ่ม/ลบ checkpoint → แจ้งกร เพราะ dropdown หน้า Generate จะเปลี่ยน
- ไม่ commit ไฟล์ `.safetensors` / `.ckpt` เด็ดขาด (`.gitignore` กันไว้แล้ว)
- ก่อนเดโม ให้รัน `check_server.py` แล้วแคปผลส่งกลุ่ม
