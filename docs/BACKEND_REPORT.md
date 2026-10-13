# รายงานโครงสร้างและการทำงานของระบบ Backend (LUMA AI System)

---

## 1. ภาพรวมสถาปัตยกรรม (System Architecture Overview)

ระบบ Backend ของโปรเจกต์ LUMA พัฒนาด้วยภาษา **Python (Flask Framework)** ออกแบบตามหลักสถาปัตยกรรม **Application Factory Pattern** และแบ่งแยกโมดูลการทำงานด้วย **Flask Blueprints** เพื่อความเป็นระเบียบ ความปลอดภัย และความสามารถในการขยายระบบในอนาคต

ระบบทำหน้าที่เป็นศูนย์กลางประสานงานระหว่าง 3 ส่วนหลัก:
1. **Frontend Client (React / Vite)**: สื่อสารผ่าน REST API ภายใต้การควบคุมความปลอดภัยด้วย JSON Web Token (JWT Authentication)
2. **Stable Diffusion AI Server**: ประมวลผลโมเดลสร้างภาพขนาดใหญ่ ผ่านระบบจัดการคิวงานการ์ดจอ (Mutex Concurrency Lock)
3. **Edge Image Processing Services**: บริการประมวลผลภาพเฉพาะทางและปัญญาประดิษฐ์ตรวจจับท่าทาง (OpenCV & Google MediaPipe) ทำงานแบบ On-the-fly ภายในเซิร์ฟเวอร์ Backend *(ดูรายละเอียดเชิงลึกแยกต่างหากใน [IMAGE_PROCESSING_REPORT.md](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/docs/IMAGE_PROCESSING_REPORT.md))*

### แผนผังสถาปัตยกรรมระบบ (Architecture Diagram)
```
+-----------------------------------------------------------------------------------+
|                             FRONTEND (React / Vite)                               |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTP / JSON / Multipart Requests
+-----------------------------------------------------------------------------------+
|                               NGINX REVERSE PROXY                                 |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ Port 5000 (Host 0.0.0.0)
+---------------------------------------------------------------------------------------------------+
|                               FLASK BACKEND (run.py)                                              |
|                                                                                                   |
|   +-------------------------------------------------------------------------------------------+   |
|   |                       JWT AUTH MIDDLEWARE (@token_required, @admin_required)              |   |
|   +-------------------------------------------------------------------------------------------+   |
|                                         │                                                         |
|   +---------------+---------------+-----+---------+---------------+---------------+           |
|   │               │               │               │               │               │           |
|   ▼               ▼               ▼               ▼               ▼               ▼           |
| [auth_bp]       [sd_bp]      [history_bp]    [profile_bp]    [admin_bp]      [process_bp]     |
| /register       /generate    /history        /profile        /admin/users    /process/*       |
| /login          /estimate    /history/:id                    (GET & DELETE)  - spot-blur      |
|                 /models      (DELETE)                                        - gesture        |
|                 /images/:id                                                  - remove-bg      |
|                     │                                                        - cartoonize     |
|                     ▼                                                        - tilt-shift     |
|             [services/ai_client.py]                                          - hdr-enhancer   |
|             - Concurrency GPU Lock (Mutex)                                        │           |
|             - Queue Counter & Time Estimation                                     ▼           |
|             - SD WebUI / Forge REST Client                            [services/image_filters]|
|                                                                       (Pure Filter Algorithms)|
+---------------------------------------------------------------------------------------------------+
             │                                                   │
             ▼                                                   ▼
+-----------------------------+                 +-----------------------------------+
|   SQLITE DATABASE           |                 |   STABLE DIFFUSION AI SERVER      |
|   (database/database.db)    |                 |   (Forge / WebUI API)             |
|   - users table             |                 |   - /sdapi/v1/txt2img             |
|   - generations table(BLOB) |                 |   - /sdapi/v1/sd-models           |
|   - Auto Schema Migration   |                 +-----------------------------------+
+-----------------------------+
```

---

## 2. หน้าที่และความรับผิดชอบของแต่ละไฟล์ (File Breakdown)

### 2.1 โครงสร้างระดับ Root และการรันระบบ
* **[`backend/run.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/run.py)**: จุดเริ่มต้นรันเซิร์ฟเวอร์ (Entry Point) ดึงค่าพอร์ตจาก Environment (`PORT=5000`) ตรวจสอบไฟล์โมเดล AI ล่วงหน้า และเริ่มการทำงานของ Flask App บน Host `0.0.0.0`
* **[`backend/config.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/config.py)**: ศูนย์กลางการตั้งค่า (Central Configuration) เช่น คีย์ลับ `JWT_SECRET_KEY`, อายุ Token (24 ชม.), รายการ `CORS_ORIGINS` ที่อนุญาตสำหรับ Localhost และ LAN, รวมถึง URL ของ AI Server (`AI_SERVER_URL`)
* **[`backend/gunicorn_conf.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/gunicorn_conf.py)**: คอนฟิกูเรชันสำหรับ Production WSGI Server (Gunicorn) กำหนด `workers=1` และ `threads=8` เพื่อรักษา Threading Lock ของ GPU Queue ให้ทำงานได้ 100%

### 2.2 แกนหลักของแอปพลิเคชัน (`backend/app/`)
* **[`backend/app/__init__.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/__init__.py)**: 
  - สร้าง Application Instance ผ่านฟังก์ชัน `create_app()` ออกแบบตาม **Clean Application Factory Pattern**
  - กำหนดค่าฐานข้อมูล SQLite ชี้ไปที่ `database/database.db`
  - ตั้งค่า Centralized Logging และ CORS
  - ลงทะเบียน Blueprints ทั้งหมดผ่าน `register_routes(app)`
  - ให้บริการ `/health` และ `/api/v1/health` สำหรับ Health Check
  - ดักจับ `RequestEntityTooLarge` (413 Payload Too Large) ป้องกัน DoS
  - เรียกใช้ระบบ **Auto Schema Migration** ผ่าน `run_auto_migrations(db)`
* **[`backend/app/extensions.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/extensions.py)**: ประกาศตัวแปร `db = SQLAlchemy()` กลาง เพื่อให้ทุกโมดูลเรียกใช้งานได้โดยไม่เกิดปัญหา Circular Import

### 2.3 ฐานข้อมูลและโมเดล (`backend/app/models/`)
* **[`backend/app/models/user.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/models/user.py)** (ตาราง `users`):
  - `id` (INTEGER PRIMARY KEY)
  - `email` (VARCHAR 255 UNIQUE INDEX)
  - `password_hash` (VARCHAR 255)
  - `role` (VARCHAR 20, ค่าเริ่มต้น `user` หรือ `admin`)
  - `created_at` (DATETIME)
  - ความสัมพันธ์แบบ Cascade Delete ไปยังตาราง `generations` (เมื่อลบ User ประวัติและภาพทั้งหมดของ User นั้นจะถูกลบตามทันที)
* **[`backend/app/models/generation.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/models/generation.py)** (ตาราง `generations`):
  - `id` (INTEGER PRIMARY KEY)
  - `user_id` (INTEGER FOREIGN KEY เชื่อมกับ `users.id`)
  - `category` (VARCHAR 50, ค่าเริ่มต้น `sd_generate` สำหรับภาพที่สร้างจาก AI Checkpoint และ `image_filter` สำหรับฟังก์ชันแต่งภาพ)
  - `action_type` (VARCHAR 50, เช่น `txt2img`, `cartoonize`, `spot_blur`, `tilt_shift`, `hdr_enhancer`, `remove_bg`)
  - `prompt`, `negative_prompt`, `checkpoint`, `sampler`, `width`, `height`, `steps`, `cfg_scale`, `seed`
  - `params` (TEXT เก็บค่าพารามิเตอร์ทั้งหมดในรูปแบบ JSON String)
  - `source_image_id` (INTEGER อ้างอิงภาพต้นฉบับกรณีแต่งภาพต่อยอด)
  - `image_path` (VARCHAR 500 เส้นทางไฟล์ภาพบน Disk Storage เพื่อเร่งความเร็วในการอ่านข้อมูล)
  - `image_data` (BLOB / LargeBinary): จัดเก็บไฟล์ภาพไบนารีลงในฐานข้อมูลโดยตรง ป้องกันข้อผิดพลาดเรื่อง Path ข้ามเครื่องและรองรับความปลอดภัย
  - `created_at` (DATETIME สำหรับจัดเรียงประวัติล่าสุด)

### 2.4 ระบบความปลอดภัยและมิดเดิลแวร์ (`backend/app/middleware/`)
* **[`backend/app/middleware/jwt_auth.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/middleware/jwt_auth.py)**:
  - `@token_required`: ป้องกัน Protected Routes ตรวจสอบ Header `Authorization: Bearer <token>`, ตรวจสอบอายุ Token (24 ชม.), และสกัด `request.user_id`
  - `@admin_required`: ตรวจสอบสิทธิ์ระดับผู้ดูแลระบบ (`role == 'admin'`) สำหรับ Endpoint เฉพาะของ Admin

### 2.5 เส้นทาง API (API Routes: `backend/app/routes/`)
* **[`backend/app/routes/__init__.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/__init__.py)**: รวมศูนย์ฟังก์ชัน `register_routes(app)` ลงทะเบียน Blueprints ทั้งหมดและ URL Aliases ในจุดเดียว
* **[`backend/app/routes/auth.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/auth.py)** (`auth_bp`):
  - `POST /api/v1/register`: ตรวจสอบความถูกต้องของอีเมลด้วย Regex, รหัสผ่านขั้นต่ำ 8 ตัวอักษร, เช็กอีเมลซ้ำ (`EMAIL_EXISTS`), แฮชรหัสผ่านด้วย PBKDF2/SHA256
  - `POST /api/v1/login`: ตรวจสอบรหัสผ่านกับค่า Hash และออก JWT Access Token อายุ 24 ชั่วโมง
* **[`backend/app/routes/sd.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/sd.py)** (`sd_bp`):
  - `GET /api/v1/models`: ดึงรายชื่อโมเดล Checkpoints จาก Stable Diffusion AI Server
  - `POST /api/v1/estimate`: คำนวณเวลาประเมินล่วงหน้าก่อนสร้างภาพ
  - `POST /api/v1/generate`: รับค่าพารามิเตอร์ -> Validation -> เข้าคิว Mutex GPU Lock -> สั่ง AI Server สร้างภาพ -> จัดเก็บ BLOB และ Disk -> ส่งคืนสถานะ
  - `GET /api/v1/images/<id>`: สตรีมไฟล์ภาพ PNG กลับไปแสดงผลบน Frontend พร้อมระบบตรวจสอบความเป็นเจ้าของภาพ (Anti-Hopping / IDOR Protection)
* **[`backend/app/routes/history.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/history.py)** (`history_bp`):
  - `GET /api/v1/history`: ดึงรายการประวัติภาพของผู้ใช้ปัจจุบัน รองรับการแบ่งหน้า (Pagination) และการกรองตามหมวดหมู่ (`category`) หรือประเภท (`type`)
  - `GET /api/v1/history/<id>`: ดูรายละเอียดพารามิเตอร์ของภาพ (ป้องกัน IDOR)
  - `DELETE /api/v1/history/<id>`: ลบภาพของตนเองออกจากระบบ พร้อมลบไฟล์ดิสก์
* **[`backend/app/routes/profile.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/profile.py)** (`profile_bp`):
  - `GET /api/v1/profile`: ดึงข้อมูลโปรไฟล์ผู้ใช้ และสรุปสถิติจำนวนภาพที่สร้าง
* **[`backend/app/routes/admin.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/admin.py)** (`admin_bp`):
  - `GET /api/v1/admin/users`: ดึงรายชื่อผู้ใช้ทั้งหมดในระบบพร้อมสถิติการสร้างภาพ (Admin Only)
  - `DELETE /api/v1/admin/users/<id>`: ลบบัญชีผู้ใช้ ล้างข้อมูลประวัติและไฟล์ภาพทั้งหมด ป้องกัน Admin ลบบัญชีตนเอง
* **[`backend/app/routes/process.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/routes/process.py)** (`process_bp`):
  - รวมเส้นทาง API สำหรับ Image Processing ทั้งหมดภายใต้ `/api/v1/process/*`
  - `/process/spot-blur`: เบลอเฉพาะจุด
  - `/process/gesture`: จดจำท่าทางมือ
  - `/process/remove-bg`: ลบพื้นหลัง
  - `/process/cartoonize`: แปลงเป็นภาพการ์ตูน
  - `/process/tilt-shift`: จำลองโมเดลจิ๋ว
  - `/process/hdr-enhancer`: เพิ่มมิติและความคมชัดสไตล์ HDR

### 2.6 บริการเชื่อมต่อ AI (`backend/app/services/ai_client.py`)
* **[`backend/app/services/ai_client.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/services/ai_client.py)**:
  - **ระบบจัดการคิวงานพร้อมกัน (Concurrency Queue)**: ใช้ `threading.Lock` ป้องกันคำขอชนกันเมื่อมีผู้ใช้สั่งสร้างภาพพร้อมกันหลายคน โดยให้ GPU ประมวลผลทีละ 1 งานอย่างปลอดภัย ป้องกันปัญหา CUDA Out of Memory
  - **ระบบประเมินเวลา (Time Estimation)**: คำนวณจากความละเอียดภาพ (Width x Height), จำนวน Steps, และจำนวนงานที่กำลังรอคิวอยู่ในระบบ
  - **ระบบ Timeout & Error Handling**: จำกัดเวลาประมวลผลสูงสุด 75 วินาที และเวลารอคิวสูงสุด 40 วินาที เพื่อตอบกลับก่อนที่ Reverse Proxy จะตัดการเชื่อมต่อ

### 2.7 บริการประมวลผลภาพคอมพิวเตอร์วิทัศน์ (`backend/app/services/image_filters/`)
* **Pure Filter Algorithms**: อัลกอริทึมประมวลผลภาพถูกจัดให้อยู่ในรูปแบบ Pure Python Functions ที่รับและคืนค่า `np.ndarray` โดยไม่มีความผูกพันกับ Flask HTTP Request:
  - `spot_blur.py`: อัลกอริทึม Gaussian Blur + Soft Masking
  - `cartoonize.py`: อัลกอริทึม Bilateral Filter + K-Means Color Quantization + Adaptive Edge
  - `tilt_shift.py`: อัลกอริทึม Progressive Smoothstep Depth Map + Color Saturation Boost
  - `hdr_enhancer.py`: อัลกอริทึม Gray World White Balance + CLAHE บน L-channel + Multi-scale Unsharp Mask
  - `remove_bg.py`: อัลกอริทึม MediaPipe Segmentation + Interactive GrabCut
  - `gesture.py`: อัลกอริทึม MediaPipe Gesture Recognizer พร้อม Auto-download และ Model Caching

### 2.8 ยูทิลิตี้และระบบสนับสนุน (`backend/app/utils/`)
* **[`backend/app/utils/error_codes.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/utils/error_codes.py)**: ฟังก์ชันสร้าง Envelope Response (`success_response()`, `error_response()`) และค่าคงที่ Error Codes มาตรฐานทั้งหมด
* **[`backend/app/utils/image_helpers.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/utils/image_helpers.py)**: ฟังก์ชันตัวช่วยตรวจสอบไฟล์ภาพ (`extract_uploaded_image`) ตรวจนามสกุล แปลงเป็น OpenCV Matrix และสตรีมภาพ PNG (`send_image_png`) ลดความซ้ำซ้อนของโค้ด
* **[`backend/app/utils/db_migrations.py`](file:///c:/Uni_Work%27/3_1/Img_pro_code/Main/Image_Project/backend/app/utils/db_migrations.py)**: ฟังก์ชัน `run_auto_migrations(db)` ตรวจสอบโครงสร้างตารางและรัน `ALTER TABLE` เพิ่มคอลัมน์ใหม่อัตโนมัติเมื่อเริ่มแอป

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
   - ค้นหาในตาราง `users` ด้วยคำสั่ง `User.query.filter_by(email=email).first()` หากพบว่ามีอยู่แล้ว จะตอบกลับ `HTTP 409 EMAIL_EXISTS`
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
2. **Middleware Auth & Validation**:
   - ตรวจสอบ JWT Token ถอดรหัสได้ `user_id` ผูกไว้ใน `request.user_id`
   - ตรวจสอบพารามิเตอร์: Prompt ไม่เกิน 2000 ตัวอักษร, Width/Height เป็น 512/768/1024, Steps อยู่ระหว่าง 1-50, CFG Scale อยู่ระหว่าง 1.0-20.0
3. **Concurrency Queue & AI Execution**:
   - เข้าคิว GPU Lock (`_gpu_lock.acquire()`) เพื่อความปลอดภัยของฮาร์ดแวร์ ป้องกันคำขอชนกัน
   - ส่งคำขอไปยัง Stable Diffusion WebUI API `POST /sdapi/v1/txt2img`
   - AI Server ประมวลผลและส่งผลลัพธ์ภาพกลับมาในรูปแบบ Base64 String
   - ปลดล็อกคิว (`_gpu_lock.release()`) ทันทีเพื่อให้คำขอถัดไปเริ่มทำงาน
4. **Database Storage**:
   - ถอดรหัส Base64 เป็นข้อมูลไบนารี (Binary Bytes)
   - บันทึกลงในตาราง `generations` โดยระบุ `user_id = request.user_id`, `category = 'sd_generate'`, `action_type = 'txt2img'`
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
1. เมื่อ Frontend ต้องการแสดงรูปภาพ จะส่งคำขอ `GET /api/v1/images/105` พร้อม JWT Token
2. Backend จะค้นหาภาพในตาราง `generations` ด้วยเงื่อนไขคู่:
   ```sql
   SELECT image_data FROM generations WHERE id = 105 AND user_id = :current_user_id;
   ```
3. **ผลลัพธ์**:
   - **หากเป็นเจ้าของภาพ**: Backend ส่งข้อมูลภาพ Binary สตรีมกลับไปในรูปแบบ `image/png` ด้วย `send_file(BytesIO(image_data), mimetype="image/png")`
   - **หากผู้ใช้คนอื่นพยายามแอบดู (IDOR Attack)**: ระบบจะไม่พบข้อมูลเนื่องจาก `user_id` ไม่ตรงกัน และตอบกลับ `HTTP 404 GENERATION_NOT_FOUND` ทันที โดยไม่เปิดเผยว่ามีรูปภาพ ID นี้อยู่จริงหรือไม่

---

### 3.5 ขั้นตอนการประมวลผลภาพบน Edge Service (Edge Image Processing Flow)
1. Frontend ส่งรูปภาพแบบ `multipart/form-data` พร้อม Header `Authorization: Bearer <Token>` ไปยัง Endpoint ใต้ `/api/v1/process/*`
2. มิดเดิลแวร์ `@token_required` ตรวจสอบสิทธิ์ผู้ใช้
3. Route ตรวจสอบนามสกุลไฟล์ (.jpg, .jpeg, .png, .webp) และถอดรหัสเป็น OpenCV BGR Matrix ด้วย `cv2.imdecode`
4. ประมวลผลบนเซิร์ฟเวอร์ Backend ทันทีผ่าน OpenCV หรือ MediaPipe โดยไม่ต้องส่งต่อไปยัง GPU AI Server
5. ส่งผลลัพธ์กลับไปยังผู้ใช้เป็นสตรีมไฟล์ภาพ PNG (`image/png`) หรือผลลัพธ์ JSON

---

## 4. สรุปรายการ API Endpoints ทั้งหมดในระบบ

| หมวดหมู่ | HTTP Method | API Path | จำเป็นต้องมี Token? | หน้าที่การทำงาน |
| :--- | :---: | :--- | :---: | :--- |
| **System** | `GET` | `/health` หรือ `/api/v1/health` | ❌ ไม่ต้องมี | ตรวจสอบสถานะการเชื่อมต่อเซิร์ฟเวอร์และ AI Server |
| **Authentication** | `POST` | `/api/v1/register` | ❌ ไม่ต้องมี | สมัครสมาชิกผู้ใช้งานใหม่ (ตรวจอีเมลซ้ำ, แฮชรหัสผ่าน) |
| **Authentication** | `POST` | `/api/v1/login` | ❌ ไม่ต้องมี | ตรวจสอบรหัสผ่านและรับ JWT Access Token |
| **Stable Diffusion** | `GET` | `/api/v1/models` | ❌ ไม่ต้องมี | ดึงรายชื่อโมเดล AI Checkpoints ทั้งหมดจาก AI Server |
| **Stable Diffusion** | `POST` | `/api/v1/estimate` | ❌ ไม่ต้องมี | คำนวณเวลาประเมินล่วงหน้าในการสร้างภาพตามขนาดและ Steps |
| **Stable Diffusion** | `POST` | `/api/v1/generate` | 🔒 มี Token | สั่งสร้างรูปภาพ AI พร้อมระบบคิว Concurrency GPU Lock |
| **Image Delivery** | `GET` | `/api/v1/images/:id` | 🔒 มี Token | สตรีมไฟล์ภาพ PNG (จำกัดสิทธิ์เฉพาะเจ้าของ ป้องกัน IDOR) |
| **History** | `GET` | `/api/v1/history` | 🔒 มี Token | ดึงประวัติการสร้างภาพ (รองรับ Pagination, Category & Type Filter) |
| **History** | `GET` | `/api/v1/history/:id` | 🔒 มี Token | ดึงรายละเอียดพารามิเตอร์ของภาพแบบเจาะลึก |
| **History** | `DELETE` | `/api/v1/history/:id` | 🔒 มี Token | ลบภาพประวัติของตนเอง พร้อมล้างไฟล์ภาพบนดิสก์ |
| **Profile** | `GET` | `/api/v1/profile` | 🔒 มี Token | ดูข้อมูลโปรไฟล์และสรุปสถิติจำนวนภาพที่สร้างทั้งหมด |
| **Admin** | `GET` | `/api/v1/admin/users` | 👑 Admin Only | ดึงรายชื่อผู้ใช้ทั้งหมดในระบบพร้อมสถิติภาพของแต่ละคน |
| **Admin** | `DELETE` | `/api/v1/admin/users/:id` | 👑 Admin Only | ลบบัญชีผู้ใช้ พร้อมล้างประวัติและไฟล์ภาพทั้งหมด |
| **Image Processing** | `POST` | `/api/v1/process/spot-blur` | 🔒 มี Token | เบลอเฉพาะจุดตามตำแหน่งพิกัดวงกลมที่ระบุ |
| **Image Processing** | `POST` | `/api/v1/process/gesture` | 🔒 มี Token | ตรวจจับและจดจำท่าทางมือจากรูปภาพนิ่ง |
| **Image Processing** | `POST` | `/api/v1/process/remove-bg` | 🔒 มี Token | ลบพื้นหลังภาพบุคคล (AI / GrabCut / แปรงเก็บ-ลบ) |
| **Image Processing** | `POST` | `/api/v1/process/cartoonize` | 🔒 มี Token | แปลงรูปภาพเป็นสไตล์การ์ตูน/อนิเมะ (Bilateral + K-Means + Edge) |
| **Image Processing** | `POST` | `/api/v1/process/tilt-shift` | 🔒 มี Token | จำลองเอฟเฟกต์ภาพถ่ายโมเดลจำลอง (Tilt-Shift Miniature) |
| **Image Processing** | `POST` | `/api/v1/process/hdr-enhancer` | 🔒 มี Token | เพิ่มมิติและความคมชัดสไตล์ HDR (CLAHE + Detail Enhance) |

---

## 5. มาตรฐานรหัสข้อผิดพลาด (Standard Error Codes)

ระบบ LUMA กำหนดรหัสข้อผิดพลาดที่เป็นทางการ 14 รูปแบบ เพื่อให้ Frontend จัดการแสดงผลได้อย่างแม่นยำ:

| รหัสข้อผิดพลาด | HTTP Status | คำอธิบายสาเหตุ |
| :--- | :---: | :--- |
| `VALIDATION_ERROR` | `400` | ข้อมูลที่ส่งมาไม่ถูกต้องตามเงื่อนไข (เช่น อีเมลผิดรูปแบบ, ค่าพารามิเตอร์เกินขอบเขต) |
| `INVALID_CREDENTIALS` | `401` | อีเมลหรือรหัสผ่านไม่ถูกต้อง |
| `UNAUTHORIZED` | `401` | ไม่ได้แนบ Token หรือ Token หมดอายุ / ลายเซ็นไม่ถูกต้อง |
| `EMAIL_EXISTS` | `409` | อีเมลนี้ถูกใช้สมัครไปแล้วในระบบ |
| `GENERATION_NOT_FOUND` | `404` | ไม่พบเรคคอร์ดภาพ หรือพยายามเข้าถึงภาพของผู้อื่น |
| `IMAGE_NOT_FOUND` | `404` | ไม่พบข้อมูลไบนารีของรูปภาพในฐานข้อมูล |
| `INVALID_IMAGE` | `400` | ไฟล์รูปภาพเสียหาย ไม่สามารถถอดรหัสด้วย OpenCV ได้ |
| `UNSUPPORTED_FILE_TYPE` | `415` | นามสกุลไฟล์ไม่รองรับ (รองรับเฉพาะ .jpg, .jpeg, .png, .webp) |
| `MODEL_UNAVAILABLE` | `503` | ไฟล์โมเดล AI ในระบบไม่พร้อมใช้งาน หรือดาวน์โหลดไม่สำเร็จ |
| `GENERATION_FAILED` | `500` | การประมวลผลคำนวณภาพขัดข้อง |
| `AI_SERVER_BUSY` | `409` | คิวงานบน AI Server แน่นเกินเวลาที่กำหนดให้รอได้ (เกิน 120 วินาที) |
| `AI_SERVER_TIMEOUT` | `504` | AI Server ใช้เวลาประมวลผลนานเกิน 75 วินาที |
| `AI_SERVER_ERROR` | `503` | เกิดข้อผิดพลาดฝั่ง AI Server หรือไม่สามารถเชื่อมต่อเครือข่ายได้ |
| `INTERNAL_SERVER_ERROR` | `500` | เกิดข้อผิดพลาดที่ไม่คาดคิดภายในระบบเซิร์ฟเวอร์ Backend |

---

## 6. แนวทางการตอบคำถามสำหรับการสอบพรีเซนต์ (Defense Q&A Cheat Sheet)

#### Q1: "ทำไมถึงเลือกเก็บรูปภาพเป็น BLOB ใน SQLite ทำไมไม่เซฟเป็นไฟล์ลงในโฟลเดอร์ปกติ (Disk Storage)?"
* **แนวทางการตอบ:**  
  *"การจัดเก็บเป็น BLOB ในฐานข้อมูลมีข้อดีหลัก 3 ประการสำหรับระบบนี้ครับ:  
  1. **ความง่ายในการพอร์ตและสำรองระบบ (Portability):** ข้อมูลรูปภาพทั้งหมดผูกรวมอยู่ในฐานข้อมูลไฟล์เดียว `database.db` สามารถย้ายไปรันบนเครื่องเซิร์ฟเวอร์อื่นได้ทันทีโดยไม่ต้องกังวลเรื่อง Relative Path เสียหาย  
  2. **ความสอดคล้องของข้อมูล (Transaction Consistency & Cascade):** เมื่อผู้ใช้ลบบัญชีหรือลบประวัติ ระบบจะ Cascade Delete ข้อมูลภาพออกจากฐานข้อมูลทันที ไม่มีปัญหาไฟล์ภาพขยะตกค้างบนดิสก์  
  3. **ความปลอดภัยในการควบคุมสิทธิ์ (Access Control):** ป้องกันไม่ให้ใครเปิดดูภาพได้โดยตรงผ่าน Web Server Static Link ทุกการร้องขอรูปภาพต้องผ่านมิดเดิลแวร์ `@token_required` ตรวจสอบสิทธิ์ความเป็นเจ้าของก่อนเสมอครับ"*

#### Q2: "ถ้ามีคนกดสั่งสร้างภาพ AI พร้อมกันหลายคน ระบบจะไม่ล่มเหรอ?"
* **แนวทางการตอบ:**  
  *"ไม่ล่มครับ เพราะเราวางระบบ **Concurrency Queue** โดยใช้ **`threading.Lock()` (Mutex Lock)** ไว้ใน `services/ai_client.py`:  
  * คำขอแรกจะได้สิทธิ์เข้าใช้งาน GPU ทันที ส่วนคำขอถัดมาจะเข้าสู่คิวรออย่างเป็นระเบียบ  
  * การ์ดจอ GPU จะประมวลผลทีละ 1 งานอย่างปลอดภัย จึงไม่เกิดปัญหาหน่วยความจำเต็ม (**CUDA Out of Memory**)  
  * และเรามีระบบคำนวณเวลารอคิวส่งกลับไปให้หน้าเว็บ ทำให้ผู้ใช้เห็นสถานะนับถอยหลังอย่างชัดเจน ไม่สับสนครับ"*

#### Q3: "ระบบป้องกันไม่ให้คนอื่นแอบดูรูปภาพของเรายังไง (IDOR Protection)?"
* **แนวทางการตอบ:**  
  *"เราป้องกันด้วยเทคนิค **Anti-Hopping / IDOR Check** ครับ โดยใน Endpoint `GET /api/v1/images/<id>` มิดเดิลแวร์ `@token_required` จะถอดรหัส `user_id` ของคนที่ล็อกอินอยู่เสมอ จากนั้นคำสั่ง SQL จะค้นหาด้วยเงื่อนไขคู่:  
  `WHERE id = :id AND user_id = request.user_id`  
  ดังนั้น ต่อให้มีคนพยายามเดาสุ่มเลขรูปภาพของผู้อื่น ระบบจะหาไม่พบและตอบกลับ `404 Not Found` ทันทีครับ"*

#### Q4: "ทำไมถึงแยกโมดูลประมวลผลภาพ (Image Processing) ออกจาก AI Server?"
* **แนวทางการตอบ:**  
  *"เพราะฟังก์ชันอย่าง Spot Blur, Gesture Recognition และ Background Removal เป็นงานประมวลผลแบบเฉพาะทางที่สามารถรันบน CPU ของเครื่องเซิร์ฟเวอร์ Backend ได้อย่างรวดเร็วระดับมิลลิวินาทีด้วย OpenCV และ MediaPipe ครับ การแยกออกมาทำให้ผู้ใช้งานไม่ต้องไปรอต่อคิว GPU ของ Stable Diffusion ที่กินเวลานาน และช่วยลดภาระงานของการ์ดจอหลักได้มหาศาลครับ"*
