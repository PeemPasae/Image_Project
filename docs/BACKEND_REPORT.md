# รายงานโครงสร้างและการทำงานของระบบ Backend (LUMA AI System)

---

## 1. ภาพรวมสถาปัตยกรรม (System Architecture Overview)

ระบบ Backend ของโปรเจกต์ LUMA พัฒนาด้วยภาษา **Python (Flask Framework)** ออกแบบตามหลักสถาปัตยกรรม **Application Factory Pattern** และแบ่งแยกโมดูลการทำงานด้วย **Flask Blueprints**

### แผนผังสถาปัตยกรรมระบบ (Architecture Diagram)
```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND (React / Vite)                           |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTP / JSON Requests
+-----------------------------------------------------------------------------------+
|                               NGINX REVERSE PROXY                                 |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ Port 5000
+-----------------------------------------------------------------------------------+
|                               FLASK BACKEND (run.py)                              |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |                       JWT AUTH MIDDLEWARE (@token_required)               |   |
|   +---------------------------------------------------------------------------+   |
|                                         │                                         |
|   +-------------------+-----------------+-------------------+-----------------+   |
|   │                   │                 │                   │                 │   |
|   ▼                   ▼                 ▼                   ▼                 ▼   |
| [auth_bp]         [sd_bp]          [history_bp]        [profile_bp]      [images] |
| /register         /generate        /history            /profile          /images  |
| /login            /estimate        /history/:id                                   |
|                   /models          (DELETE)                                       |
|                       │                                                           |
|                       ▼                                                           |
|               [services/ai_client.py]                                             |
|               - Concurrency GPU Lock (Mutex)                                      |
|               - Queue Counter & Time Estimation                                   |
+-----------------------------------------------------------------------------------+
             │                                                   │
             ▼                                                   ▼
+-----------------------------+                 +-----------------------------------+
|   SQLITE DATABASE           |                 |   STABLE DIFFUSION AI SERVER      |
|   (database/database.db)    |                 |   (Forge / WebUI API)             |
|   - users table             |                 |   - /sdapi/v1/txt2img             |
|   - generations table(BLOB) |                 |   - /sdapi/v1/sd-models           |
+-----------------------------+                 +-----------------------------------+
```

---

## 2. หน้าที่และความรับผิดชอบของแต่ละไฟล์ (File Breakdown)

### 2.1 โครงสร้างระดับ Root และการรันระบบ
* **`backend/run.py`**: จุดเริ่มต้นรันเซิร์ฟเวอร์ (Entry Point) ดึงค่าพอร์ตจาก Environment (`PORT=5000`) และเริ่มการทำงานของ Flask App บน Host `0.0.0.0`
* **`backend/config.py`**: ศูนย์กลางการตั้งค่า (Central Configuration) เช่น คีย์ลับ JWT Secret, อายุ Token (24 ชม.), รายการ CORS Origins ที่อนุญาต, และ URL ของ AI Server

### 2.2 แกนหลักของแอปพลิเคชัน (`backend/app/`)
* **`backend/app/__init__.py`**: 
  - สร้าง Application Instance ผ่าน `create_app()`
  - กำหนดค่าฐานข้อมูล SQLite ชี้ไปที่ `database/database.db`
  - ทำการลงทะเบียน Blueprints: `auth_bp`, `profile_bp`, `sd_bp`, `history_bp`
  - มีระบบ **Auto-Migration** ตรวจสอบโครงสร้างคอลัมน์ในตารางฐานข้อมูลและสร้างตารางอัตโนมัติเมื่อเริ่มระบบ
* **`backend/app/extensions.py`**: ประกาศตัวแปร `db = SQLAlchemy()` กลาง เพื่อให้ทุกโมดูลเรียกใช้งานได้โดยไม่เกิดปัญหา Circular Import

### 2.3 ฐานข้อมูลและโมเดล (`backend/app/models/`)
* **`backend/app/models/user.py`** (ตาราง `users`):
  - `id` (INTEGER PRIMARY KEY)
  - `email` (VARCHAR 255 UNIQUE INDEX)
  - `password_hash` (VARCHAR 255)
  - `created_at` (DATETIME)
  - ความสัมพันธ์แบบ Cascade Delete ไปยังตาราง `generations` (เมื่อลบ User ภาพทั้งหมดของ User นั้นจะถูกลบตามทันที)
* **`backend/app/models/generation.py`** (ตาราง `generations`):
  - รองรับประวัติ 2 หมวดหมู่:
    1. `category = 'sd_generate'`: สร้างจากโมเดล AI Checkpoint (Stable Diffusion)
    2. `category = 'image_filter'`: สร้างจากฟังก์ชันแต่งภาพย่อย (Sub-functions เช่น Canny, Blur)
  - เก็บพารามิเตอร์ Prompt, Negative Prompt, Steps, CFG Scale, Seed
  - `image_data` (BLOB / LargeBinary): จัดเก็บไฟล์ภาพไบนารีลงในฐานข้อมูลโดยตรง

### 2.4 ระบบความปลอดภัยและมิดเดิลแวร์ (`backend/app/middleware/`)
* **`backend/app/middleware/jwt_auth.py`**:
  - สร้าง Decorator `@token_required` ป้องกันเส้นทาง Protected Routes
  - ตรวจสอบความถูกต้องของ Header `Authorization: Bearer <token>`
  - ถอดรหัส JSON Web Token (HS256) และสกัด `request.user_id` ออกมา
  - ตรวจสอบอายุ Token (ไม่เกิน 24 ชั่วโมง) ป้องกันการสวมรอยข้ามบัญชี

### 2.5 เส้นทาง API (API Routes: `backend/app/routes/`)
* **`backend/app/routes/auth.py` (`auth_bp`)**:
  - `POST /api/v1/register`: ตรวจสอบความถูกต้องของอีเมล, รหัสผ่านขั้นต่ำ 8 ตัวอักษร, เช็กอีเมลซ้ำ (`EMAIL_EXISTS`), และแฮชรหัสผ่านก่อนบันทึก
  - `POST /api/v1/login`: ตรวจสอบรหัสผ่านกับค่า Hash และออก JWT Access Token
* **`backend/app/routes/sd.py` (`sd_bp`)**:
  - `GET /api/v1/models`: ดึงรายชื่อโมเดล Checkpoints จาก AI Server
  - `POST /api/v1/estimate`: คำนวณเวลาประเมินล่วงหน้าก่อนสร้างภาพ
  - `POST /api/v1/generate`: รับค่าพารามิเตอร์ -> ส่งเข้าคิว GPU -> สั่ง AI Server สร้างภาพ -> แปลงภาพเป็น Binary BLOB -> บันทึกลงตาราง `generations`
  - `GET /api/v1/images/<id>`: สตรีมไฟล์ภาพ PNG กลับไปแสดงผลบน Frontend พร้อมระบบตรวจสอบความเป็นเจ้าของภาพ (ป้องกัน IDOR)
* **`backend/app/routes/history.py` (`history_bp`)**:
  - `GET /api/v1/history`: ดึงรายการประวัติภาพของผู้ใช้ปัจจุบัน รองรับการแบ่งหน้า (Pagination) และการกรองแยกตามประเภทภาพ (`category`, `type`)
  - `GET /api/v1/history/<id>`: ดูรายละเอียดพารามิเตอร์ของภาพ
  - `DELETE /api/v1/history/<id>`: ลบภาพของตนเองออกจากระบบ
* **`backend/app/routes/profile.py` (`profile_bp`)**:
  - `GET /api/v1/profile`: ดึงข้อมูลโปรไฟล์ผู้ใช้ และสรุปสถิติจำนวนภาพที่สร้างแยกตามประเภท

### 2.6 บริการเชื่อมต่อ AI (`backend/app/services/`)
* **`backend/app/services/ai_client.py`**:
  - **ระบบจัดการคิวงานพร้อมกัน (Concurrency Queue)**: ใช้ `threading.Lock` ป้องกันคำขอชนกันเมื่อมีผู้ใช้สั่งเจนภาพพร้อมกันหลายคน โดยให้ GPU ประมวลผลทีละ 1 งานอย่างปลอดภัย
  - **ระบบประเมินเวลา (Time Estimation)**: คำนวณจากความละเอียดภาพ (Width x Height), จำนวน Steps, และจำนวนงานที่กำลังรอคิวอยู่ในระบบ
  - **ระบบ Timeout & Error Handling**: จำกัดเวลาประมวลผลสูงสุด 75 วินาที และรอคิวสูงสุด 120 วินาที

### 2.7 ยูทิลิตี้และมาตรฐานการตอบกลับ (`backend/app/utils/`)
* **`backend/app/utils/error_codes.py`**:
  - กำหนดฟังก์ชัน `success_response()` และ `error_response()`
  - กำหนดรหัสข้อผิดพลาด 12 รูปแบบตามสเปก LUMA เช่น `VALIDATION_ERROR`, `INVALID_CREDENTIALS`, `UNAUTHORIZED`, `EMAIL_EXISTS`, `GENERATION_NOT_FOUND`, `AI_SERVER_BUSY`

---

## 3. เจาะลึกกระบวนการทำงานและเส้นทางข้อมูล (Step-by-Step Data Flow)

### 3.1 ขั้นตอนการสมัครสมาชิก (Register Flow)
1. **Frontend**: ผู้ใช้กรอกอีเมลและรหัสผ่าน แล้วส่งคำขอแบบ `POST` ไปที่ `/api/v1/register`
   ```json
   {
     "email": "user@example.com",
     "password": "Password123"
   }
   ```
2. **Backend Validation**:
   - ตรวจสอบรูปแบบ Regex ของอีเมล
   - ตรวจสอบความยาวรหัสผ่าน (ต้อง >= 8 ตัวอักษร)
   - ค้นหาในตาราง `users` ว่ามีอีเมลนี้อยู่แล้วหรือไม่ หากซ้ำจะส่งกลับ `HTTP 409 EMAIL_EXISTS`
3. **Password Hashing & Save**:
   - แฮชรหัสผ่านด้วยอัลกอริทึม PBKDF2/SHA256 (`generate_password_hash`)
   - บันทึกผู้ใช้ใหม่ลงในฐานข้อมูล SQLite
4. **Response**: ส่งข้อมูลผู้ใช้กลับไปยัง Frontend ด้วยสถานะ `HTTP 201 Created`
   ```json
   {
     "success": true,
     "data": {
       "message": "Registration successful",
       "user": {
         "id": 1,
         "email": "user@example.com",
         "created_at": "2026-09-18T09:00:00"
       }
     }
   }
   ```

---

### 3.2 ขั้นตอนการเข้าสู่ระบบ (Login Flow)
1. **Frontend**: ส่งคำขอ `POST /api/v1/login` พร้อมอีเมลและรหัสผ่าน
2. **Backend Authentication**:
   - ดึงข้อมูลผู้ใช้จากตาราง `users` ด้วยอีเมล
   - นำรหัสผ่านที่ส่งมาไปเปรียบเทียบกับ Hash ในฐานข้อมูล (`check_password_hash`)
   - หากไม่ถูกต้อง ส่งกลับ `HTTP 401 INVALID_CREDENTIALS`
3. **JWT Generation**:
   - เข้ารหัส JWT Payload: `{"user_id": 1, "email": "user@example.com", "exp": <วันเวลาหมดอายุใน 24 ชม.>}`
   - เซ็นลายเซ็นดิจิทัลด้วยอัลกอริทึม HS256 และ Secret Key
4. **Response**: ส่ง Access Token ให้ Frontend บันทึกลงใน `localStorage`
   ```json
   {
     "success": true,
     "data": {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "Bearer",
       "expires_in": 86400,
       "user": {
         "id": 1,
         "email": "user@example.com"
       }
     }
   }
   ```

---

### 3.3 ขั้นตอนการสั่งสร้างรูปภาพด้วย AI (Image Generation Flow)
1. **Frontend**: ส่งคำขอ `POST /api/v1/generate` พร้อมแนบ Header `Authorization: Bearer <Token>`
   ```json
   {
     "prompt": "futuristic city skyline at sunset, 8k resolution",
     "negative_prompt": "blurry, low quality",
     "checkpoint": "v1-5-pruned-emaonly.safetensors",
     "sampler": "Euler a",
     "width": 512,
     "height": 512,
     "steps": 25,
     "cfg_scale": 7.5,
     "seed": -1
   }
   ```
2. **Middleware Auth**:
   - ตรวจสอบ JWT Token ถอดรหัสได้ `user_id = 1` และผูกไว้ใน `request.user_id`
3. **Concurrency Queue & AI Execution**:
   - เข้าคิว GPU Lock (`_gpu_lock.acquire()`) เพื่อความปลอดภัยของฮาร์ดแวร์
   - ส่งคำขอไปยัง AI Server API `POST /sdapi/v1/txt2img`
   - AI Server ประมวลผลและส่งผลลัพธ์ภาพกลับมาในรูปแบบ Base64 String
   - ปลดล็อกคิว (`_gpu_lock.release()`) เพื่อให้คำขอถัดไปเริ่มทำงาน
4. **Database Storage**:
   - ถอดรหัส Base64 เป็นข้อมูลไบนารี (Binary Bytes)
   - บันทึกลงในตาราง `generations` โดยระบุ `user_id = 1` และ `category = 'sd_generate'`
5. **Response**: ส่งผลลัพธ์ให้ Frontend พร้อม URL สำหรับเรียกดูภาพ
   ```json
   {
     "success": true,
     "data": {
       "generation_id": 105,
       "image_url": "/api/v1/images/105",
       "seed": 2847192847,
       "estimated_time_seconds": 3.75,
       "actual_time_seconds": 3.42,
       "created_at": "2026-09-18T09:15:20"
     }
   }
   ```

---

### 3.4 ขั้นตอนการสตรีมและป้องกันสิทธิ์รูปภาพ (Anti-Hopping & IDOR Protection)
1. เมื่อ Frontend ต้องการแสดงรูปภาพ จะยิงคำขอ `GET /api/v1/images/105` พร้อม JWT Token
2. Backend จะค้นหาภาพในตาราง `generations` ด้วยเงื่อนไข:
   ```sql
   SELECT image_data FROM generations WHERE id = 105 AND user_id = <user_id_จาก_Token>;
   ```
3. **ผลลัพธ์**:
   - หากเป็นเจ้าของภาพ: Backend ส่งข้อมูลภาพ Binary สตรีมกลับไปในรูปแบบ `image/png`
   - หากผู้ใช้คนอื่นพยายามแอบดู: ระบบจะไม่พบข้อมูลและตอบกลับ `HTTP 404 GENERATION_NOT_FOUND` ทันที

---

## 4. สรุปรายการ API Endpoints

| HTTP Method | API Path | จำเป็นต้องมี Token? | หน้าที่การทำงาน |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/register` | ❌ | สมัครสมาชิกผู้ใช้งานใหม่ |
| `POST` | `/api/v1/login` | ❌ | ตรวจสอบรหัสผ่านและรับ JWT Token |
| `GET` | `/api/v1/models` | ❌ | ดึงรายชื่อโมเดล AI Checkpoints |
| `POST` | `/api/v1/estimate` | ❌ | คำนวณเวลาโดยประมาณในการสร้างภาพ |
| `POST` | `/api/v1/generate` | 🔒 มี | สั่งสร้างรูปภาพ AI (ผูกกับเจ้าของบัญชี) |
| `GET` | `/api/v1/images/:id` | 🔒 มี | สตรีมไฟล์ภาพ PNG (จำกัดสิทธิ์เฉพาะเจ้าของ) |
| `GET` | `/api/v1/history` | 🔒 มี | ดึงประวัติการสร้างภาพ (รองรับ Pagination & Filter) |
| `GET` | `/api/v1/history/:id` | 🔒 มี | ดึงรายละเอียดพารามิเตอร์ของภาพ |
| `DELETE` | `/api/v1/history/:id` | 🔒 มี | ลบภาพประวัติของตนเอง |
| `GET` | `/api/v1/profile` | 🔒 มี | ดูข้อมูลโปรไฟล์และสถิติจำนวนภาพที่สร้าง |

---

## 5. มาตรฐานรหัสข้อผิดพลาด (Error Codes Reference)

| รหัสข้อผิดพลาด | HTTP Status | คำอธิบายสาเหตุ |
| :--- | :---: | :--- |
| `VALIDATION_ERROR` | `400` | ข้อมูลที่ส่งมาไม่ถูกต้องตามเงื่อนไข (เช่น อีเมลผิดรูปแบบ, ค่าตัวเลขเกินขอบเขต) |
| `INVALID_CREDENTIALS` | `401` | อีเมลหรือรหัสผ่านไม่ถูกต้อง |
| `UNAUTHORIZED` | `401` | ไม่ได้แนบ Token หรือ Token หมดอายุ / ลายเซ็นไม่ถูกต้อง |
| `EMAIL_EXISTS` | `409` | อีเมลนี้ถูกใช้สมัครไปแล้วในระบบ |
| `GENERATION_NOT_FOUND` | `404` | ไม่พบเรคคอร์ดภาพ หรือพยายามเข้าถึงภาพของผู้อื่น |
| `IMAGE_NOT_FOUND` | `404` | ไม่พบข้อมูลไบนารีของรูปภาพในฐานข้อมูล |
| `AI_SERVER_BUSY` | `409` | คิวงานบน AI Server แน่นเกินเวลาที่กำหนดให้รอได้ |
| `AI_SERVER_TIMEOUT` | `504` | AI Server ใช้เวลาประมวลผลนานเกิน 75 วินาที |
| `AI_SERVER_ERROR` | `503` | เกิดข้อผิดพลาดฝั่ง AI Server หรือไม่สามารถเชื่อมต่อเครือข่ายได้ |
| `INTERNAL_SERVER_ERROR` | `500` | เกิดข้อผิดพลาดที่ไม่คาดคิดภายในระบบเซิร์ฟเวอร์ Backend |
