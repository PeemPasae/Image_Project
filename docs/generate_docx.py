import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_table_styled(doc, headers, data, col_widths=None):
    all_data = [headers] + data
    table = doc.add_table(rows=len(all_data), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    for row_idx, row in enumerate(all_data):
        for col_idx, text in enumerate(row):
            cell = table.cell(row_idx, col_idx)
            cell.text = str(text)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            run = p.runs[0]
            run.font.name = 'Cordia New'
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            if row_idx == 0:
                run.bold = True
                run.font.size = Pt(14)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                set_cell_background(cell, "1F4E79")
            else:
                run.font.size = Pt(13)
                if col_idx == 0:
                    run.bold = True
                if row_idx % 2 == 0:
                    set_cell_background(cell, "FAFAFA")
                else:
                    set_cell_background(cell, "FFFFFF")

    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    return table

def add_heading_1(doc, text):
    h = doc.add_heading(level=1)
    r = h.add_run(text)
    r.font.name = 'Cordia New'
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    return h

def add_heading_2(doc, text):
    h = doc.add_heading(level=2)
    r = h.add_run(text)
    r.font.name = 'Cordia New'
    r.font.size = Pt(16)
    r.bold = True
    r.font.color.rgb = RGBColor(0x2F, 0x55, 0x97)
    return h

def add_heading_3(doc, text):
    h = doc.add_heading(level=3)
    r = h.add_run(text)
    r.font.name = 'Cordia New'
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return h

def add_code_block(doc, code_str):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F5F7")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    cell.width = Inches(6.5)
    
    lines = code_str.strip().split('\n')
    for i, line in enumerate(lines):
        if i == 0:
            p = cell.paragraphs[0]
        else:
            p = cell.add_paragraph()
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line)
        r.font.name = 'Consolas'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0x24, 0x29, 0x2E)
    doc.add_paragraph()

def add_box(doc, title, text, bg_hex="EBF3FB", title_color=RGBColor(0x1F, 0x4E, 0x79)):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    cell.width = Inches(6.5)
    
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    if title:
        r_title = p.add_run(f"{title}\n")
        r_title.bold = True
        r_title.font.name = 'Cordia New'
        r_title.font.size = Pt(14)
        r_title.font.color.rgb = title_color
    
    r_text = p.add_run(text)
    r_text.font.name = 'Cordia New'
    r_text.font.size = Pt(13)
    r_text.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    doc.add_paragraph()

def generate_backend_master_report():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Cordia New'
    font.size = Pt(14)
    font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # Title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = t.add_run("เอกสารสรุปโครงสร้างและคู่มือรีวิวโค้ดระบบ Backend (ฉบับจบในไฟล์เดียว)\nLUMA AI & Computer Vision Architecture Master Review")
    rt.font.name = 'Cordia New'
    rt.font.size = Pt(22)
    rt.bold = True
    rt.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    doc.add_paragraph()

    # 1. บทนำและบทพูดสรุปสำหรับพรีเซนต์
    add_heading_1(doc, "1. บทนำและบทพูดสรุปสำหรับพรีเซนต์ 1 นาที (Elevator Pitch)")
    add_box(doc, "🗣️ สคริปต์บทพูดพรีเซนต์เปิดตัว (แนะนำให้ใช้พูดตอนเริ่ม):",
            "\"ระบบ Backend ของ LUMA ถูกออกแบบขึ้นมาเพื่อทำหน้าที่เป็นศูนย์กลางเชื่อมประสานระหว่าง 3 ส่วนหลักครับ:\n"
            "1. ส่วนหน้าบ้าน (Frontend): สื่อสารผ่าน REST API ภายใต้การควบคุมความปลอดภัยด้วย JWT Authentication และระบบป้องกัน IDOR\n"
            "2. ส่วนประมวลผล AI หนัก (Stable Diffusion Server): ควบคุมการส่งงานเข้า GPU ผ่านระบบ Mutex Concurrency Lock ป้องกันการ์ดจอ Out of Memory พร้อมมีระบบคำนวณเวลาประเมินล่วงหน้า\n"
            "3. ส่วนประมวลผลภาพเร็ว (Edge Image Processing): ฟังก์ชัน Spot Blur, Gesture Recognition 7 ท่าทาง และ Hybrid Background Removal พัฒนาด้วย OpenCV/MediaPipe ทำงานบน Backend เสร็จไวทันที ไม่ต้องต่อคิวเตาอบ GPU\n"
            "นอกจากนี้ ฐานข้อมูล SQLite ยังมีระบบ Auto Schema Migration ตรวจสอบและอัปเดตคอลัมน์ให้อัตโนมัติเมื่อเริ่มระบบครับ\"",
            bg_hex="F2F7FA")

    # 2. แผนภาพสถาปัตยกรรม
    add_heading_1(doc, "2. ภาพรวมสถาปัตยกรรมระบบ (System Architecture Overview)")
    add_box(doc, "💡 คอนเซปต์เปรียบเหมือน 'ร้านอาหารอัจฉริยะ':",
            "1. Nginx Reverse Proxy (พนักงานต้อนรับหน้าร้าน): รับคำขอจากลูกค้าหน้าเว็บ แล้วส่งต่อเข้าครัว\n"
            "2. Flask Backend (หัวหน้าเชฟ): รับออร์เดอร์ ตรวจสอบบัตรสมาชิก (JWT) แล้วจ่ายงานให้แผนกต่าง ๆ\n"
            "3. AI GPU Server (เตาอบใหญ่): อบอาหารจานหลักคือภาพ AI Stable Diffusion ซึ่งกินพลังการ์ดจอสูง\n"
            "4. Image Processing (แผนกตกแต่งจานด่วน): ใช้ OpenCV/MediaPipe ตัดพื้นหลัง จับท่ามือ เสร็จไวบน Backend\n"
            "5. SQLite Database (ห้องคลังเสบียง): จัดเก็บข้อมูลสมาชิกและรูปภาพเป็นก้อนไบนารีอย่างปลอดภัย")

    doc.add_paragraph()

    # 3. เจาะลึกรีวิวโค้ดทีละบรรทัด
    add_heading_1(doc, "3. เจาะลึกรีวิวโค้ดทีละบรรทัด (Line-by-Line Code Review)")

    # 3.1 run.py
    add_heading_2(doc, "3.1 backend/run.py - จุดเริ่มต้นเซิร์ฟเวอร์")
    add_box(doc, "คำอธิบายภาษาคน:", "รับหน้าที่สตาร์ตเครื่อง ดึงพอร์ตจาก .env และที่สำคัญคือ host='0.0.0.0' เพื่อเปิดรับการเชื่อมต่อจาก Nginx หรืออุปกรณ์ภายนอกในวงแลน")
    code_run = """if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8") # ป้องกันภาษาไทยเพี้ยนบนคอนโซล Windows

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # host='0.0.0.0' สั่งให้เปิดรับ Request จากทุก IP (เช่น เครื่อง Nginx ข้ามเครื่อง)
    app.run(host="0.0.0.0", port=port, debug=True)"""
    add_code_block(doc, code_run)

    # 3.2 __init__.py
    add_heading_2(doc, "3.2 backend/app/__init__.py - Application Factory & Auto-Migration")
    add_box(doc, "คำอธิบายภาษาคน:", "โรงงานประกอบร่าง Flask App และมีระบบ 'ตรวจและซ่อมบ้านอัตโนมัติ' ตรวจสอบตาราง SQLite ทุกครั้งตอนเปิดแอป ถ้าคอลัมน์ไหนยังไม่มี จะรัน ALTER TABLE เพิ่มให้อัตโนมัติ!")
    code_init = """def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=Config.CORS_ORIGINS) # อนุญาตให้ข้าม Domain มาคุยได้
    db.init_app(app)

    # ลงทะเบียน 5 Blueprints หลัก
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(profile_bp, url_prefix="/api/v1")
    app.register_blueprint(sd_bp, url_prefix="/api/v1")
    app.register_blueprint(history_bp, url_prefix="/api/v1")
    app.register_blueprint(process_bp, url_prefix="/api/v1")

    # ตรวจสอบโครงสร้างคอลัมน์อัตโนมัติ (Auto Schema Migration)
    with app.app_context():
        db.create_all()
        inspector = db.inspect(db.engine)
        existing = {col["name"] for col in inspector.get_columns("generations")}
        migrations = [
            ("image_data", "ALTER TABLE generations ADD COLUMN image_data BLOB"),
            ("category", "ALTER TABLE generations ADD COLUMN category VARCHAR(50) DEFAULT 'sd_generate'"),
            ("params", "ALTER TABLE generations ADD COLUMN params TEXT DEFAULT '{}'"),
        ]
        for col_name, sql_stmt in migrations:
            if col_name not in existing:
                db.session.execute(db.text(sql_stmt))
        db.session.commit()
    return app"""
    add_code_block(doc, code_init)

    # 3.3 jwt_auth.py & sd.py
    add_heading_2(doc, "3.3 backend/app/middleware/jwt_auth.py - ยามตรวจบัตร และระบบป้องกัน IDOR")
    add_box(doc, "คำอธิบายภาษาคน:", "ยามตรวจบัตร VIP (@token_required) จะแกะบัตร JWT สกัด user_id แปะไว้ใน request และตอนดึงรูปภาพจะค้นหาคู่เสมอ (id = :id AND user_id = request.user_id) ป้องกันไม่ให้ใครเดาเลขแอบดูรูปคนอื่นได้")
    code_jwt = """def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return error_response(UNAUTHORIZED, "Missing or invalid token", 401)
        token = auth_header.split()[1]
        try:
            payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            request.user_id = payload.get("user_id") # สกัด user_id ไว้ใช้งานต่อ
        except jwt.ExpiredSignatureError:
            return error_response(UNAUTHORIZED, "Token expired", 401)
        return f(*args, **kwargs)
    return decorated

# โค้ดป้องกัน IDOR ใน sd.py
@sd_bp.route("/images/<int:id>", methods=["GET"])
@token_required
def get_image(id):
    # ต้องตรงทั้ง ID ภาพ และ user_id ของเจ้าของเท่านั้น!
    gen = Generation.query.filter_by(id=id, user_id=request.user_id).first()
    if not gen or not gen.image_data:
        return error_response(GENERATION_NOT_FOUND, "Image not found", 404)
    return send_file(io.BytesIO(gen.image_data), mimetype="image/png")"""
    add_code_block(doc, code_jwt)

    # 3.4 ai_client.py
    add_heading_2(doc, "3.4 backend/app/services/ai_client.py - คิวการ์ดจอ Mutex GPU Lock")
    add_box(doc, "คำอธิบายภาษาคน:", "เหมือนห้องน้ำที่เข้าได้ทีละคนและต้องลงกลอนประตู (_gpu_lock) เพื่อป้องกันการ์ดจอหน่วยความจำเต็ม (CUDA Out of Memory) เมื่องานเสร็จสั่ง _gpu_lock.release() ปลดกลอนให้คิวถัดไปทำต่อ")
    code_ai = """_gpu_lock = threading.Lock() # ประตูกลอนล็อก GPU

def generate_sd_image(payload: dict) -> tuple:
    # 1. ยืนรอคิวขอสิทธิ์ใช้งาน GPU (รอได้สูงสุด 120 วินาที)
    lock_acquired = _gpu_lock.acquire(blocking=True, timeout=120)
    if not lock_acquired:
        raise AIServerBusyException("GPU Server is busy.")

    try:
        # 2. ส่งงานเข้า GPU ปลอดภัยคนเดียวในเวลานั้น
        response = requests.post(f"{server_url}/sdapi/v1/txt2img", json=payload, timeout=75)
        base64_image = response.json()["images"][0]
        return base64_image
    finally:
        # 3. ปลดล็อกประตูเสมอ ให้คิวถัดไปได้ทำต่อ!
        _gpu_lock.release()"""
    add_code_block(doc, code_ai)

    # 3.5 spot_blur.py
    add_heading_2(doc, "3.5 backend/app/services/image_filters/spot_blur.py - เบลอเฉพาะจุด")
    add_box(doc, "คำอธิบายภาษาคน:", "เบลอทั้งภาพรอไว้ -> สร้างแผ่น Mask ดำมืดแล้ววาดวงกลมสีขาว -> ทำ Gaussian Blur ที่ตัว Mask เพื่อให้ขอบเนียนนุ่มฟุ้ง -> รวมภาพด้วย Alpha Blending")
    code_blur = """def spot_blur(img, circles, strength=10, soft=True):
    k = strength * 2 + 1
    blurred = cv2.GaussianBlur(img, (k, k), 0) # 1. เบลอภาพรอไว้

    mask = np.zeros(img.shape[:2], np.float32) # 2. แผ่นดำมืด
    for x, y, r in circles:
        cv2.circle(mask, (int(x), int(y)), int(r), 1.0, -1) # วาดวงกลมขาว

    if soft and circles:
        edge = int(max(r for _, _, r in circles) * 0.5) * 2 + 1
        mask = cv2.GaussianBlur(mask, (edge, edge), 0) # 3. เกลี่ยขอบนุ่ม

    mask = mask[:, :, None]
    out = img * (1 - mask) + blurred * mask # 4. รวมภาพ
    return out.astype(np.uint8)"""
    add_code_block(doc, code_blur)

    # 3.6 gesture.py
    add_heading_2(doc, "3.6 backend/app/services/image_filters/gesture.py - ตรวจจับท่าทางมือ MediaPipe")
    add_box(doc, "คำอธิบายภาษาคน:", "AI ตรวจจับข้อนิ้ว 21 จุด รู้ 7 ท่าทางมาตรฐาน โหมดเว็บแคมแยก Session ต่อคน เพื่อจำตำแหน่งมือข้ามเฟรม มือนิ่งไม่กระตุก และมีระบบคืนแรมทันทีถ้าทิ้งกล้องเกิน 60 วิ")
    code_gesture = """def recognize_gesture_frame(img, user_id, num_hands=2, min_confidence=0.5):
    mp_image = _to_mp_image(img) # BGR -> RGB
    key = (num_hands, round(min_confidence, 1))

    with _video_lock:
        _close_idle_sessions(time.monotonic()) # คืนแรมหากไม่ได้ใช้นานเกิน 60 วิ
        session = _sessions.get(user_id)
        if session is None or session["key"] != key:
            session = {"key": key, "recognizer": _create_recognizer(vision.RunningMode.VIDEO, *key), "last_ts": 0}
            _sessions[user_id] = session

        timestamp_ms = max(session["last_ts"] + 1, int(time.monotonic() * 1000))
        session["last_ts"] = timestamp_ms

        result = session["recognizer"].recognize_for_video(mp_image, timestamp_ms)
    return _format(result, inference_ms)"""
    add_code_block(doc, code_gesture)

    # 3.7 remove_bg.py
    add_heading_2(doc, "3.7 backend/app/services/image_filters/remove_bg.py - ตัดพื้นหลังไฮบริด")
    add_box(doc, "คำอธิบายภาษาคน:", "ย่อภาพเหลือด้านยาว 900px เพื่อรัน GrabCut ได้เร็วใน 0.2 วินาที -> รวมพลัง AI + แปรงแต้ม Keep/Remove ของผู้ใช้ -> ใช้สูตร Color Decontamination ถอนสีสะท้อนของฉากหลังเดิมออก ขอบผมจึงไม่เรืองแสง")
    code_rm_bg = """def remove_background(img, rect=None, strokes=None, use_ai=True, bg_color=None):
    # 1. ย่อรูปเหลือ 900px เพื่อความเร็วจัด
    s = min(1.0, WORK_SIDE / max(H, W))
    small = cv2.resize(img, (round(W * s), round(H * s))) if s < 1 else img

    # 2. AI หาคน + 3. รวมร่าง GrabCut ตัดขอบผม
    person = _person_prob(small) if use_ai else None
    alpha_small = _cut(small, person, small_rect, small_strokes)

    # 4. ถอนสีสะท้อนเดิม (Matting): F = (I - (1 - a) * B_old) / a
    alpha = cv2.resize(alpha_small, (W, H))
    bg_old = cv2.resize(bg_small, (W, H))
    F = np.clip((I - (1 - a) * bg_old) / np.maximum(a, 0.15), 0, 255)

    return np.dstack([F, alpha * 255]).astype(np.uint8) if bg_color is None else out"""
    add_code_block(doc, code_rm_bg)

    # 4. ตาราง API
    add_heading_1(doc, "4. สรุปรายการ API Endpoints และ Error Codes ทั้งหมด")
    api_data = [
        ("POST", "/api/v1/register", "ไม่จำเป็น", "สมัครสมาชิกผู้ใช้ใหม่ (แฮชรหัสผ่าน ป้องกันอีเมลซ้ำ)"),
        ("POST", "/api/v1/login", "ไม่จำเป็น", "เข้าสู่ระบบ ตรวจสอบรหัสผ่าน และรับบัตร JWT Token 24 ชม."),
        ("GET", "/api/v1/profile", "ต้องมี", "ดึงข้อมูลโปรไฟล์และสรุปสถิติจำนวนภาพที่สร้างทั้งหมด"),
        ("GET", "/api/v1/models", "ไม่จำเป็น", "ดึงรายชื่อ Checkpoint Models ทั้งหมดจาก AI Server"),
        ("POST", "/api/v1/estimate", "ไม่จำเป็น", "คำนวณเวลาประเมินล่วงหน้าในการสร้างภาพ"),
        ("POST", "/api/v1/generate", "ต้องมี", "สั่งสร้างรูปภาพ AI (เข้าคิว GPU Mutex Lock)"),
        ("GET", "/api/v1/images/:id", "ต้องมี", "สตรีมไฟล์รูปภาพ Binary PNG (จำกัดสิทธิ์เฉพาะเจ้าของ ป้องกัน IDOR)"),
        ("GET", "/api/v1/history", "ต้องมี", "ดึงรายการประวัติภาพพร้อม Pagination และ Filter"),
        ("GET", "/api/v1/history/:id", "ต้องมี", "ดึงรายละเอียดพารามิเตอร์เต็มของภาพ"),
        ("DELETE", "/api/v1/history/:id", "ต้องมี", "ลบประวัติรูปภาพของตนเองออกจากระบบ"),
        ("POST", "/api/v1/process/spot-blur", "ต้องมี", "เบลอเฉพาะจุดตามพิกัดวงกลม (Feathered Soft Edges)"),
        ("POST", "/api/v1/process/gesture", "ต้องมี", "ตรวจจับท่าทางมือ 7 ท่าจากภาพนิ่ง (MediaPipe 21 จุด)"),
        ("POST", "/api/v1/process/gesture/frame", "ต้องมี", "ตรวจจับท่าทางมือจากสตรีม Webcam (แยก Session ต่อคน)"),
        ("POST", "/api/v1/process/gesture/stop", "ต้องมี", "ปิดกล้องเว็บแคม และทำลาย Recognizer เพื่อคืน Memory"),
        ("POST", "/api/v1/process/remove-bg", "ต้องมี", "ตัดพื้นหลังบุคคลแบบไฮบริด (AI + GrabCut + แปรงแต้ม)")
    ]
    create_table_styled(doc, ["Method", "Endpoint Path", "Token?", "คำอธิบายหน้าที่การทำงาน"], api_data, [0.8, 2.0, 0.8, 2.8])

    doc.add_paragraph()

    # 5. คลังคำถาม-คำตอบ สำหรับเตรียมสอบ
    add_heading_1(doc, "5. คลังเก็งคำถาม-คำตอบ สำหรับสอบพรีเซนต์ (Defense Q&A Cheat Sheet)")

    qa_list = [
        ("Q1: ทำไมถึงเลือกเก็บรูปภาพเป็น BLOB ใน SQLite ทำไมไม่เซฟเป็นไฟล์ลงดิสก์?",
         "ตอบ: 1. ความสะดวกในการสำรองข้อมูล ย้ายไฟล์ database.db ไฟล์เดียวภาพติดไปด้วยครบ\n"
         "2. ความสมบูรณ์ของข้อมูล การสั่งลบ User (Cascade Delete) ภาพจะหายไปด้วยทันที ไม่มีไฟล์ขยะตกค้างในเครื่อง\n"
         "3. การควบคุมความปลอดภัย ทุกการเปิดดูรูปภาพต้องผ่าน @token_required ตรวจสอบความเป็นเจ้าของก่อนเสมอ"),
        ("Q2: ถ้ามีคนกดสั่งสร้างภาพ AI พร้อมกัน 10 คน ระบบจะไม่ล่มเหรอ?",
         "ตอบ: ไม่ล่มครับ เพราะเราใช้ Mutex Lock (threading.Lock()) ใน ai_client.py คำขอแรกจะได้เข้าใช้ GPU ทันที ส่วนอีก 9 คนจะเข้าคิวรออย่างเป็นระเบียบ การ์ดจอ GPU ประมวลผลทีละ 1 งานอย่างปลอดภัย จึงไม่เกิดปัญหา CUDA Out of Memory พร้อมมีระบบคำนวณเวลารอคิวแสดงบนหน้าเว็บครับ"),
        ("Q3: ระบบป้องกันไม่ให้คนอื่นแอบดูรูปภาพของเรายังไง (IDOR)?",
         "ตอบ: เราใช้เทคนิค Anti-Hopping / IDOR Check ใน Endpoint GET /images/:id โดยมิดเดิลแวร์ @token_required จะถอดรหัส user_id ของคนที่ล็อกอินอยู่เสมอ และคำสั่ง SQL จะค้นหาด้วยเงื่อนไขคู่: WHERE id = :id AND user_id = request.user_id ดังนั้น ต่อให้มีคนสุ่มเลข ID รูปของคนอื่น ระบบจะหาไม่พบและตอบกลับ 404 ทันทีครับ"),
        ("Q4: ทำไมใน Gesture Recognition ถึงต้องแยก Session ต่อผู้ใช้ในโหมดเว็บแคม?",
         "ตอบ: เพราะโมเดล MediaPipe ในโหมด VIDEO มีการจดจำตำแหน่งมือของเฟรมก่อนหน้า (Tracking State) เพื่อให้การติดตามมือนิ่งและเร็วขึ้น ถ้าใช้ตัวเดียวกันแชร์ข้ามคน มือของผู้ใช้ A จะไปกระตุกใส่นาย B ทันที เราจึงแยกห้อง _sessions[user_id] ให้แต่ละคน และมีระบบทำลายห้องอัตโนมัติหากหยุดใช้เกิน 60 วินาทีเพื่อคืนหน่วยความจำครับ"),
        ("Q5: ทำไมต้องย่อรูปเหลือ 900px ก่อนตัดพื้นหลังด้วย GrabCut?",
         "ตอบ: เพราะอัลกอริทึม GrabCut มีความซับซ้อนในการคำนวณกราฟสีสูงมาก หากใช้รูปขนาด 12 ล้านพิกเซล เซิร์ฟเวอร์จะค้างนานถึง 5-10 วินาที การย่อเหลือ 900px ทำให้คำนวณเสร็จในเสี้ยววินาที (~0.2 วินาที) แล้วเราค่อยนำ Mask ขยายสัดส่วนกลับไปเป็นขนาดจริง พร้อมทำ Gaussian Feathering ที่ขอบ จึงได้ทั้งความเร็วและภาพที่คมชัดครับ")
    ]

    for q, a in qa_list:
        add_box(doc, q, a, bg_hex="FDFEFE")

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(output_dir, "BACKEND_REPORT.docx")
    try:
        doc.save(output_path)
        print(f"Successfully generated Master DOCX at: {output_path}")
    except PermissionError:
        alt_path = os.path.join(output_dir, "BACKEND_MASTER_REPORT.docx")
        doc.save(alt_path)
        print(f"Notice: BACKEND_REPORT.docx was locked by Word. Saved to: {alt_path}")

if __name__ == "__main__":
    generate_backend_master_report()

