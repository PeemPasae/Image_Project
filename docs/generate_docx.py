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


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
    )
    tcPr.append(tcMar)


def setup_document_styles(doc):
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    style = doc.styles["Normal"]
    font = style.font
    font.name = "Cordia New"
    font.size = Pt(14)
    font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def add_heading_1(doc, text):
    h = doc.add_heading(level=1)
    r = h.add_run(text)
    r.font.name = "Cordia New"
    r.font.size = Pt(18)
    r.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    return h


def add_heading_2(doc, text):
    h = doc.add_heading(level=2)
    r = h.add_run(text)
    r.font.name = "Cordia New"
    r.font.size = Pt(16)
    r.bold = True
    r.font.color.rgb = RGBColor(0x2F, 0x55, 0x97)
    return h


def add_heading_3(doc, text):
    h = doc.add_heading(level=3)
    r = h.add_run(text)
    r.font.name = "Cordia New"
    r.font.size = Pt(14)
    r.bold = True
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return h


def add_bullet(doc, bold_prefix, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = "Cordia New"
        r_bold.font.size = Pt(14)
        r_bold.bold = True
    r_text = p.add_run(text)
    r_text.font.name = "Cordia New"
    r_text.font.size = Pt(14)
    return p


def render_table(doc, headers, rows_data, col_widths=None):
    table = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h_text
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.15
        run = p.runs[0]
        run.font.name = "Cordia New"
        run.font.size = Pt(14)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_background(cell, "1F4E79")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

    # Data Rows
    for row_idx, row_values in enumerate(rows_data):
        for col_idx, val in enumerate(row_values):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(val)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            run = p.runs[0]
            run.font.name = "Cordia New"
            run.font.size = Pt(13)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            if col_idx == 0:
                run.bold = True
            if row_idx % 2 == 1:
                set_cell_background(cell, "F7F9FB")

    # Set Widths if specified
    if col_widths:
        for row in table.rows:
            for c_idx, width in enumerate(col_widths):
                if c_idx < len(row.cells):
                    row.cells[c_idx].width = width

    doc.add_paragraph()
    return table


# ==============================================================================
# 1. GENERATE BACKEND REPORT DOCX
# ==============================================================================
def generate_backend_report(output_dir):
    doc = Document()
    setup_document_styles(doc)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title.add_run("รายงานโครงสร้างและการทำงานของระบบ Backend\n(LUMA AI System Architecture & Data Flow Report)")
    run_title.font.name = "Cordia New"
    run_title.font.size = Pt(22)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    doc.add_paragraph()

    # Section 1
    add_heading_1(doc, "1. ภาพรวมสถาปัตยกรรมระบบ (System Architecture Overview)")
    p = doc.add_paragraph(
        "ระบบ Backend ของโปรเจกต์ LUMA พัฒนาด้วยภาษา Python (Flask Framework) ออกแบบตามหลักสถาปัตยกรรม "
        "Application Factory Pattern และแบ่งแยกโมดูลการทำงานด้วย Flask Blueprints เพื่อความเป็นระเบียบ ความปลอดภัย และความสามารถในการขยายระบบในอนาคต"
    )
    p.paragraph_format.line_spacing = 1.15

    add_bullet(doc, "Frontend Integration: ", "เชื่อมต่อกับ Frontend (React / Vite) ผ่าน REST API และส่งผลลัพธ์ผ่าน JSON Envelope มาตรฐาน")
    add_bullet(doc, "Authentication & Security: ", "ควบคุมสิทธิ์ด้วย JSON Web Token (JWT HS256, อายุ 24 ชม.), การแฮชรหัสผ่าน PBKDF2/SHA256, และระบบป้องกัน IDOR")
    add_bullet(doc, "Database Storage: ", "ใช้ SQLite (database/database.db) ผ่าน Flask-SQLAlchemy จัดเก็บรูปภาพเป็น Binary BLOB และมี Auto Schema Migration ตรวจสอบคอลัมน์อัตโนมัติ")
    add_bullet(doc, "Stable Diffusion Integration: ", "เชื่อมต่อ AI Server ด้วย Concurrency Queue (threading.Lock Mutex) ป้องกันงานชนกันบนการ์ดจอ")
    add_bullet(doc, "Edge Image Processing: ", "แยกฟังก์ชันประมวลผลภาพเฉพาะทาง (Spot Blur, Gesture Recognition, Background Removal) มารันบนเซิร์ฟเวอร์ Backend โดยตรงด้วย OpenCV และ MediaPipe")

    doc.add_paragraph()

    # Section 2
    add_heading_1(doc, "2. หน้าที่และความรับผิดชอบของแต่ละไฟล์ในระบบ Backend")
    file_headers = ["โฟลเดอร์ / ชื่อไฟล์", "หน้าที่และความรับผิดชอบหลัก"]
    file_rows = [
        ("backend/run.py", "จุดเริ่มต้นรันเซิร์ฟเวอร์ (Entry Point) กำหนดพอร์ต (PORT=5000) และเปิดบริการบน 0.0.0.0"),
        ("backend/config.py", "ศูนย์กลางคอนฟิกูเรชัน เช่น JWT Secret Key, CORS Origins, และ URL ของ AI Server"),
        ("backend/app/__init__.py", "Application Factory สร้าง Flask App, ผูก SQLAlchemy, ลงทะเบียน 5 Blueprints และทำ Auto Schema Migration"),
        ("backend/app/extensions.py", "ประกาศตัวแปรกลาง db = SQLAlchemy() ป้องกันปัญหา Circular Import"),
        ("backend/app/models/user.py", "โมเดลตาราง users (id, email, password_hash, created_at) ผูก Cascade Delete ไปยังตารางภาพ"),
        ("backend/app/models/generation.py", "โมเดลตาราง generations สำหรับบันทึกประวัติการสร้างภาพ AI พร้อมเก็บไฟล์เป็น BLOB"),
        ("backend/app/middleware/jwt_auth.py", "มิดเดิลแวร์ @token_required ถอดรหัส user_id จาก Bearer JWT Token และตรวจอายุ Token"),
        ("backend/app/routes/auth.py", "เส้นทาง /register (ตรวจสอบอีเมลซ้ำ, แฮชรหัสผ่าน) และ /login (ตรวจสอบรหัสผ่าน, ออก JWT)"),
        ("backend/app/routes/sd.py", "เส้นทาง /generate (สร้างภาพ AI), /estimate (ประเมินเวลา), /images/:id (สตรีมภาพ PNG พร้อมเช็กเจ้าของ)"),
        ("backend/app/routes/history.py", "เส้นทาง /history (ดึงประวัติพร้อม Pagination & Filter), ดูรายละเอียด และลบประวัติของตนเอง"),
        ("backend/app/routes/profile.py", "เส้นทาง /profile ดึงข้อมูลส่วนตัวผู้ใช้ และสรุปสถิติจำนวนภาพที่สร้างทั้งหมด"),
        ("backend/app/services/ai_client.py", "ตัวเชื่อมต่อ Stable Diffusion Server พร้อมระบบ Concurrency Queue (GPU Lock) และระบบคำนวณเวลาประเมิน"),
        ("backend/app/services/image_filters/routes.py", "จุดรับคำขอ API สำหรับการประมวลผลภาพบนเซิร์ฟเวอร์ (/api/v1/process/*)"),
        ("backend/app/utils/error_codes.py", "ฟังก์ชันห่อ Response Format (success_response, error_response) และนิยาม Error Codes ทั้ง 14 รูปแบบ")
    ]
    render_table(doc, file_headers, file_rows, [Inches(2.3), Inches(4.2)])

    # Section 3
    add_heading_1(doc, "3. เจาะลึกกระบวนการทำงานและเส้นทางข้อมูล (Data Flow)")
    
    add_heading_2(doc, "3.1 การสมัครสมาชิกและเข้าสู่ระบบ (Auth Flow)")
    add_bullet(doc, "Register: ", "ผู้ใช้ส่งอีเมลและรหัสผ่าน -> Backend ตรวจ Regex และเช็กอีเมลซ้ำในตาราง users -> แฮชรหัสผ่านด้วย PBKDF2/SHA256 -> บันทึกลงฐานข้อมูล ตอบกลับ 201 Created")
    add_bullet(doc, "Login: ", "ผู้ใช้ส่งอีเมลและรหัสผ่าน -> ตรวจสอบกับ Hash ด้วย check_password_hash -> ออก JWT Token (HS256 อายุ 24 ชม.) บรรจุ user_id -> ส่งกลับให้ Frontend เก็บใน localStorage")

    add_heading_2(doc, "3.2 การสร้างภาพด้วย AI และการป้องกันสิทธิ์รูปภาพ (Generation & IDOR Protection)")
    add_bullet(doc, "Generate: ", "รับคำขอ POST /api/v1/generate พร้อม JWT Token -> ตรวจพารามิเตอร์ -> เข้าคิว Mutex GPU Lock -> ยิงคำขอไปที่ Stable Diffusion API -> รับ Base64 แปลงเป็นไบนารี -> บันทึกลงตาราง generations (BLOB) -> ตอบกลับ URL ภาพ")
    add_bullet(doc, "Stream Image: ", "Frontend สั่ง GET /api/v1/images/:id พร้อม Token -> ค้นหาใน DB ด้วยเงื่อนไขคู่: id = :id AND user_id = request.user_id -> หากเป็นเจ้าของจะสตรีมไบนารี PNG กลับไป -> หากไม่ใช่จะตอบกลับ 404 เพื่อป้องกัน IDOR ทันที")

    add_heading_2(doc, "3.3 การประมวลผลภาพบน Edge Service (Edge Image Processing)")
    add_bullet(doc, "Local Processing: ", "ผู้ใช้อัปโหลดรูปภาพพร้อมพารามิเตอร์ไปยัง /api/v1/process/* -> ตรวจสอบ Token และนามสกุลไฟล์ -> ถอดรหัสเป็น OpenCV Matrix -> ประมวลผลบนเซิร์ฟเวอร์ทันทีด้วย OpenCV/MediaPipe โดยไม่ต้องต่อคิว AI Server -> ตอบกลับเป็นภาพ PNG หรือผลลัพธ์ JSON")

    doc.add_paragraph()

    # Section 4
    add_heading_1(doc, "4. สรุปรายการ API Endpoints ทั้งหมด")
    api_headers = ["Method", "Endpoint Path", "Token?", "คำอธิบายหน้าที่การทำงาน"]
    api_rows = [
        ("POST", "/api/v1/register", "ไม่จำเป็น", "สมัครสมาชิกผู้ใช้งานใหม่"),
        ("POST", "/api/v1/login", "ไม่จำเป็น", "ตรวจสอบรหัสผ่านและรับ JWT Token"),
        ("GET", "/api/v1/models", "ไม่จำเป็น", "ดึงรายชื่อโมเดล AI Checkpoints ทั้งหมด"),
        ("POST", "/api/v1/estimate", "ไม่จำเป็น", "คำนวณเวลาประเมินล่วงหน้าในการสร้างภาพ"),
        ("POST", "/api/v1/generate", "ต้องมี", "สั่งสร้างรูปภาพ AI (ผูกกับเจ้าของบัญชี)"),
        ("GET", "/api/v1/images/:id", "ต้องมี", "สตรีมไฟล์ภาพ PNG (จำกัดสิทธิ์เฉพาะเจ้าของ)"),
        ("GET", "/api/v1/history", "ต้องมี", "ดึงรายการประวัติภาพพร้อม Pagination และ Filter"),
        ("GET", "/api/v1/history/:id", "ต้องมี", "ดึงรายละเอียดพารามิเตอร์ของภาพ"),
        ("DELETE", "/api/v1/history/:id", "ต้องมี", "ลบประวัติรูปภาพของตนเองออกจากระบบ"),
        ("GET", "/api/v1/profile", "ต้องมี", "ดึงข้อมูลโปรไฟล์และสรุปสถิติจำนวนภาพที่สร้าง"),
        ("POST", "/api/v1/process/spot-blur", "ต้องมี", "เบลอภาพเฉพาะจุดตามตำแหน่งพิกัดวงกลม"),
        ("POST", "/api/v1/process/gesture", "ต้องมี", "จดจำท่าทางมือจากรูปภาพนิ่ง"),
        ("POST", "/api/v1/process/gesture/frame", "ต้องมี", "ตรวจจับท่าทางมือจากเว็บแคมแบบเรียลไทม์"),
        ("POST", "/api/v1/process/gesture/stop", "ต้องมี", "ปิดการใช้งานกล้องเว็บแคมและคืนหน่วยความจำ"),
        ("POST", "/api/v1/process/remove-bg", "ต้องมี", "ตัดพื้นหลังภาพบุคคล (AI / GrabCut / แปรงเก็บ-ลบ)")
    ]
    render_table(doc, api_headers, api_rows, [Inches(1.0), Inches(2.2), Inches(1.0), Inches(2.3)])

    # Section 5
    add_heading_1(doc, "5. มาตรฐานรหัสข้อผิดพลาด (Standard Error Codes)")
    err_headers = ["Error Code", "HTTP Status", "คำอธิบายสาเหตุ"]
    err_rows = [
        ("VALIDATION_ERROR", "400", "ข้อมูลที่ส่งมาไม่ถูกต้องตามเงื่อนไข (เช่น รูปแบบอีเมลผิด, พารามิเตอร์ผิดช่วง)"),
        ("INVALID_CREDENTIALS", "401", "อีเมลหรือรหัสผ่านไม่ถูกต้อง"),
        ("UNAUTHORIZED", "401", "ไม่มี Token หรือ Token หมดอายุ / ลายเซ็นไม่ถูกต้อง"),
        ("EMAIL_EXISTS", "409", "อีเมลนี้ถูกใช้สมัครไปแล้วในระบบ"),
        ("GENERATION_NOT_FOUND", "404", "ไม่พบเรคคอร์ดรูปภาพ หรือพยายามเข้าถึงภาพของผู้อื่น"),
        ("IMAGE_NOT_FOUND", "404", "ไม่พบข้อมูลรูปภาพแบบ Binary ในฐานข้อมูล"),
        ("INVALID_IMAGE", "400", "ไฟล์รูปภาพเสียหาย ไม่สามารถถอดรหัสด้วย OpenCV ได้"),
        ("UNSUPPORTED_FILE_TYPE", "415", "นามสกุลไฟล์ไม่รองรับ (รองรับเฉพาะ .jpg, .jpeg, .png, .webp)"),
        ("MODEL_UNAVAILABLE", "503", "ไฟล์โมเดล AI ในระบบไม่พร้อมใช้งาน หรือดาวน์โหลดไม่สำเร็จ"),
        ("GENERATION_FAILED", "500", "การประมวลผลคำนวณภาพขัดข้อง"),
        ("AI_SERVER_BUSY", "409", "คิวงานบน AI Server แน่นเกินเวลาที่กำหนดให้รอได้ (เกิน 120 วินาที)"),
        ("AI_SERVER_TIMEOUT", "504", "AI Server ประมวลผลช้าเกินเวลาที่กำหนด (เกิน 75 วินาที)"),
        ("AI_SERVER_ERROR", "503", "เกิดข้อผิดพลาดฝั่ง AI Server หรือไม่สามารถเชื่อมต่อได้"),
        ("INTERNAL_SERVER_ERROR", "500", "เกิดข้อผิดพลาดที่ไม่คาดคิดภายในระบบเซิร์ฟเวอร์ Backend")
    ]
    render_table(doc, err_headers, err_rows, [Inches(2.0), Inches(1.1), Inches(3.4)])

    # Section 6
    add_heading_1(doc, "6. แนวทางการตอบคำถามสำหรับการสอบพรีเซนต์ (Defense Q&A)")
    
    q_data = [
        ("Q1: ทำไมถึงเลือกเก็บรูปภาพเป็น BLOB ใน SQLite ไม่เซฟเป็นไฟล์ลงดิสก์?",
         "ตอบ: การจัดเก็บเป็น BLOB ช่วยให้ระบบมีความเป็นเอกภาพและพอร์ตง่าย (ไฟล์ database.db ไฟล์เดียวย้ายไปรันที่ไหนก็ครบ), มี Transaction Consistency ร่วมกับ Cascade Delete เมื่อลบผู้ใช้ข้อมูลภาพจะถูกลบทันทีไม่มีไฟล์ขยะตกค้าง, และช่วยเรื่องความปลอดภัยในการควบคุมสิทธิ์เข้าดูภาพผ่าน @token_required"),
        ("Q2: หากมีผู้ใช้กดสั่งสร้างภาพพร้อมกันหลายคน ระบบป้องกันการล่มอย่างไร?",
         "ตอบ: เราวางระบบ Concurrency Queue โดยใช้ threading.Lock (Mutex) ใน services/ai_client.py ทำให้ GPU ประมวลผลทีละ 1 งานอย่างปลอดภัย ไม่เกิดปัญหาหน่วยความจำการ์ดจอเต็ม (CUDA Out of Memory) พร้อมมีระบบคำนวณเวลาประเมินส่งกลับไปให้หน้าเว็บแสดงเวลานับถอยหลัง"),
        ("Q3: ระบบป้องกันไม่ให้ผู้ใช้แอบดูรูปภาพของคนอื่นอย่างไร (IDOR Protection)?",
         "ตอบ: ใน Endpoint /api/v1/images/:id มิดเดิลแวร์จะถอดรหัส user_id จาก Token ของผู้เรียกเสมอ และใช้คำสั่ง SQL ค้นหาด้วยเงื่อนไขคู่ WHERE id = :id AND user_id = request.user_id หากผู้ใช้คนอื่นพยายามเดาเลข ID ระบบจะหาไม่พบและตอบกลับ 404 ทันที"),
        ("Q4: ทำไมจึงแยกโมดูลประมวลผลภาพ (Image Processing) มารันบน Backend?",
         "ตอบ: เพราะฟังก์ชันอย่าง Spot Blur, Gesture Recognition และ Background Removal สามารถประมวลผลบน CPU ด้วย OpenCV และ MediaPipe ได้รวดเร็วระดับมิลลิวินาที การแยกออกมาช่วยลดภาระงานของ GPU หลัก และทำให้ผู้ใช้ไม่ต้องรอต่อคิวสร้างภาพ AI ที่กินเวลานานครับ")
    ]
    for q, ans in q_data:
        add_heading_2(doc, q)
        p = doc.add_paragraph(ans)
        p.paragraph_format.line_spacing = 1.15

    output_path = os.path.join(output_dir, "BACKEND_REPORT.docx")
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")


# ==============================================================================
# 2. GENERATE IMAGE PROCESSING REPORT DOCX
# ==============================================================================
def generate_image_processing_report(output_dir):
    doc = Document()
    setup_document_styles(doc)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title.add_run("รายงานระบบประมวลผลภาพและคอมพิวเตอร์วิทัศน์\n(LUMA Image Processing & Computer Vision Report)")
    run_title.font.name = "Cordia New"
    run_title.font.size = Pt(22)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    doc.add_paragraph()

    # Section 1
    add_heading_1(doc, "1. ภาพรวมระบบ (Overview)")
    p = doc.add_paragraph(
        "โมดูล Image Processing Services (backend/app/services/image_filters/) เป็นบริการประมวลผลภาพ ตกแต่งภาพเฉพาะจุด "
        "และวิเคราะห์ท่าทางแบบ Edge Service ของระบบ LUMA ทำงานบนเซิร์ฟเวอร์ Backend (Flask) โดยตรง โดยไม่ต้องพึ่งพา Stable Diffusion AI Server หรือ GPU ภายนอก "
        "ทำให้คำขอทำงานเสร็จสิ้นภายในหลักมิลลิวินาที ภายใต้การควบคุมความปลอดภัยด้วยมิดเดิลแวร์ @token_required"
    )
    p.paragraph_format.line_spacing = 1.15

    add_bullet(doc, "OpenCV & NumPy: ", "ใช้ในการคำนวณเมทริกซ์ภาพ, การสร้าง Mask, Gaussian Blur, Alpha Blending, การกรอง Connected Components, และ GrabCut Optimization")
    add_bullet(doc, "Google MediaPipe Tasks: ", "ใช้งานโมเดล Gesture Recognizer (ตรวจจับโครงสร้างกระดูกมือ 21 จุด) และโมเดล Selfie Segmenter (แยกบุคคลออกจากพื้นหลัง)")

    doc.add_paragraph()

    # Section 2
    add_heading_1(doc, "2. โครงสร้างไฟล์และความรับผิดชอบ")
    struct_headers = ["ชื่อไฟล์", "หน้าที่และความรับผิดชอบหลัก"]
    struct_rows = [
        ("spot_blur.py", "ฟังก์ชันเบลอภาพเฉพาะจุดตามตำแหน่งพิกัดวงกลม พร้อมระบบเกลี่ยขอบนุ่ม (Feathering)"),
        ("gesture.py", "ระบบตรวจจับท่าทางมือจากภาพนิ่งและเว็บแคมเรียลไทม์ พร้อมระบบแคชและจัดการเซสชันผู้ใช้"),
        ("remove_bg.py", "ระบบตัดพื้นหลังภาพบุคคลแบบ Hybrid (AI + Interactive GrabCut + Matting Equation)"),
        ("routes.py", "จุดรับคำขอ API (process_bp) ภายใต้ Prefix /api/v1/process/* และตรวจสอบสิทธิ์/ความถูกต้องของไฟล์")
    ]
    render_table(doc, struct_headers, struct_rows, [Inches(1.8), Inches(4.7)])

    # Section 3
    add_heading_1(doc, "3. เจาะลึกระบบย่อยที่ 1: Spot Blur (การเบลอเฉพาะจุด)")
    p = doc.add_paragraph(
        "ฟังก์ชัน Spot Blur ช่วยให้ผู้ใช้สามารถระบายวงกลมเพื่อเซนเซอร์ข้อมูลส่วนบุคคลหรือจุดที่ไม่ต้องการบนภาพ โดยมีกระบวนการ 4 ขั้นตอนสำคัญ:"
    )
    p.paragraph_format.line_spacing = 1.15

    add_bullet(doc, "1. Pre-blurring: ", "นำภาพต้นฉบับมาเบลอทั้งใบด้วย cv2.GaussianBlur โดยขนาด Kernel คำนวณจากสูตร (strength * 2 + 1) เพื่อให้ได้เลขคี่เสมอ")
    add_bullet(doc, "2. Mask Creation: ", "สร้างแผ่น Mask สีดำ (0.0) แล้ววาดวงกลมสีขาว (1.0) ตามพิกัด x, y, r ที่ผู้ใช้ระบาย")
    add_bullet(doc, "3. Feathering (Soft Edges): ", "นำแผ่น Mask ไปทำ Gaussian Blur ด้วยขนาดตามรัศมีวงกลมที่ใหญ่ที่สุด เพื่อให้ขอบของวงกลมค่อย ๆ จางลงอย่างเป็นธรรมชาติ")
    add_bullet(doc, "4. Alpha Blending: ", "ผสมภาพด้วยสมการ Output = Image * (1 - Mask) + Blurred * Mask ทำให้รอยต่อระหว่างส่วนที่เบลอกับส่วนปกติกลมกลืนไร้รอยต่อ")

    doc.add_paragraph()

    # Section 4
    add_heading_1(doc, "4. เจาะลึกระบบย่อยที่ 2: Hand Gesture Recognition (ตรวจจับท่าทางมือ)")
    p = doc.add_paragraph(
        "ระบบตรวจจับท่าทางมือใช้โมเดล Gesture Recognizer ของ Google MediaPipe ซึ่งตรวจจับข้อต่อกระดูกมือทั้งหมด 21 จุด (Landmarks) "
        "ในพิกัด 3 มิติ และจำแนกท่าทางมาตรฐานได้ 7 ท่าทาง:"
    )
    p.paragraph_format.line_spacing = 1.15

    gesture_headers = ["ชื่อท่าทาง (Category)", "ภาษาไทย", "ลักษณะการสังเกต"]
    gesture_rows = [
        ("Closed_Fist", "กำมือ", "ปลายนิ้วทั้ง 4 พับลงมาแตะที่โคนฝ่ามือ"),
        ("Open_Palm", "แบมือ", "นิ้วทุกนิ้วเหยียดตรงและกางออก"),
        ("Pointing_Up", "ชี้นิ้วขึ้น", "นิ้วชี้ชี้ขึ้น นิ้วอื่นกำพับลง"),
        ("Thumb_Down", "คว่ำนิ้วโป้ง", "นิ้วโป้งชี้ลง นิ้วอื่นพับชิด"),
        ("Thumb_Up", "ชูนิ้วโป้ง", "นิ้วโป้งชี้ขึ้น แสดงความยอดเยี่ยม"),
        ("Victory", "ชูสองนิ้ว", "นิ้วชี้และนิ้วกลางเหยียดตรงเป็นรูปตัว V"),
        ("ILoveYou", "I Love You", "ชูนิ้วโป้ง นิ้วชี้ และนิ้วก้อย (นิ้วกลางและนิ้วนางพับ)"),
        ("None", "ไม่ตรงกับท่าที่รู้จัก", "มีมือในภาพแต่องศาไม่ตรงกับท่ามาตรฐาน")
    ]
    render_table(doc, gesture_headers, gesture_rows, [Inches(1.8), Inches(1.5), Inches(3.2)])

    add_heading_2(doc, "การแยกโหมดรูปนิ่ง (Image) กับโหมดเว็บแคม (Video)")
    add_bullet(doc, "โหมดรูปนิ่ง: ", "ประมวลผลแบบไร้สถานะ (Stateless) แชร์ Recognizer ร่วมกันผ่านแคชเพื่อลด Overhead ในการโหลดโมเดล")
    add_bullet(doc, "โหมดเว็บแคม: ", "โมเดลต้องจดจำตำแหน่งมือจากเฟรมก่อนหน้า (Tracking State) เพื่อให้มือนิ่งไม่กระตุก ระบบจึงแยกเซสชันต่อผู้ใช้ (_sessions[user_id]) และมีระบบปิดทำลายเซสชันอัตโนมัติเมื่อหยุดใช้งานเกิน 60 วินาที เพื่อป้องกัน Memory Leak")

    doc.add_paragraph()

    # Section 5
    add_heading_1(doc, "5. เจาะลึกระบบย่อยที่ 3: Remove Background (การตัดพื้นหลังบุคคลแบบ Hybrid)")
    p = doc.add_paragraph(
        "ระบบตัดพื้นหลังบุคคลผสานการทำงานระหว่าง AI Segmentation, Interactive GrabCut, และ Color Decontamination "
        "เพื่อมอบผลลัพธ์ที่แม่นยำและรวดเร็วระดับ Sub-second:"
    )
    p.paragraph_format.line_spacing = 1.15

    add_bullet(doc, "1. Downscaling Optimization: ", "ย่อภาพลงมาที่ WORK_SIDE = 900px ก่อนคำนวณ ทำให้อัลกอริทึม GrabCut รันเสร็จในเวลาเพียง ~0.2 วินาที (จากเดิม 4-6 วินาทีบนภาพขนาดเต็ม)")
    add_bullet(doc, "2. AI Initial Mask: ", "ใช้โมเดล selfie_multiclass_256x256 คำนวณความน่าจะเป็นของพิกเซลที่เป็นบุคคล เพื่อสร้าง Initial Mask ให้ GrabCut")
    add_bullet(doc, "3. Interactive Strokes: ", "ผู้ใช้สามารถลากกรอบ (Rect) หรือใช้แปรงระบายจุดที่ต้องการเก็บ (Keep) หรือลบออก (Remove) เพิ่มเติมได้อย่างอิสระ")
    add_bullet(doc, "4. Noise Filtering: ", "ใช้ cv2.connectedComponentsWithStats ค้นหาก้อนวัตถุหลักและกรองเศษ Noise ฝุ่นเล็ก ๆ ทิ้งไป")
    add_bullet(doc, "5. Color Decontamination: ", "ใช้สมการ Matting Equation: F = (I - (1 - alpha) * B) / alpha เพื่อหักลบสีสะท้อนของฉากหลังเดิมออกจากไรผม ทำให้ขอบผมไม่เรืองแสงและดูเป็นธรรมชาติ")

    doc.add_paragraph()

    # Section 6
    add_heading_1(doc, "6. สรุปรายละเอียด API Endpoints (/api/v1/process/*)")
    proc_headers = ["Method", "Endpoint Path", "พารามิเตอร์สำคัญ", "ผลลัพธ์ตอบกลับ"]
    proc_rows = [
        ("POST", "/api/v1/process/spot-blur", "image, circles, strength, soft", "สตรีมภาพ PNG ที่เบลอเฉพาะจุด"),
        ("POST", "/api/v1/process/gesture", "image, num_hands, min_confidence", "JSON สรุปผลชื่อท่าทาง และความมั่นใจ"),
        ("POST", "/api/v1/process/gesture/frame", "image (frame), num_hands, min_confidence", "JSON โครงกระดูกมือ 21 จุดและท่าทางสำหรับเว็บแคม"),
        ("POST", "/api/v1/process/gesture/stop", "-", "JSON ยืนยันการปิดเซสชันและคืนหน่วยความจำ"),
        ("POST", "/api/v1/process/remove-bg", "image, use_ai, rect, strokes, bg", "สตรีมภาพ PNG โปร่งใส (BGRA) หรือเติมสีพื้นใหม่")
    ]
    render_table(doc, proc_headers, proc_rows, [Inches(0.9), Inches(2.2), Inches(1.8), Inches(1.6)])

    # Section 7
    add_heading_1(doc, "7. แนวทางการตอบคำถามสำหรับการสอบพรีเซนต์ (Defense Q&A)")
    qa_list = [
        ("Q1: ในโหมดเว็บแคมของ Gesture Recognition ทำไมต้องแยกเซสชันต่อผู้ใช้?",
         "ตอบ: เพราะโมเดลของ MediaPipe ในโหมด RunningMode.VIDEO ต้องอาศัยข้อมูล Tracking State จากเฟรมก่อนหน้าเพื่อติดตามมืออย่างราบรื่น หากใช้ Recognizer ตัวเดียวกันแชร์ข้ามคน ตำแหน่งมือของผู้ใช้คนหนึ่งจะไปกระตุกใส่อีกคนทันที เราจึงต้องแยกเซสชันต่อ user_id และมีระบบทำลายเซสชันอัตโนมัติเมื่อหยุดส่งภาพเกิน 60 วินาทีเพื่อคืนหน่วยความจำครับ"),
        ("Q2: ทำไมจึงต้องย่อขนาดภาพลงมาที่ 900px ก่อนรัน GrabCut?",
         "ตอบ: เพราะการคำนวณกราฟสีของ GrabCut มีความซับซ้อนสูงมาก หากคำนวณบนภาพขนาดจริง 12 ล้านพิกเซล จะกินเวลานาน 4-6 วินาที การย่อภาพลงมาที่ด้านยาว 900px ช่วยลดเวลาคำนวณเหลือเพียง ~0.2 วินาที จากนั้นเราจึงนำ Mask ที่ได้ขยายสัดส่วนกลับไปเป็นขนาดจริงพร้อมทำ Gaussian Feathering จึงได้ทั้งความเร็วและความคมชัดครับ"),
        ("Q3: สมการ Color Decontamination ช่วยแก้ปัญหาอะไร?",
         "ตอบ: ช่วยแก้ปัญหาขอบสีสะท้อนของฉากหลังเดิม (Background Color Bleed) ที่ติดอยู่ตามไรผมหรือขอบเสื้อผ้าครับ เช่น หากฉากหลังเดิมเป็นสีเขียว ขอบผมจะมีสีเขียวติดมาด้วย สมการ Matting Equation จะคำนวณหักลบสีพื้นหลังเดิมออก ทำให้เส้นผมกลับมาเป็นสีธรรมชาติต้นฉบับครับ")
    ]
    for q, ans in qa_list:
        add_heading_2(doc, q)
        p = doc.add_paragraph(ans)
        p.paragraph_format.line_spacing = 1.15

    output_path = os.path.join(output_dir, "IMAGE_PROCESSING_REPORT.docx")
    doc.save(output_path)
    print(f"Successfully generated: {output_path}")


def main():
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Generating documents in: {docs_dir}")
    generate_backend_report(docs_dir)
    generate_image_processing_report(docs_dir)
    print("All documents generated successfully!")


if __name__ == "__main__":
    main()
