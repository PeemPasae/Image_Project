# เอกสารสรุปโครงสร้างและคู่มือรีวิวโค้ดระบบ Backend (ฉบับจบในไฟล์เดียว พร้อมพรีเซนต์)
**โปรเจกต์:** LUMA AI & Image Processing System  
**ภาษาและเฟรมเวิร์ก:** Python 3.11, Flask 3.0.3, OpenCV, Google MediaPipe, SQLite, SQLAlchemy

---

## สารบัญเนื้อหา (Quick Navigation)
1. [บทนำและบทพูดสรุปสำหรับพรีเซนต์ 1 นาที (Elevator Pitch)](#1-บทนำและบทพูดสรุปสำหรับพรีเซนต์-1-นาที)
2. [แผนภาพสถาปัตยกรรมระบบ (System Architecture)](#2-แผนภาพสถาปัตยกรรมระบบ)
3. [เจาะลึกรีวิวโค้ดทีละบรรทัด (Line-by-Line Code Review)](#3-เจาะลึกรีวิวโค้ดทีละบรรทัด-line-by-line-code-review)
   * 3.1 [`backend/run.py` - จุดเริ่มต้นเซิร์ฟเวอร์](#31-backendrunpy---จุดเริ่มต้นเซิร์ฟเวอร์)
   * 3.2 [`backend/config.py` - ศูนย์กลางการตั้งค่า](#32-backendconfigpy---ศูนย์กลางการตั้งค่า)
   * 3.3 [`backend/app/__init__.py` - Application Factory & Auto-Migration](#33-backendapp__init__py---application-factory--auto-migration)
   * 3.4 [`backend/app/models/` - ฐานข้อมูลผู้ใช้และรูปภาพ (BLOB Storage)](#34-backendappmodels---ฐานข้อมูลผู้ใช้และรูปภาพ)
   * 3.5 [`backend/app/middleware/jwt_auth.py` - ยามตรวจบัตรและระบบความปลอดภัย](#35-backendappmiddlewarejwt_authpy---ยามตรวจบัตรและระบบความปลอดภัย)
   * 3.6 [`backend/app/routes/auth.py` - การสมัครสมาชิกและแฮชรหัสผ่าน](#36-backendapproutesauthpy---การสมัครสมาชิกและแฮชรหัสผ่าน)
   * 3.7 [`backend/app/routes/sd.py` - สั่งสร้างภาพ AI และป้องกันการแอบดูรูป (IDOR)](#37-backendapproutessdpy---สั่งสร้างภาพ-ai-และป้องกันการแอบดูรูป-idor)
   * 3.8 [`backend/app/services/ai_client.py` - คิวการ์ดจอ Mutex GPU Lock & Time Estimation](#38-backendappservicesai_clientpy---คิวการ์ดจอ-mutex-gpu-lock--time-estimation)
   * 3.9 [`backend/app/services/image_filters/spot_blur.py` - เบลอเฉพาะจุด](#39-backendappservicesimage_filtersspot_blurpy---เบลอเฉพาะจุด)
   * 3.10 [`backend/app/services/image_filters/gesture.py` - ตรวจจับท่าทางมือ MediaPipe](#310-backendappservicesimage_filtersgesturepy---ตรวจจับท่าทางมือ-mediapipe)
   * 3.11 [`backend/app/services/image_filters/remove_bg.py` - ระบบตัดพื้นหลังไฮบริด](#311-backendappservicesimage_filtersremove_bgpy---ระบบตัดพื้นหลังไฮบริด)
   * 3.12 [`backend/app/services/image_filters/routes.py` - จุดรับคำขอ Image Processing](#312-backendappservicesimage_filtersroutespy---จุดรับคำขอ-image-processing)
4. [สรุปตาราง API Endpoints และ Error Codes ทั้งหมด](#4-สรุปตาราง-api-endpoints-และ-error-codes-ทั้งหมด)
5. [คลังเก็งคำถาม-คำตอบ สำหรับสอบพรีเซนต์ (Defense Q&A Cheat Sheet)](#5-คลังเก็งคำถาม-คำตอบ-สำหรับสอบพรีเซนต์-defense-qa-cheat-sheet)

---

## 1. บทนำและบทพูดสรุปสำหรับพรีเซนต์ 1 นาที

> **บทพูดพรีเซนต์ (แนะนำให้ใช้พูดตอนเริ่ม):**
> *"ระบบ Backend ของ LUMA ถูกออกแบบขึ้นมาเพื่อทำหน้าที่เป็นศูนย์กลางเชื่อมประสานระหว่าง 3 ส่วนหลักครับ:
> 1. **ส่วนหน้าบ้าน (Frontend):** สื่อสารผ่าน REST API ภายใต้การควบคุมความปลอดภัยด้วย **JWT Authentication** และระบบป้องกัน **IDOR**
> 2. **ส่วนประมวลผล AI หนัก (Stable Diffusion Server):** ควบคุมการส่งงานเข้า GPU ผ่านระบบ **Mutex Concurrency Lock** เพื่อป้องกันไม่ให้การ์ดจอหน่วยความจำเต็มเมื่อมีคนกดพร้อมกัน พร้อมมีอัลกอริทึมคำนวณเวลาประเมินล่วงหน้า
> 3. **ส่วนประมวลผลภาพเร็ว (Edge Image Processing):** เราพัฒนาฟังก์ชัน **Spot Blur, Gesture Recognition 7 ท่าทาง** และ **Hybrid Background Removal** ด้วย OpenCV และ MediaPipe ให้ทำงานบนเซิร์ฟเวอร์ Backend ได้ทันทีโดยไม่ต้องต่อคิว GPU 
> นอกจากนี้ ฐานข้อมูล SQLite ยังมีระบบ **Auto Schema Migration** ที่ตรวจสอบและอัปเดตคอลัมน์ให้อัตโนมัติเมื่อเริ่มระบบครับ"*

---

## 2. แผนภาพสถาปัตยกรรมระบบ

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
| [auth_bp]         [sd_bp]          [history_bp]        [profile_bp]      [process_bp] |
| /register         /generate        /history            /profile          /process/*   |
| /login            /estimate        /history/:id                          (Computer    |
|                   /models          (DELETE)                              Vision &     |
|                   /images/:id                                            MediaPipe)   |
|                       │                                                       │   |
|                       ▼                                                       ▼   |
|               [services/ai_client.py]                         [services/image_filters]|
|               - Concurrency GPU Lock (Mutex)                  - Spot Blur (OpenCV)    |
|               - Queue Counter & Time Estimate                 - Gesture (MediaPipe)   |
|               - SD WebUI / Forge Client                       - Remove BG (GrabCut)   |
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

## 3. เจาะลึกรีวิวโค้ดทีละบรรทัด (Line-by-Line Code Review)

---

### 3.1 `backend/run.py` - จุดเริ่มต้นเซิร์ฟเวอร์
**หน้าที่:** จุดรันระบบ (Entry Point) ดึงพอร์ตจากตัวแปรสภาพแวดล้อม และเปิดให้เชื่อมต่อข้ามเครื่อง

```python
import os
import sys
from app import create_app

# บรรทัดที่ 12-16: แก้ปัญหาฟอนต์ไทยบน Windows Terminal เพี้ยน
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# บรรทัดที่ 19: สร้าง Flask Instance ผ่าน Application Factory
app = create_app()

if __name__ == "__main__":
    # บรรทัดที่ 23: อ่านพอร์ตจาก .env ถ้าไม่มีให้ใช้พอร์ต 5000 เป็นค่าตั้งต้น
    port = int(os.getenv("PORT", 5000))
    
    # บรรทัดที่ 36: รันแอปพลิเคชัน
    # host="0.0.0.0" สำคัญมาก! ทำให้เครื่องอื่นในวงแลน หรือ Nginx ยิงเข้ามาหาได้
    # debug=True ช่วย reload โค้ดให้อัตโนมัติเมื่อมีการแก้ไขไฟล์
    app.run(host="0.0.0.0", port=port, debug=True)
```

* **คำถามที่อาจโดนถาม:** *"ทำไมต้องใส่ `host='0.0.0.0'` ทำไมไม่ใช้ `127.0.0.1`?"*  
  **คำตอบ:** ถ้าใส่ `127.0.0.1` จะเรียกได้เฉพาะภายในเครื่องตัวเองเท่านั้น แต่สถาปัตยกรรมของเรามี Nginx หรืออุปกรณ์ภายนอกเชื่อมต่อเข้ามา การใช้ `0.0.0.0` จะสั่งให้ Flask เปิดรับสัญญาณจากทุก Network Interface ในเครื่อง

---

### 3.2 `backend/config.py` - ศูนย์กลางการตั้งค่า
**หน้าที่:** รวมศูนย์คอนฟิกูเรชันทั้งหมดของระบบ โหลดค่าจาก `.env` ไม่ให้มีการฮาร์ดโค้ดคีย์ลับกระจายในโค้ด

```python
import os
from datetime import timedelta
from dotenv import load_dotenv

# บรรทัดที่ 12: โหลดตัวแปรจากไฟล์ .env เข้าสู่ os.environ
load_dotenv()

class Config:
    # บรรทัดที่ 23-27: ดึงรหัสลับสำหรับเซ็น JWT Token
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET") or "luma_default_jwt_secret_key_2026"

    # บรรทัดที่ 30: กำหนดให้ Token มีอายุใช้งานได้ 24 ชั่วโมง
    JWT_EXPIRES_IN = timedelta(hours=24)

    # บรรทัดที่ 36: กำหนด CORS เปิดรับคำขอจากหน้าเว็บ
    CORS_ORIGINS = "*"

    # บรรทัดที่ 42: URL ชี้ไปยังเครื่อง AI Server (ถ้าไม่ตั้งไว้ให้ชี้ไปที่ IP แลนเริ่มต้น)
    AI_SERVER_URL = os.environ.get("AI_SERVER_URL", "http://172.20.56.221:8088")

    # บรรทัดที่ 45: เวลา Timeout รอ AI เจนภาพสูงสุด 75 วินาที
    AI_SERVER_TIMEOUT_SECONDS = 75
```

---

### 3.3 `backend/app/__init__.py` - Application Factory & Auto-Migration
**หน้าที่:** ประกอบร่าง Flask App, ต่อฐานข้อมูล SQLite, ลงทะเบียน 5 Blueprints, และตรวจเช็กโครงสร้างตารางอัตโนมัติ

```python
def create_app(test_config=None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    # กำหนด CORS รองรับคำขอทั้ง Localhost และเครือข่าย LAN
    CORS(app, origins=Config.CORS_ORIGINS, methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

    # ชี้ตำแหน่งไฟล์ SQLite ไปที่ database/database.db
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        db_path = os.path.join(project_root, "database", "database.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # ลงทะเบียนเส้นทางแยกตามโมดูล (Blueprints)
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.sd import sd_bp
    from app.routes.history import history_bp
    from app.services.image_filters import process_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    app.register_blueprint(process_bp, url_prefix="/api/v1")

    # ==========================================================================
    # ระบบ Auto Schema Migration (ตรวจเช็กและเติมคอลัมน์ให้อัตโนมัติ)
    # ==========================================================================
    with app.app_context():
        db.create_all() # สร้างตารางถ้ายังไม่มี
        try:
            inspector = db.inspect(db.engine)
            # ดึงรายชื่อคอลัมน์ที่มีอยู่จริงในตารางปัจจุบัน
            existing_columns = {col["name"] for col in inspector.get_columns("generations")}

            # รายการคอลัมน์ที่ระบบต้องการใช้งาน
            migrations = [
                ("image_data", "ALTER TABLE generations ADD COLUMN image_data BLOB"),
                ("category", "ALTER TABLE generations ADD COLUMN category VARCHAR(50) DEFAULT 'sd_generate'"),
                ("action_type", "ALTER TABLE generations ADD COLUMN action_type VARCHAR(50) DEFAULT 'txt2img'"),
                ("params", "ALTER TABLE generations ADD COLUMN params TEXT DEFAULT '{}'"),
                ("source_image_id", "ALTER TABLE generations ADD COLUMN source_image_id INTEGER"),
            ]

            # วนลูปเช็ก: ถ้าคอลัมน์ไหนยังไม่มี ให้สั่งรัน ALTER TABLE เติมเข้าไปทันที
            for col_name, sql_stmt in migrations:
                if col_name not in existing_columns:
                    db.session.execute(db.text(sql_stmt))
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app
```

* **คำถามที่อาจโดนถาม:** *"ทำไมต้องมี Auto-Migration ในโค้ด ทำไมไม่ใช้ Flask-Migrate หรือ Alembic?"*  
  **คำตอบ:** ในโปรเจกต์ระดับนี้และใช้งาน SQLite การใช้ Alembic จะเพิ่มความซับซ้อนในการตั้งค่าและรันคำสั่ง migration cli สำหรับเพื่อนในทีม การเขียน Auto-Migration แบบตรวจเช็กคอลัมน์ด้วย `db.inspect()` ทำให้ใครก็ตามที่โคลนโค้ดไป เพียงแค่กดรัน เซิร์ฟเวอร์จะอัปเดตตารางฐานข้อมูล SQLite ให้เข้ากันได้ 100% ทันทีโดยไม่ต้องรันคำสั่งพิเศษใด ๆ เพิ่มเติม

---

### 3.4 `backend/app/models/` - ฐานข้อมูลผู้ใช้และรูปภาพ

#### ไฟล์: `backend/app/models/user.py`
```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False) # เก็บเฉพาะค่าแฮช ห้ามเก็บรหัสจริง
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # จุดเด่น: Cascade Delete ถ้าลบ User คนนี้ รูปภาพในตาราง generations ทั้งหมดจะถูกลบกวาดตามไปด้วยทันที
    generations = db.relationship("Generation", backref="user", lazy=True, cascade="all, delete-orphan")
```

#### ไฟล์: `backend/app/models/generation.py`
```python
class Generation(db.Model):
    __tablename__ = "generations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=True)
    negative_prompt = db.Column(db.Text, nullable=True)
    checkpoint = db.Column(db.String(255), nullable=True)
    sampler = db.Column(db.String(100), nullable=True)
    width = db.Column(db.Integer, default=512)
    height = db.Column(db.Integer, default=512)
    steps = db.Column(db.Integer, default=20)
    cfg_scale = db.Column(db.Float, default=7.0)
    seed = db.Column(db.BigInteger, default=-1)

    # จุดเด่น: เก็บรูปภาพเป็น Binary BLOB ลงในฐานข้อมูล SQLite โดยตรง
    image_data = db.Column(db.LargeBinary, nullable=True)

    category = db.Column(db.String(50), default="sd_generate") # 'sd_generate'
    action_type = db.Column(db.String(50), default="txt2img")
    params = db.Column(db.Text, default="{}") # เก็บพารามิเตอร์อื่น ๆ เป็น JSON String
    source_image_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

### 3.5 `backend/app/middleware/jwt_auth.py` - ยามตรวจบัตรและระบบความปลอดภัย
**หน้าที่:** Decorator `@token_required` ตรวจความถูกต้องของบัตรผ่าน JWT และสกัด `request.user_id`

```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. อ่านค่า Header "Authorization" จากหน้าบ้าน
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return error_response(UNAUTHORIZED, "Authorization header is missing", 401)

        # 2. ตรวจสอบว่าขึ้นต้นด้วย "Bearer <token>" หรือไม่
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response(UNAUTHORIZED, "Invalid Authorization header format. Must be 'Bearer <token>'", 401)

        token = parts[1]
        try:
            # 3. ถอดรหัสและตรวจลายเซ็น Token ด้วย Secret Key (HS256)
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            
            # 4. สกัด user_id และ email แปะไว้ที่ request ให้ Controller เรียกใช้ได้
            request.user_id = payload.get("user_id")
            request.user_email = payload.get("email")

        except jwt.ExpiredSignatureError:
            # Token มีอายุเกิน 24 ชม.
            return error_response(UNAUTHORIZED, "Token has expired", 401)
        except (jwt.InvalidTokenError, Exception) as e:
            # Token ถูกดัดแปลง หรือปลอมแปลงลายเซ็น
            return error_response(UNAUTHORIZED, f"Invalid token: {str(e)}", 401)

        return f(*args, **kwargs)
    return decorated
```

---

### 3.6 `backend/app/routes/auth.py` - การสมัครสมาชิกและแฮชรหัสผ่าน

```python
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # 1. Validation ตรวจความยาวรหัสผ่าน
    if len(password) < 8:
        return error_response(VALIDATION_ERROR, "Password must be at least 8 characters", 400)

    # 2. ตรวจอีเมลซ้ำในฐานข้อมูล
    if User.query.filter_by(email=email).first():
        return error_response(EMAIL_EXISTS, "Email is already registered", 409)

    # 3. แฮชรหัสผ่านด้วย PBKDF2/SHA256 (ห้ามเก็บรหัสจริง)
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return success_response({"message": "Registration successful", "user": {"id": new_user.id, "email": new_user.email}}, 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # 1. ดึงข้อมูล User จากอีเมล
    user = User.query.filter_by(email=email).first()

    # 2. นำรหัสผ่านที่กรอกมา ไปปั่นเทียบกับแฮชในฐานข้อมูล
    if not user or not check_password_hash(user.password_hash, password):
        return error_response(INVALID_CREDENTIALS, "Invalid email or password", 401)

    # 3. รหัสถูกต้อง -> ออกบัตร JWT Token อายุ 24 ชั่วโมง
    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_payload, get_jwt_secret(), algorithm="HS256")

    return success_response({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "user": {"id": user.id, "email": user.email}
    })
```

---

### 3.7 `backend/app/routes/sd.py` - สั่งสร้างภาพ AI และป้องกันการแอบดูรูป (IDOR)

```python
# สั่งสร้างรูปภาพ AI
@sd_bp.route("/generate", methods=["POST"])
@token_required
def generate_image():
    payload = request.get_json() or {}
    
    # 1. ส่งคำขอเข้าคิว AI Client (มีการ์ดจอ GPU Mutex Lock คุมอยู่)
    base64_image, actual_time, est_time = generate_sd_image(payload)
    
    # 2. ถอดรหัส Base64 String กลับมาเป็นข้อมูล Binary Bytes
    image_bytes = base64.b64decode(base64_image)

    # 3. บันทึกลงตาราง generations ผูก user_id ของคนที่ล็อกอินอยู่
    gen = Generation(
        user_id=request.user_id,
        prompt=payload.get("prompt"),
        negative_prompt=payload.get("negative_prompt"),
        checkpoint=payload.get("checkpoint"),
        sampler=payload.get("sampler"),
        width=int(payload.get("width", 512)),
        height=int(payload.get("height", 512)),
        steps=int(payload.get("steps", 20)),
        cfg_scale=float(payload.get("cfg_scale", 7.0)),
        seed=int(payload.get("seed", -1)),
        image_data=image_bytes, # บันทึกก้อน Binary ลงตาราง SQLite
        category="sd_generate",
        action_type="txt2img"
    )
    db.session.add(gen)
    db.session.commit()

    return success_response({
        "generation_id": gen.id,
        "image_url": f"/api/v1/images/{gen.id}",
        "actual_time_seconds": actual_time
    }, 201)


# สตรีมไฟล์รูปภาพพร้อมระบบป้องกัน IDOR (Anti-Hopping)
@sd_bp.route("/images/<int:generation_id>", methods=["GET"])
@token_required
def get_image(generation_id):
    # ไม้เด็ดความปลอดภัย: ต้องค้นหาคู่ id = :id AND user_id = request.user_id เสมอ!
    gen = Generation.query.filter_by(id=generation_id, user_id=request.user_id).first()
    
    # ถ้าไม่ใช่เจ้าของ หรือไม่มีรูปภาพ จะตอบกลับ 404 ทันที ไม่ยอมให้เดาเลข ID แอบดูรูปคนอื่น
    if not gen or not gen.image_data:
        return error_response(GENERATION_NOT_FOUND, "Image not found or unauthorized", 404)

    # สตรีมไบนารีภาพออกเป็นไฟล์ PNG ให้เบราว์เซอร์แสดงรูปได้โดยตรง
    return send_file(io.BytesIO(gen.image_data), mimetype="image/png")
```

---

### 3.8 `backend/app/services/ai_client.py` - คิวการ์ดจอ Mutex GPU Lock & Time Estimation

```python
_gpu_lock = threading.Lock()            # กลอนประตูล็อกการ์ดจอ (Mutex Lock)
_waiting_counter_lock = threading.Lock()
_waiting_jobs_count = 0                 # ตัวนับจำนวนคนที่กำลังยืนรอคิว

# คำนวณเวลาประเมินล่วงหน้า
def calculate_estimated_time(width: int = 512, height: int = 512, steps: int = 20) -> dict:
    seconds_per_step = 0.15 # ความเร็วเฉลี่ยต่อ Step ของขนาด 512x512
    resolution_factor = (width * height) / (512.0 * 512.0) # ตัวคูณตามขนาดภาพ
    base_generation = round(max(2.0, steps * seconds_per_step * resolution_factor), 1)

    with _waiting_counter_lock:
        current_waiting = _waiting_jobs_count # อ่านจำนวนคนรอคิว

    queue_wait = round(current_waiting * 4.5, 1) # คนข้างหน้าใช้เฉลี่ยคนละ 4.5 วิ
    total_est = round(base_generation + queue_wait, 1)

    return {
        "estimated_generation_seconds": base_generation,
        "queue_position": current_waiting,
        "total_estimated_seconds": total_est
    }


# ฟังก์ชันเข้าคิวและส่งคำขอไปยัง AI Server
def generate_sd_image(payload: dict) -> tuple:
    global _waiting_jobs_count
    server_url = get_ai_server_url()

    # 1. คำนวณเวลาประเมิน
    est_info = calculate_estimated_time(
        width=int(payload.get("width", 512)),
        height=int(payload.get("height", 512)),
        steps=int(payload.get("steps", 20))
    )

    # 2. เพิ่มจำนวนงานรอคิวในระบบ
    with _waiting_counter_lock:
        _waiting_jobs_count += 1

    # 3. ยืนรอคิวขอสิทธิ์ใช้งาน GPU (รอได้สูงสุด 120 วินาที)
    lock_acquired = _gpu_lock.acquire(blocking=True, timeout=120)

    # 4. เมื่อได้เข้าใช้ หรือหลุดคิว ให้ลดตัวเลขคนรอลง
    with _waiting_counter_lock:
        _waiting_jobs_count = max(0, _waiting_jobs_count - 1)

    if not lock_acquired:
        raise AIServerBusyException("GPU Server is busy. Queue wait exceeded 120s.")

    # 5. สั่งงาน GPU ทีละคนอย่างปลอดภัย
    try:
        start_time = time.perf_counter()
        response = requests.post(f"{server_url}/sdapi/v1/txt2img", json=payload, timeout=75)
        actual_duration = round(time.perf_counter() - start_time, 2)

        data = response.json()
        base64_image = data["images"][0]
        return base64_image, actual_duration, est_info["total_estimated_seconds"]
    finally:
        # 6. จุดสำคัญที่สุด: ต้องปลดล็อกประตูเสมอเมื่อทำเสร็จ ให้คิวถัดไปได้ทำต่อ!
        _gpu_lock.release()
```

---

### 3.9 `backend/app/services/image_filters/spot_blur.py` - เบลอเฉพาะจุด

```python
def spot_blur(img, circles, strength=10, soft=True):
    # 1. เบลอภาพทั้งภาพเตรียมรอไว้ (Kernel ต้องเป็นเลขคี่เสมอ)
    k = strength * 2 + 1
    blurred = cv2.GaussianBlur(img, (k, k), 0)

    # 2. สร้างแผ่น Mask สีดำมืด (0.0) แล้ววาดวงกลมสีขาว (1.0) ตรงจุดที่ผู้ใช้จิ้มเมาส์
    mask = np.zeros(img.shape[:2], np.float32)
    for x, y, r in circles:
        cv2.circle(mask, (int(x), int(y)), int(r), 1.0, -1) # -1 คือระบายทึบเต็มวง

    # 3. ไม้เด็ด: ทำขอบวงกลมให้นุ่มฟุ้งด้วย Gaussian Blur บนตัว Mask ไม่ให้ขอบตัดคมแข็ง
    if soft and circles:
        edge = int(max(r for _, _, r in circles) * 0.5) * 2 + 1
        mask = cv2.GaussianBlur(mask, (edge, edge), 0)

    # 4. ผสมภาพด้วย Alpha Blending: ขาว (1.0) ใช้รูปเบลอ, ดำ (0.0) ใช้รูปเดิม
    mask = mask[:, :, None] # เพิ่มมิติให้คูณกับ 3 สี BGR ได้
    out = img * (1 - mask) + blurred * mask
    return out.astype(np.uint8)
```

---

### 3.10 `backend/app/services/image_filters/gesture.py` - ตรวจจับท่าทางมือ MediaPipe

```python
# แปลงสี BGR เป็น RGB เพราะ OpenCV อ่าน BGR แต่ MediaPipe บังคับใช้ RGB
def _to_mp_image(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

# โหมดที่ 1: วิเคราะห์รูปนิ่งเดี่ยว ๆ (ใช้ Recognizer แคชร่วมกันได้)
def recognize_gesture(img, num_hands=2, min_confidence=0.5):
    mp_image = _to_mp_image(img)
    key = (num_hands, round(min_confidence, 1))

    with _image_lock:
        if key not in _image_recognizers:
            _image_recognizers[key] = _create_recognizer(vision.RunningMode.IMAGE, *key)
        start = time.perf_counter()
        result = _image_recognizers[key].recognize(mp_image)
        inference_ms = (time.perf_counter() - start) * 1000
    return _format(result, inference_ms)

# โหมดที่ 2: วิเคราะห์สตรีมเว็บแคม (แยก Session ต่อผู้ใช้ เพื่อจำตำแหน่งมือข้ามเฟรม)
def recognize_gesture_frame(img, user_id, num_hands=2, min_confidence=0.5):
    mp_image = _to_mp_image(img)
    key = (num_hands, round(min_confidence, 1))
    now = time.monotonic()

    with _video_lock:
        # คืนแรมทันทีถ้าผู้ใช้คนไหนทิ้งหน้าเว็บไปเกิน 60 วินาที
        _close_idle_sessions(now)

        # หา Recognizer ประจำตัวของผู้ใช้คนนี้
        session = _sessions.get(user_id)
        if session is None or session["key"] != key:
            session = {
                "key": key,
                "recognizer": _create_recognizer(vision.RunningMode.VIDEO, *key),
                "last_ts": 0,
            }
            _sessions[user_id] = session

        # MediaPipe Video Mode กำหนดว่า Timestamp ต้องเดินหน้าเสมอ
        timestamp_ms = max(session["last_ts"] + 1, int(now * 1000))
        session["last_ts"] = timestamp_ms
        session["last_used"] = now

        start = time.perf_counter()
        result = session["recognizer"].recognize_for_video(mp_image, timestamp_ms)
        inference_ms = (time.perf_counter() - start) * 1000

    return _format(result, inference_ms)
```

---

### 3.11 `backend/app/services/image_filters/remove_bg.py` - ระบบตัดพื้นหลังไฮบริด

```python
def remove_background(img, rect=None, strokes=None, use_ai=True, bg_color=None):
    H, W = img.shape[:2]

    # 1. ย่อรูปเหลือด้านยาว 900px ก่อน เพื่อให้ GrabCut รันเสร็จใน 0.2 วินาที (ไม่ค้าง)
    s = min(1.0, WORK_SIDE / max(H, W))
    small = cv2.resize(img, (round(W * s), round(H * s)), interpolation=cv2.INTER_AREA) if s < 1 else img

    # 2. ให้ AI MediaPipe สแกนความน่าจะเป็นของคน (0.0 - 1.0)
    person = _person_prob(small) if use_ai else None

    # 3. รวมร่าง AI + กรอบ Rect + แปรงแต้มของผู้ใช้ ส่งให้ GrabCut ตัดเส้นผม
    alpha_small = _cut(small, person, small_rect, small_strokes)

    # 4. ถอนสีสะท้อนของฉากหลังเดิมออกจากไรผม (Color Decontamination) ด้วยสมการ Matting
    alpha = cv2.resize(alpha_small, (W, H), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (0, 0), max(1.0, 1.0 / s))
    bg_old = cv2.resize(bg_small, (W, H), interpolation=cv2.INTER_LINEAR)

    a = alpha[:, :, None]
    I = img.astype(np.float32)
    # สมการ: สีจริง (F) = [สีที่เห็น (I) - (1 - alpha) * สีฉากหลังเดิม] / alpha
    F = np.clip((I - (1 - a) * bg_old) / np.maximum(a, 0.15), 0, 255)
    F = np.where(a > 0.95, I, F) # กลางตัวคนใช้สีเดิม 100%

    # 5. ส่งออกเป็นไฟล์ PNG โปร่งใส (BGRA) หรือเติมสีฉากหลังใหม่ตามที่เลือก
    if bg_color is None:
        return np.dstack([F, alpha * 255]).astype(np.uint8)
    else:
        out = F * a + np.array(bg_color, np.float32) * (1 - a)
        return out.astype(np.uint8)
```

---

### 3.12 `backend/app/services/image_filters/routes.py` - จุดรับคำขอ Image Processing

```python
@process_bp.route("/process/spot-blur", methods=["POST"])
@token_required
def process_spot_blur():
    # 1. ตรวจสอบไฟล์ภาพ
    file = request.files.get("image")
    if not file or not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return error_response(UNSUPPORTED_FILE_TYPE, "Only .jpg, .jpeg, .png, .webp are supported", 415)

    # 2. อ่านพิกัดวงกลมที่ลากเมาส์
    circles = json.loads(request.form.get("circles", "[]"))
    strength = int(request.form.get("strength", 10))
    soft = request.form.get("soft", "true") == "true"

    # 3. Decode ภาพไบนารีเป็น Image BGR ของ OpenCV
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # 4. เรียกใช้งานฟังก์ชัน spot_blur
    result = spot_blur(img, circles, strength=strength, soft=soft)

    # 5. Encode ผลลัพธ์เป็นไฟล์ PNG แล้วส่งสตรีมกลับหน้าบ้าน
    png = cv2.imencode(".png", result)[1].tobytes()
    return send_file(BytesIO(png), mimetype="image/png")
```

---

## 4. สรุปตาราง API Endpoints และ Error Codes ทั้งหมด

### 4.1 ตาราง API Endpoints
| HTTP Method | API Path | Token? | Request Format | Response Type | คำอธิบายหน้าที่ |
| :---: | :--- | :---: | :---: | :---: | :--- |
| `POST` | `/api/v1/register` | ❌ | `application/json` | `application/json` | สมัครสมาชิกผู้ใช้ใหม่ (ตรวจอีเมลซ้ำ, แฮชรหัสผ่าน) |
| `POST` | `/api/v1/login` | ❌ | `application/json` | `application/json` | ตรวจสอบรหัสผ่าน และออกบัตร JWT Access Token (24 ชม.) |
| `GET` | `/api/v1/profile` | 🔒 มี | Header Bearer | `application/json` | ดึงข้อมูลส่วนตัว และสรุปสถิติจำนวนภาพที่สร้าง |
| `GET` | `/api/v1/models` | ❌ | ไม่มี | `application/json` | ดึงรายชื่อ AI Checkpoints จากเครื่อง GPU Server |
| `POST` | `/api/v1/estimate` | ❌ | `application/json` | `application/json` | คำนวณเวลาประเมินล่วงหน้าในการสร้างภาพ |
| `POST` | `/api/v1/generate` | 🔒 มี | `application/json` | `application/json` | สั่งสร้างรูปภาพ AI (เข้าคิว Mutex GPU Lock) |
| `GET` | `/api/v1/images/:id` | 🔒 มี | Header Bearer | `image/png` | สตรีมไฟล์ภาพ PNG (ตรวจสิทธิ์เจ้าของ ป้องกัน IDOR) |
| `GET` | `/api/v1/history` | 🔒 มี | Query Params | `application/json` | ดึงประวัติภาพ (รองรับ Pagination แบ่งหน้า และ Filter) |
| `GET` | `/api/v1/history/:id` | 🔒 มี | Header Bearer | `application/json` | ดึงรายละเอียดพารามิเตอร์เต็มของภาพ |
| `DELETE` | `/api/v1/history/:id` | 🔒 มี | Header Bearer | `application/json` | ลบประวัติและข้อมูลรูปภาพของตนเองออกจากระบบ |
| `POST` | `/api/v1/process/spot-blur` | 🔒 มี | `multipart/form-data` | `image/png` | เบลอเฉพาะจุดตามพิกัดวงกลม (Feathered Soft Edges) |
| `POST` | `/api/v1/process/gesture` | 🔒 มี | `multipart/form-data` | `application/json` | ตรวจจับท่าทางมือ 7 ท่าจากภาพถ่ายนิ่ง (MediaPipe 21 จุด) |
| `POST` | `/api/v1/process/gesture/frame` | 🔒 มี | `multipart/form-data` | `application/json` | ตรวจจับท่าทางมือจากสตรีม Webcam (แยก Session ต่อคน) |
| `POST` | `/api/v1/process/gesture/stop` | 🔒 มี | ไม่มี | `application/json` | ปิดกล้องเว็บแคม และทำลาย Recognizer เพื่อคืน Memory |
| `POST` | `/api/v1/process/remove-bg` | 🔒 มี | `multipart/form-data` | `image/png` | ตัดพื้นหลังบุคคลแบบไฮบริด (AI + GrabCut + แปรงแต้ม) |

---

### 4.2 ตาราง Error Codes
| รหัสข้อผิดพลาด | HTTP Status | คำอธิบายภาษาคน |
| :--- | :---: | :--- |
| `VALIDATION_ERROR` | `400` | ข้อมูลที่ส่งมาไม่ถูกต้อง (เช่น อีเมลผิดฟอร์แมต, รหัสผ่านสั้นเกินไป, ตัวเลขติดลบ) |
| `INVALID_CREDENTIALS` | `401` | อีเมลหรือรหัสผ่านไม่ถูกต้อง |
| `UNAUTHORIZED` | `401` | ไม่ได้แนบ Token, Token หมดอายุแล้ว หรือลายเซ็นถูกปลอมแปลง |
| `EMAIL_EXISTS` | `409` | อีเมลนี้มีคนใช้ลงทะเบียนไปแล้ว |
| `GENERATION_NOT_FOUND` | `404` | ไม่พบรูปภาพในระบบ หรือพยายามแอบเปิดดูรูปของคนอื่น (IDOR) |
| `IMAGE_NOT_FOUND` | `404` | ไม่พบข้อมูลไฟล์ไบนารีของรูปภาพในฐานข้อมูล |
| `INVALID_IMAGE` | `400` | ไฟล์รูปภาพเสียหาย ไม่สามารถเปิดอ่านด้วย OpenCV ได้ |
| `UNSUPPORTED_FILE_TYPE` | `415` | นามสกุลไฟล์ไม่ถูกต้อง (ระบบรองรับเฉพาะ .jpg, .jpeg, .png, .webp) |
| `MODEL_UNAVAILABLE` | `503` | ไฟล์โมเดล AI ในเครื่องยังไม่พร้อมใช้งาน หรือดาวน์โหลดไม่สำเร็จ |
| `GENERATION_FAILED` | `500` | การประมวลผลคำนวณภาพขัดข้อง |
| `AI_SERVER_BUSY` | `409` | คิวงานบนเครื่อง AI Server แน่นเกินไป และรอนานเกิน 120 วินาที |
| `AI_SERVER_TIMEOUT` | `504` | AI Server ใช้เวลาเจนภาพนานเกินกำหนด (เกิน 75 วินาที) |
| `AI_SERVER_ERROR` | `503` | ไม่สามารถติดต่อเชื่อมต่อไปยังเครื่อง AI Server ได้ (เครื่องอาจจะปิดอยู่) |
| `INTERNAL_SERVER_ERROR` | `500` | เกิดข้อผิดพลาดที่ไม่คาดคิดภายในเซิร์ฟเวอร์ Backend |

---

## 5. คลังเก็งคำถาม-คำตอบ สำหรับสอบพรีเซนต์ (Defense Q&A Cheat Sheet)

#### Q1: "ทำไมถึงเลือกเก็บรูปภาพเป็น BLOB ใน SQLite ทำไมไม่เซฟเป็นไฟล์ลงในโฟลเดอร์ปกติ (Disk Storage)?"
* **แนวทางการตอบ:**  
  *"การจัดเก็บเป็น BLOB ในฐานข้อมูลมีข้อดี 3 ประการสำหรับระบบนี้ครับ:  
  1. **ความง่ายในการสำรองข้อมูลและการพอร์ตระบบ (Portability):** ข้อมูลรูปภาพทั้งหมดผูกอยู่กับฐานข้อมูลไฟล์เดียว `database.db` ย้ายไปรันที่ไหนภาพก็ไม่สูญหาย ไม่ต้องกังวลเรื่อง Path รูปภาพเพี้ยน  
  2. **ความสอดคล้องของข้อมูล (Transaction Consistency):** การลบผู้ใช้ (Cascade Delete) หรือลบประวัติ จะลบภาพออกจากฐานข้อมูลทันที ไม่มีปัญหาไฟล์ภาพขยะค้างเติ่งอยู่ในโฟลเดอร์ดิสก์  
  3. **การควบคุมความปลอดภัย (Access Control):** ป้องกันไม่ให้ใครเปิดดูภาพได้โดยตรงผ่าน Web Server static link ทุกการร้องขอรูปภาพต้องผ่านมิดเดิลแวร์ `@token_required` ตรวจสอบความเป็นเจ้าของก่อนเสมอครับ"*

#### Q2: "ถ้ามีคนกดสั่งสร้างภาพ AI พร้อมกัน 10 คน ระบบจะไม่ล่มเหรอ?"
* **แนวทางการตอบ:**  
  *"ไม่ล่มครับ เพราะเราวางระบบ **Concurrency Queue** โดยใช้ **`threading.Lock()` (Mutex Lock)** ไว้ใน `services/ai_client.py`:  
  * คำขอแรกจะได้สิทธิ์เข้าใช้งาน GPU ทันที ส่วนอีก 9 คนจะเข้าสู่คิวรออย่างเป็นระเบียบ  
  * การ์ดจอ GPU จะประมวลผลทีละ 1 งานอย่างปลอดภัย จึงไม่เกิดปัญหาหน่วยความจำเต็ม (**CUDA Out of Memory**)  
  * และเรามีระบบคำนวณเวลารอคิวส่งกลับไปให้หน้าเว็บ ทำให้ผู้ใช้เห็นสถานะนับถอยหลังอย่างชัดเจน ไม่สับสนครับ"*

#### Q3: "ระบบป้องกันไม่ให้คนอื่นแอบดูรูปภาพของเรายังไง (IDOR Protection)?"
* **แนวทางการตอบ:**  
  *"เราป้องกันด้วยเทคนิค **Anti-Hopping / IDOR Check** ครับ โดยใน Endpoint `GET /api/v1/images/<id>` มิดเดิลแวร์ `@token_required` จะถอดรหัส `user_id` ของคนที่ล็อกอินอยู่เสมอ จากนั้นคำสั่ง SQL จะค้นหาด้วยเงื่อนไขคู่:  
  `WHERE id = :id AND user_id = request.user_id`  
  ดังนั้น ต่อให้มีคนพยายามเดาสุ่มเลขรูปภาพของผู้อื่น ระบบจะหาไม่พบและตอบกลับ `404 Not Found` ทันทีครับ"*

#### Q4: "ทำไมใน Gesture Recognition ถึงต้องแยก Session ต่อผู้ใช้ในโหมดเว็บแคม?"
* **แนวทางการตอบ:**  
  *"เพราะโมเดลของ MediaPipe ในโหมด `RunningMode.VIDEO` ถูกออกแบบมาให้ **'จดจำตำแหน่งมือของเฟรมก่อนหน้า' (Tracking State)** เพื่อให้การประมวลผลเฟรมถัดไปทำได้รวดเร็วและมือนิ่งไม่กระตุกครับ ถ้าเราใช้ตัว Recognizer ตัวเดียวกันแชร์ข้ามคน มือของผู้ใช้ A จะไปกระตุกปนกับผู้ใช้ B ทันที เราจึงต้องสร้าง Dict `_sessions[user_id]` แยกห้องให้แต่ละคน และมีระบบตัดทำลายห้องอัตโนมัติหากหยุดใช้เกิน 60 วินาทีเพื่อคืนหน่วยความจำครับ"*

#### Q5: "ทำไมต้องย่อรูปเป็นขนาด 900px ก่อนตัดพื้นหลังด้วย GrabCut?"
* **แนวทางการตอบ:**  
  *"เพราะอัลกอริทึม GrabCut มีความซับซ้อนในการคำนวณกราฟสี (Graph Cut Optimization) สูงมาก หากเราใช้ภาพขนาดต้นฉบับ เช่น 12 ล้านพิกเซล เซิร์ฟเวอร์จะใช้เวลาคำนวณนานถึง 5-10 วินาทีและกิน CPU มหาศาลครับ การย่อด้านยาวลงมาที่ `WORK_SIDE = 900px` ทำให้คำนวณเสร็จในเสี้ยววินาที (~0.2 วินาที) แล้วเราค่อยนำ Mask ขยายสัดส่วนกลับไปเป็นขนาดจริง พร้อมทำ Gaussian Feathering ที่ขอบ จึงได้ทั้งความเร็วระดับเรียลไทม์และความคมชัดของภาพขนาดเต็มครับ"*
