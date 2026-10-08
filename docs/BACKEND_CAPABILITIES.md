# ความสามารถและการทำงานของระบบ Backend (Backend Capabilities & Features)

เอกสารฉบับนี้อธิบายฟีเจอร์, ฟังก์ชันการทำงาน, และความสามารถทั้งหมดของระบบ **LUMA Backend** โดยละเอียด ซึ่งครอบคลุมทั้งระบบสมาชิก, ปัญญาประดิษฐ์สร้างภาพ (Generative AI), ระบบตกแต่งภาพด้วย Computer Vision, และการจัดการข้อมูล

---

## สารบัญความสามารถ (Capabilities Index)

1. [ระบบความปลอดภัยและการจัดการสมาชิก (Authentication & Security)](#1-ระบบความปลอดภัยและการจัดการสมาชิก-authentication--security)
2. [ระบบปัญญาประดิษฐ์สร้างภาพ (Generative AI - Stable Diffusion)](#2-ระบบปัญญาประดิษฐ์สร้างภาพ-generative-ai---stable-diffusion)
3. [ระบบประมวลผลแต่งรูปภาพด้วย Computer Vision (Image Processing)](#3-ระบบประมวลผลแต่งรูปภาพด้วย-computer-vision-image-processing)
4. [ระบบประวัติและคลังรูปภาพ (History & Gallery Management)](#4-ระบบประวัติและคลังรูปภาพ-history--gallery-management)
5. [ระบบโปรไฟล์และสถิติผู้ใช้งาน (User Profile & Metrics)](#5-ระบบโปรไฟล์และสถิติผู้ใช้งาน-user-profile--metrics)
6. [ระบบจัดการข้อผิดพลาดและโครงสร้าง Response Envelope](#6-ระบบจัดการข้อผิดพลาดและโครงสร้าง-response-envelope)
7. [เสถียรภาพและการรองรับการใช้งานระดับ Production](#7-เสถียรภาพและการรองรับการใช้งานระดับ-production)

---

## 1. ระบบความปลอดภัยและการจัดการสมาชิก (Authentication & Security)

### 1.1 การสมัครสมาชิกและตรวจสอบชื่อซ้ำ (Registration & Duplicate Check)
- **Email Validation:** ตรวจสอบความถูกต้องของโครงสร้างอีเมลด้วย Regular Expression
- **Password Strength:** บังคับความยาวรหัสผ่านขั้นต่ำ 8 ตัวอักษร
- **Duplicate Prevention:** ตรวจจับอีเมลที่มีผู้ลงทะเบียนแล้ว หากซ้ำจะตอบกลับด้วย `EMAIL_EXISTS` (HTTP 409)
- **Secure Password Hashing:** เข้ารหัสผ่านด้วยฟังก์ชันทางเดียว (One-Way Hashing) โดยใช้ **PBKDF2-HMAC-SHA256** ผ่านไลบรารี Werkzeug ห้ามเก็บ Plaintext ลงฐานข้อมูลเด็ดขาด

### 1.2 การเข้าสู่ระบบและออก Token (Login & JWT Generation)
- ตรวจสอบความถูกต้องของอีเมลและรหัสผ่านเทียบกับค่าแฮช หากไม่ถูกต้องจะตอบกลับ `INVALID_CREDENTIALS` (HTTP 401)
- ออก **JSON Web Token (JWT)** ที่ลงนามด้วยอัลกอริทึม **HMAC-SHA256 (HS256)**
- Token มีอายุการใช้งาน 24 ชั่วโมง (`JWT_EXPIRES_IN`) พร้อมฝัง `user_id` และ `email` ไว้ใน Payload

### 1.3 ระบบคุ้มครองสิทธิ์และป้องกันการข้ามสิทธิ์ (IDOR & Anti-Hopping Protection)
- ใช้ Decorator [`@token_required`](file:///c:/Uni_Work'/3_1/Img_pro_code/Main/Image_Project/backend/app/middleware/jwt_auth.py) ครอบคลุมทุก Endpoint ที่ต้องการความปลอดภัย
- ป้องกันช่องโหว่ **IDOR (Insecure Direct Object Reference)**: ในการดูรายละเอียดรูปภาพ, การสตรีมไฟล์ภาพ, หรือการลบประวัติ ระบบจะบังคับกรองด้วย `user_id` ของ Token เสมอ ผู้ใช้ไม่สามารถเข้าถึงหรือลบข้อมูลของผู้ใช้ท่านอื่นได้แม้จะทราบ ID ก็ตาม

---

## 2. ระบบปัญญาประดิษฐ์สร้างภาพ (Generative AI - Stable Diffusion)

### 2.1 การสำรวจโมเดล Checkpoint (Model Discovery)
- เชื่อมต่อไปยัง AI Server ผ่าน endpoint `/sdapi/v1/sd-models` เพื่อดึงรายชื่อโมเดล Checkpoint ทั้งหมดที่ติดตั้งอยู่บน GPU Server
- แปลงข้อมูลโมเดลให้อยู่ในรูปแบบ `{ "title": "...", "model_name": "..." }` เพื่อส่งให้ Frontend แสดงใน Dropdown ให้ผู้ใช้เลือก

### 2.2 การควบคุมพารามิเตอร์การสร้างภาพ (Text-to-Image Generation)
- **Prompt & Negative Prompt:** รองรับข้อความอธิบายภาพที่ต้องการและสิ่งที่ไม่ต้องการ (สูงสุด 2,000 ตัวอักษร)
- **Resolution Control:** รองรับขนาดความละเอียดมาตรฐาน 3 ระดับ: `512x512`, `768x768`, และ `1024x1024` พิกเซล
- **Sampling Steps:** ควบคุมจำนวนรอบในการกำจัดสัญญาณรบกวน (1 - 50 Steps)
- **CFG Scale:** ควบคุมน้ำหนักความเคร่งครัดตามข้อความ Prompt (1.0 - 20.0)
- **Sampling Methods:** รองรับ Sampler หลากหลายรูปแบบ เช่น `Euler a`, `Euler`, `DPM++ 2M Karras`
- **Seed Control:** กำหนดค่า Seed เพื่อสร้างภาพเดิมซ้ำได้ หรือระบุ `-1` สำหรับการสุ่มแบบ Random

### 2.3 การจัดการคิวงานพร้อมกันบนการ์ดจอ (GPU Concurrency Queue)
- มีระบบ **Mutex Lock (`_gpu_lock`)** เพื่อให้คำขอประมวลผลบนการ์ดจอ GPU เข้าคิวทำงานทีละงานอย่างเป็นระเบียบ (Thread-Safe)
- ป้องกันไม่ให้ GPU Memory (VRAM) เกิดข้อผิดพลาด Out of Memory (OOM) เมื่อมีผู้ใช้หลายคนกดสั่งพร้อมกัน
- มี Timeout ควบคุมการรอคิวเพื่อตอบกลับ `AI_SERVER_BUSY` (HTTP 409) หรือ `AI_SERVER_TIMEOUT` (HTTP 504) อย่างเหมาะสม

### 2.4 การจัดเก็บและให้บริการสตรีมไฟล์รูปภาพ (Binary BLOB & Streaming)
- แปลงภาพผลลัพธ์ Base64 จาก AI Server ให้กลายเป็นข้อมูลไบนารี (`bytes`) แล้วจัดเก็บลงในฟิลด์ `image_data` (BLOB) ของฐานข้อมูล SQLite ทันที
- ให้บริการสตรีมไฟล์รูปภาพผ่าน Endpoint `/api/v1/images/:id` โดยตรงในรูปแบบ `image/png` ช่วยให้เบราว์เซอร์สามารถแคชภาพและโหลดได้อย่างรวดเร็ว

---

## 3. ระบบประมวลผลแต่งรูปภาพด้วย Computer Vision (Image Processing)

ประมวลผลภาพบนหน่วยความจำ (In-Memory Processing) ด้วย OpenCV และ Google MediaPipe โดยไม่ต้องบันทึกลงดิสก์:

### 3.1 Spot Blur (เบลอเฉพาะจุด)
- ผู้ใช้ระบุพิกัดและรัศมีวงกลมที่ลากเมาส์ผ่านหน้าเว็บ (`circles = [[x, y, r], ...]`)
- ผสานภาพเบลอ (Gaussian Blur) เข้ากับภาพต้นฉบับผ่านเทคนิค **Soft-Edge Alpha Masking** เพื่อให้รอยต่อระหว่างส่วนที่เบลอกับส่วนที่คมชัดดูเนียนตาเป็นธรรมชาติ

### 3.2 Cartoonize (แปลงภาพเป็นสไตล์การ์ตูน/อนิเมะ)
- **Bilateral Filtering:** เกลี่ยพื้นผิวและสีผิวให้เนียนเรียบโดยยังคงรักษาความคมของเส้นขอบวัตถุ
- **Color Quantization (K-Means Clustering):** ลดทอนเฉดสีของภาพให้เหลือกลุ่มสีหลัก (2 - 32 สี) สไตล์ภาพวาดระบายสีการ์ตูน
- **Adaptive Thresholding:** สกัดลายเส้นโครงร่างสีดำ (Ink Outlines) แล้วรวมเข้ากับเลเยอร์สี

### 3.3 Tilt-Shift (จำลองภาพถ่ายโมเดลจิ๋ว)
- **Color & Contrast Boost:** เร่งค่าความสดของสีในระบบสี HSV และเพิ่ม Contrast เพื่อจำลองสีของเล่นพลาสติก
- **Progressive Depth Blur:** คำนวณระนาบโฟกัสในแนวดิ่ง (Focus Position & Focus Width) และใช้ฟังก์ชัน **Smoothstep** เบลอส่วนบนและล่างแบบไล่ระดับความลึก

### 3.4 HDR Enhancer (เพิ่มมิติและความคมชัดสไตล์ HDR)
- **Gray World Auto White Balance:** ปรับสมดุลสีขาวอัตโนมัติ ชดเชยอุณหภูมิสีของแสงในภาพ
- **CIE L\*a\*b\* Color Space:** แปลงภาพเพื่อปรับเฉพาะมิติความสว่าง (Luminance) ไม่กระทบต่อโทนสีเดิม
- **CLAHE (Contrast Limited Adaptive Histogram Equalization):** ปรับเกลี่ยแสงในบริเวณเงามืดและไฮไลต์
- **Multi-scale Unsharp Masking:** ขับเน้น Micro-contrast และพื้นผิว (Texture) ให้มีความคมชัดสูง

### 3.5 Hand Gesture Recognition (ปัญญาประดิษฐ์จดจำท่าทางของมือ)
- ใช้โมเดล **Google MediaPipe Gesture Recognizer** ตรวจจับตำแหน่งมือและจุด Landmark 21 จุด
- จดจำท่าทางมือมาตรฐานได้ 7 ท่าทาง:
  - กำมือ (Closed Fist)
  - แบมือ (Open Palm)
  - ชี้นิ้วขึ้น (Pointing Up)
  - ชูนิ้วโป้ง (Thumb Up)
  - คว่ำนิ้วโป้ง (Thumb Down)
  - ชูสองนิ้ว (Victory)
  - สัญลักษณ์บอกรัก (ILoveYou)
- ส่งคืนชื่อท่าทางภาษาไทย/อังกฤษ พร้อมค่าความมั่นใจ (Confidence Score %)

### 3.6 Remove Background (ตัดและลบพื้นหลัง)
- **AI Human Segmentation:** ใช้โมเดล MediaPipe Selfie Multiclass Segmenter ตรวจหาตำแหน่งบุคคลในภาพ
- **OpenCV GrabCut Algorithm:** ผสานอัลกอริทึม Graph Cut ร่วมกับกรอบสี่เหลี่ยม (Bounding Box) และเส้นแปรงที่ผู้ใช้ป้าย (Interactive Strokes) สำหรับเก็บหรือลบรายละเอียดเฉพาะจุด
- **Edge Matting & Defringing:** ประมาณสีพื้นหลังเดิมที่ขอบเพื่อลบสีสะท้อน (Color Spill/Fringe) และทำขอบโปร่งใสให้นุ่มนวล ส่งคืนภาพเป็น PNG แบบโปร่งใส (BGRA) หรือเติมสีพื้นหลังตามต้องการ

---

## 4. ระบบประวัติและคลังรูปภาพ (History & Gallery Management)

- **User Isolation:** แสดงเฉพาะรายการภาพที่เป็นของผู้ใช้งานที่ล็อกอินอยู่เท่านั้น
- **Server-Side Pagination:** รองรับการแบ่งหน้าผ่านพารามิเตอร์ `page` และ `limit` (ค่าเริ่มต้น 20 รายการต่อหน้า) เรียงลำดับจากภาพล่าสุดไปเก่าสุด
- **Metadata Preservation:** บันทึกพารามิเตอร์ทั้งหมดที่ใช้ในการสร้างภาพ (Prompt, Checkpoint, Seed, Steps, Size)
- **Safe Pre-fill Compatibility:** การันตีการส่งค่าที่ไม่เป็น `null` สำหรับฟิลด์สำคัญ เพื่อให้ผู้ใช้สามารถกดปุ่ม **"Again"** บนหน้าเว็บเพื่อดึงค่าเดิมกลับมาสร้างใหม่ได้อย่างปลอดภัย
- **Cascade Deletion:** เมื่อผู้ใช้สั่งลบภาพ รายการประวัติและข้อมูลไบนารีภาพในฐานข้อมูลจะถูกลบออกอย่างสมบูรณ์

---

## 5. ระบบโปรไฟล์และสถิติผู้ใช้งาน (User Profile & Metrics)

- แสดงข้อมูลบัญชีผู้ใช้: รหัสประจำตัว (`id`), อีเมล (`email`), และวันเวลาที่ลงทะเบียน (`created_at`)
- **Generation Metric:** รายงานจำนวนรูปภาพทั้งหมดที่ผู้ใช้ได้สร้างขึ้นในระบบ (`generation_count`)
- ทำงานอย่างรวดเร็วด้วยการคิวรีรอบเดียว (Single Optimized Query)

---

## 6. ระบบจัดการข้อผิดพลาดและโครงสร้าง Response Envelope

ระบบกำหนดรหัสข้อผิดพลาดและ HTTP Status ไว้อย่างเป็นระเบียบ:

| รหัสข้อผิดพลาด (Code) | HTTP Status | ความหมาย |
|---|---|---|
| `VALIDATION_ERROR` | 400 | ข้อมูลที่ส่งมาไม่ถูกต้องตามเงื่อนไข หรือประเภทข้อมูลผิดพลาด |
| `INVALID_IMAGE` | 400 | ไฟล์รูปภาพเสียหายหรือไม่สามารถถอดรหัส (Decode) ได้ |
| `INVALID_CREDENTIALS` | 401 | อีเมลหรือรหัสผ่านไม่ถูกต้อง |
| `UNAUTHORIZED` | 401 | ไม่มีสิทธิ์เข้าถึง, Token หมดอายุ หรือไม่ถูกต้อง |
| `GENERATION_NOT_FOUND`| 404 | ไม่พบข้อมูลประวัติภาพตาม ID ที่ระบุ หรือไม่ใช่เจ้าของ |
| `IMAGE_NOT_FOUND` | 404 | ไม่พบข้อมูลไบนารีรูปภาพในฐานข้อมูล |
| `EMAIL_EXISTS` | 409 | อีเมลนี้ถูกลงทะเบียนในระบบไปแล้ว |
| `AI_SERVER_BUSY` | 409 | คิวประมวลผลบนการ์ดจอเต็ม |
| `UNSUPPORTED_FILE_TYPE`| 415 | ไฟล์ที่อัปโหลดไม่ใช่นามสกุล .jpg, .jpeg, .png, หรือ .webp |
| `FILE_TOO_LARGE` | 413 | ไฟล์ที่อัปโหลดมีขนาดเกินขีดจำกัดสูงสุด 16 MB |
| `GENERATION_FAILED` | 500 | กระบวนการสร้างหรือประมวลผลรูปภาพล้มเหลว |
| `INTERNAL_SERVER_ERROR`| 500 | เกิดข้อผิดพลาดที่ไม่คาดคิดภายในระบบ Backend |
| `AI_SERVER_ERROR` | 502/503 | ไม่สามารถเชื่อมต่อกับ AI GPU Server ได้ |
| `MODEL_UNAVAILABLE` | 503 | ไม่พบโมเดลที่ต้องการบน AI Server หรือดาวน์โหลดโมเดลไม่สำเร็จ |
| `AI_SERVER_TIMEOUT` | 504 | AI Server ใช้เวลาประมวลผลนานเกินกำหนด |

---

## 7. เสถียรภาพและการรองรับการใช้งานระดับ Production (Production Readiness)

1. **Auto Schema Migration:** ระบบตรวจสอบคอลัมน์ในตาราง SQLite อัตโนมัติเมื่อเริ่มระบบ หากขาดคอลัมน์ใดจะสร้างให้ทันทีโดยไม่ทำให้ข้อมูลเดิมสูญหาย
2. **Hybrid Disk-Backed Storage:** จัดเก็บไฟล์ภาพแยกบนฮาร์ดดิสก์ (`uploads/generations/{id}.png`) และสตรีมตรงผ่านคำสั่ง Kernel OS `sendfile` ลดการกิน RAM และป้องกันขนาดไฟล์ฐานข้อมูล SQLite บวมเกินควบคุม
3. **Anti-DoS / Payload Limit:** ควบคุมขนาดไฟล์อัปโหลดสูงสุด 16 MB ด้วย `MAX_CONTENT_LENGTH` พร้อม Error Handler `FILE_TOO_LARGE` (HTTP 413) ป้องกันการโจมตีทำให้เกิด Out-of-Memory (OOM)
4. **Pre-download AI Models:** มีสคริปต์ `scripts/download_models.py` สำหรับเตรียมโมเดล MediaPipe ล่วงหน้า ขจัดปัญหา Cold Start และ Network Timeout กลาง Request ของผู้ใช้
5. **Centralized Rotating Logger:** ระบบบันทึก Log หมุนเวียนลงไฟล์ `logs/luma_backend.log` (5 MB x 3 ไฟล์) และแสดงผลบน Console แบบ Real-time บันทึกเวลาคิว GPU และ Exception Stacktrace ครบถ้วน
6. **Production WSGI Ready (Gunicorn):** มีไฟล์ `gunicorn_conf.py` กำหนดค่า `workers = 1` และ `threads = 8` รักษาความปลอดภัยของ Mutex Lock บน GPU สำหรับเซิร์ฟเวอร์แบบ Single Node
7. **Health Check & Monitoring:** มี Endpoint `GET /api/v1/health` สำหรับให้ Docker, Kubernetes หรือ Load Balancer ตรวจสอบความพร้อมทำงาน
8. **Reverse Proxy Ready:** ครอบ WSGI App ด้วย `ProxyFix` เพื่อให้ Backend รับค่า Client IP จริงผ่าน Nginx ได้อย่างแม่นยำ
9. **Automated Test Suite:** มีชุดทดสอบอัตโนมัติ 13 ชุดครอบคลุมทุกระบบหลักบน In-Memory Database (ผ่าน 100%)
