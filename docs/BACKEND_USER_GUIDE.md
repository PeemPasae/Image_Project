# คู่มือการติดตั้งและใช้งานระบบ Backend (Backend User & Developer Guide)

คู่มือฉบับนี้อธิบายขั้นตอนการติดตั้ง, การกำหนดค่าสภาพแวดล้อม (Configuration), การรันเซิร์ฟเวอร์, การรันชุดทดสอบ (Automated Tests), และเอกสารอ้างอิง API Endpoints ทั้งหมดของระบบ **LUMA Backend**

---

## 1. ความต้องการของระบบ (Prerequisites)

- **ระบบปฏิบัติการ:** Windows 10/11 หรือ Linux (Ubuntu 20.04/22.04 LTS)
- **ภาษา:** Python 3.10 หรือ Python 3.11 (แนะนำ 3.11.9)
- **เครื่องมือจัดการแพ็กเกจ:** `pip`
- **ระบบฐานข้อมูล:** SQLite 3 (ติดตั้งมาพร้อมกับ Python)
- **AI Server:** Stable Diffusion WebUI / Forge API (กรณีใช้งานสร้างภาพ AI)

---

## 2. ขั้นตอนการติดตั้ง (Installation)

### 2.1 เข้าสู่โฟลเดอร์โปรเจกต์
เปิด PowerShell หรือ Command Prompt แล้วไปยังโฟลเดอร์โปรเจกต์:
```powershell
cd "c:\Uni_Work'\3_1\Img_pro_code\Main\Image_Project\backend"
```

### 2.2 สร้างและเปิดใช้งาน Virtual Environment (แนะนำ)
```powershell
# สร้าง virtual environment ชื่อ .venv
python -m venv .venv

# เปิดใช้งานบน Windows
.venv\Scripts\activate

# (หรือบน Linux / macOS)
# source .venv/bin/activate
```

### 2.3 ติดตั้ง Dependencies ทั้งหมด
ติดตั้งแพ็กเกจที่จำเป็นจากไฟล์ [`requirements.txt`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/requirements.txt):
```powershell
pip install -r requirements.txt
```

---

## 3. การกำหนดค่าสภาพแวดล้อม (Environment Configuration)

คัดลอกไฟล์แม่แบบ [`.env.example`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/.env.example) ไปเป็น [`.env`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/.env):
```powershell
cp .env.example .env
```

แก้ไขค่าตัวแปรในไฟล์ `.env` ตามความเหมาะสม:
```ini
# โฮสต์และพอร์ตของ Backend
HOST=0.0.0.0
PORT=5000
FLASK_DEBUG=false

# รหัสลับสำหรับเข้ารหัสและถอดรหัส JWT Token (ควรตั้งให้คาดเดายาก)
JWT_SECRET_KEY=luma_super_secret_jwt_key_2026

# ที่อยู่ IP และพอร์ตของ AI GPU Server (Stable Diffusion WebUI / Forge)
AI_SERVER_URL=http://172.20.57.0:8088

# โฟลเดอร์สำหรับจัดเก็บไฟล์ภาพ (Disk-Backed Storage)
UPLOAD_FOLDER=uploads

# ระดับการบันทึก Log (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## 4. การเตรียมโมเดล AI ล่วงหน้า (Pre-download AI Models)

เพื่อป้องกันปัญหา Cold Start หรือ Request Timeout ขณะที่ผู้ใช้เริ่มใช้งาน ให้รันสคริปต์ดาวน์โหลดโมเดล MediaPipe ล่วงหน้า:
```powershell
python scripts/download_models.py
```
สคริปต์จะตรวจสอบความสมบูรณ์ของไฟล์และดาวน์โหลด:
1. `models/selfie_multiclass_256x256.tflite` (~16 MB)
2. `models/gesture_recognizer.task` (~8 MB)

---

## 5. การเริ่มต้นฐานข้อมูล (Database Initialization)

ระบบ Backend มีระบบ **Auto-Migration** ที่จะสร้างตารางและอัปเดตโครงสร้างคอลัมน์ใน `database/database.db` ให้อัตโนมัติเมื่อสตาร์ทเซิร์ฟเวอร์ครั้งแรก

หากต้องการสร้างฐานข้อมูลด้วยสคริปต์ล่วงหน้า สามารถรันคำสั่ง:
```powershell
python ../database/init_db.py
```

หากต้องการล้างข้อมูลทั้งหมดในฐานข้อมูลเพื่อเริ่มต้นใหม่:
```powershell
python ../database/clear.py
```

---

## 6. การเริ่มรันเซิร์ฟเวอร์ (Starting the Server)

### 6.1 รันสำหรับ Development:
```powershell
python run.py
```

ผลลัพธ์บนคอนโซลจะแสดงดังนี้:
```text
======================================================================
[*] LUMA Backend API Server is running on: http://0.0.0.0:5000
[*] Debug Mode:       OFF (Production / Behind Proxy)
[*] Local Access:     http://127.0.0.1:5000/api/v1
[*] Health Check:     http://127.0.0.1:5000/api/v1/health
[*] Disk Storage:     backend/uploads
[*] AI Models Status: [READY] All models present
[*] Network Access:   Ready to receive requests from Nginx Gateway (0.0.0.0:5000)
======================================================================
```

### 6.2 รันสำหรับ Production (Gunicorn on Linux / Docker):
```bash
gunicorn -c gunicorn_conf.py run:app
```
> **คำแนะนำด้านสถาปัตยกรรม:** คอนฟิกูเรชันกำหนด `workers = 1` และ `threads = 8` เพื่อรักษาความปลอดภัยของ Mutex Lock บน GPU ให้ทำงานร่วมกันได้อย่างสมบูรณ์

---

## 7. การรันชุดทดสอบอัตโนมัติ (Automated Testing)

รันชุดทดสอบครอบคลุมทุกระบบด้วย `pytest`:
```powershell
# รันชุดทดสอบทั้งหมดภายในโฟลเดอร์ backend
python -m pytest tests -v
```

ผลการทดสอบที่คาดหวัง:
```text
tests/test_backend_full.py::test_register_and_duplicate_check PASSED
tests/test_backend_full.py::test_login_and_jwt PASSED
tests/test_backend_full.py::test_user_isolation_and_idor_protection PASSED
tests/test_backend_full.py::test_history_pagination PASSED
tests/test_backend_full.py::test_concurrent_generation_simulation PASSED
tests/test_backend_full.py::test_generate_string_parameters_and_type_coercion PASSED
tests/test_backend_full.py::test_generation_type_display_name PASSED
tests/test_backend_full.py::test_get_profile_contract PASSED
tests/test_backend_full.py::test_health_check_endpoint PASSED
tests/test_backend_full.py::test_disk_storage_and_streaming PASSED
tests/test_image_filters_suite.py::test_cartoonize_algorithm PASSED
tests/test_image_filters_suite.py::test_spot_blur_algorithm PASSED
tests/test_image_filters_suite.py::test_cartoonize_upload_endpoint PASSED

============================= 13 passed in 4.77s =============================
```

---

## 8. เอกสารอ้างอิง API (API Reference)

Base URL ของระบบ: `http://localhost:5000/api/v1`

### 8.0 ตรวจสอบสถานะระบบ (Health Check)
- **Method:** `GET`
- **Path:** `/health`
- **การตอบกลับ:**
  ```json
  {
    "success": true,
    "data": {
      "status": "healthy",
      "database": "connected",
      "ai_server_url": "http://172.20.57.0:8088"
    }
  }
  ```

### 8.1 ระบบสมาชิก (Authentication)

#### 1. สมัครสมาชิก
- **Method:** `POST`
- **Path:** `/register`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "message": "Registration successful",
      "user": {
        "id": 1,
        "email": "user@example.com",
        "created_at": "2026-10-02T09:00:00"
      }
    }
  }
  ```

#### 2. เข้าสู่ระบบ
- **Method:** `POST`
- **Path:** `/login`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 86400,
      "user": {
        "id": 1,
        "email": "user@example.com",
        "created_at": "2026-10-02T09:00:00"
      }
    }
  }
  ```

---

### 7.2 ระบบสร้างภาพ AI (Stable Diffusion)

ทุก Endpoint ในส่วนนี้ต้องแนบ Header: `Authorization: Bearer <access_token>`

#### 1. ดึงรายชื่อโมเดล Checkpoints
- **Method:** `GET`
- **Path:** `/models`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "models": [
        { "title": "v1-5-pruned-emaonly.safetensors", "model_name": "v1-5-pruned-emaonly" }
      ]
    }
  }
  ```

#### 2. สั่งสร้างรูปภาพ (Text-to-Image)
- **Method:** `POST`
- **Path:** `/generate`
- **Request Body:**
  ```json
  {
    "prompt": "A futuristic glowing cybernetic city at night, 8k",
    "negative_prompt": "blurry, low quality",
    "checkpoint": "v1-5-pruned-emaonly",
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7.0,
    "sampler": "Euler a",
    "seed": -1
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "generation_id": 105,
      "image_url": "/api/v1/images/105",
      "seed": 128492019,
      "created_at": "2026-10-02T09:15:00"
    }
  }
  ```

#### 3. สตรีมไฟล์รูปภาพ (Binary Stream)
- **Method:** `GET`
- **Path:** `/images/:id`
- **Response (200 OK):** ข้อมูลไบนารีของรูปภาพ `Content-Type: image/png`

---

### 7.3 ระบบประวัติและโปรไฟล์ (History & Profile)

#### 1. ดึงรายการประวัติ (Pagination)
- **Method:** `GET`
- **Path:** `/history?page=1&limit=20`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "history": [
        {
          "id": 105,
          "prompt": "A futuristic city",
          "negative_prompt": "blurry",
          "checkpoint": "v1-5-pruned-emaonly",
          "sampler": "Euler a",
          "width": 512,
          "height": 512,
          "steps": 20,
          "cfg_scale": 7.0,
          "seed": 128492019,
          "image_url": "/api/v1/images/105",
          "created_at": "2026-10-02T09:15:00"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 1,
        "total_pages": 1
      }
    }
  }
  ```

#### 2. ดึงรายละเอียดภาพเดี่ยว
- **Method:** `GET`
- **Path:** `/history/:id`
- **Response (200 OK):** ข้อมูลของภาพตาม ID

#### 3. ลบภาพออกจากระบบ
- **Method:** `DELETE`
- **Path:** `/history/:id`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "message": "Generation deleted successfully"
    }
  }
  ```

#### 4. ดึงข้อมูลโปรไฟล์ผู้ใช้
- **Method:** `GET`
- **Path:** `/profile`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "email": "user@example.com",
      "created_at": "2026-10-02T09:00:00",
      "generation_count": 1
    }
  }
  ```

---

### 7.4 ระบบประมวลผลแต่งรูปภาพ (Image Processing Tools)

ทุก Endpoint รับข้อมูลแบบ `multipart/form-data`:

| Endpoint | พารามิเตอร์สำคัญ | ผลลัพธ์ตอบกลับ |
|---|---|---|
| `POST /process/spot-blur` | `image` (file), `circles` (JSON string `[[x,y,r]]`), `strength` (1-30), `soft` ("true"/"false") | Binary PNG |
| `POST /process/cartoonize` | `image` (file), `num_colors` (2-32), `line_thickness` (1-5), `smoothness` (1-10) | Binary PNG |
| `POST /process/tilt-shift` | `image` (file), `focus_position` (0.0-1.0), `focus_width` (0.05-0.8), `blur_strength` (1-30), `saturation_boost` (1.0-2.5), `contrast_boost` (1.0-2.0) | Binary PNG |
| `POST /process/hdr-enhancer` | `image` (file), `clahe_clip_limit` (1.0-5.0), `clahe_grid_size` (2-16), `detail_strength` (0.0-3.0), `color_balance` ("true"/"false") | Binary PNG |
| `POST /process/gesture` | `image` (file), `num_hands` (1-4), `min_confidence` (0.1-1.0) | JSON Gesture Result |
| `POST /process/remove-bg` | `image` (file), `use_ai` ("true"/"false"), `bg` ("transparent" หรือ "#HEX"), `rect` (JSON `[x,y,w,h]`), `strokes` (JSON `[{type, r, points}]`) | Binary PNG |

---

## 8. วิธีเปิดใช้งานฟังก์ชันสำรอง (Re-enabling Disabled Features)

หากต้องการนำฟังก์ชันที่คอมเมนต์ `#` ไว้ด้านล่างไฟล์กลับมาใช้งาน:

1. **เปิดใช้งานการประมาณเวลา (`/estimate`):**
   - ไปที่ท้ายไฟล์ [`backend/app/routes/sd.py`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/sd.py)
   - ลบเครื่องหมาย `#` ออกจากฟังก์ชัน `estimate_time()`
2. **เปิดใช้งานการสตรีมเว็บแคมสำหรับ Gesture:**
   - ไปที่ท้ายไฟล์ [`backend/app/services/image_filters/gesture.py`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/app/services/image_filters/gesture.py) ลบ `#` ออกจากโค้ดโหมด VIDEO
   - ไปที่ท้ายไฟล์ [`backend/app/services/image_filters/routes.py`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/app/services/image_filters/routes.py) ลบ `#` ออกจาก `/process/gesture/frame` และ `/process/gesture/stop`
