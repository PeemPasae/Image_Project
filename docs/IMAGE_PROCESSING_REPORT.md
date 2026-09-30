# รายงานระบบประมวลผลภาพและคอมพิวเตอร์วิทัศน์ (LUMA Image Processing & Computer Vision Report)

---

## 1. ภาพรวมระบบ (Overview)

โมดูล **Image Processing Services** (`backend/app/services/image_filters/`) เป็นบริการประมวลผลภาพ ตกแต่งภาพเฉพาะจุด และวิเคราะห์ท่าทางแบบ Edge / Local Service ของระบบ LUMA โดยทำงานอยู่บนเซิร์ฟเวอร์ Backend (Flask) โดยตรง **ไม่ต้องพึ่งพา Stable Diffusion AI Server หรือ GPU ภายนอก** ทำให้คำขอทำงานเสร็จสิ้นภายในหลักมิลลิวินาที (Sub-second response time)

บริการนี้ถูกรวมเข้าสู่ระบบหลักผ่าน **Flask Blueprint** ชื่อ `process_bp` (URL Prefix: `/api/v1/process/*`) และได้รับการปกป้องด้วย Decorator `@token_required` (JWT Authentication)

### เทคโนโลยีและโมเดลที่ใช้งาน
1. **OpenCV (cv2) & NumPy**: ใช้ในการคำนวณเมทริกซ์ภาพ, การสร้าง Mask วงกลม, Gaussian Blur, Alpha Blending, การค้นหา Connected Components เพื่อกำจัด Noise, และอัลกอริทึม GrabCut Optimization
2. **Google MediaPipe Tasks (Python Vision API)**: 
   * **Gesture Recognizer (`gesture_recognizer.task`)**: โมเดล Deep Learning สำหรับระบุโครงสร้างกระดูกมือ (Hand Landmarks) 21 จุด และจำแนกท่าทางมือมาตรฐาน 7 รูปแบบ
   * **Selfie Segmenter (`selfie_multiclass_256x256.tflite`)**: โมเดล Deep Learning สำหรับแยกบุคคลออกจากพื้นหลัง (Multi-class Segmentation)

---

## 2. โครงสร้างไฟล์และความรับผิดชอบ (Module Architecture)

```
backend/app/services/image_filters/
├── __init__.py          # ส่งออก process_bp Blueprint และฟังก์ชัน Image Filters
├── routes.py            # จุดรับคำขอ (API Endpoints), ตรวจสอบ Input, สตรีมภาพ/บันทึกประวัติ
├── remove_bg.py         # ระบบตัดพื้นหลังภาพบุคคลแบบ Hybrid (AI + GrabCut + Matting)
├── spot_blur.py         # ฟังก์ชันเบลอภาพเฉพาะจุดตามตำแหน่งวงกลม (Spot Blur Engine)
├── gesture.py           # ระบบตรวจจับท่าทางมือจากภาพนิ่งและเว็บแคม (Gesture Engine)
└── cartoonize.py        # แปลงภาพสไตล์การ์ตูน/อนิเมะ (Anime / Comic Stylization)
```

---

## 3. เจาะลึกระบบย่อยที่ 1: Spot Blur (การเบลอเฉพาะจุด)

### 3.1 หลักการทำงานเชิงแนวคิด
ผู้ใช้บนหน้าเว็บสามารถใช้เมาส์หรือการสัมผัสวาดจุดวงกลมบนภาพเพื่อเบลอบางส่วน (เช่น การเซนเซอร์ใบหน้า ป้ายทะเบียนรถ หรือข้อความส่วนบุคคล):
1. **เตรียมภาพเบลอทั้งใบ (Pre-blurring)**: นำภาพต้นฉบับมาทำ Gaussian Blur ทั้งภาพด้วยเคอร์เนลขนาดตามค่า `strength`
2. **สร้างแผ่นหน้ากาก (Mask Creation)**: สร้างภาพขาวดำ (Grayscale 0.0 - 1.0) ขนาดเท่าภาพต้นฉบับ โดยมีพื้นหลังเป็นสีดำ (0.0) และวาดวงกลมสีขาว (1.0) ตามพิกัด $(x, y, r)$ ที่ผู้ใช้ส่งมา
3. **เกลี่ยขอบนุ่ม (Feathering / Soft Edges)**: หากผู้ใช้เปิดออปชัน `soft=true` ระบบจะนำแผ่น Mask ไปทำ Gaussian Blur ซ้ำ เพื่อให้ขอบของวงกลมค่อย ๆ จางลง (Gradient Decay) ไม่เกิดรอยตัดแข็งทื่อ
4. **การผสมภาพ (Alpha Blending)**: ใช้สมการ Interpolation ทางคอมพิวเตอร์กราฟิกส์:
   $$\text{Output} = \text{Image} \times (1 - \text{Mask}) + \text{Blurred} \times \text{Mask}$$

### 3.2 ซอร์สโค้ดและการทำงาน (`backend/app/services/image_filters/spot_blur.py`)
```python
import cv2
import numpy as np

def spot_blur(img, circles, strength=10, soft=True):
    # 1. คำนวณขนาด Kernel สำหรับ Gaussian Blur (ต้องเป็นเลขคี่เสมอ)
    k = strength * 2 + 1
    blurred = cv2.GaussianBlur(img, (k, k), 0)

    # 2. สร้างแผ่น Mask เริ่มต้นด้วยค่า 0.0 (สีดำ)
    mask = np.zeros(img.shape[:2], np.float32)
    for x, y, r in circles:
        # วาดวงกลมสีขาวทึบ (1.0) พิกัด x, y รัศมี r
        cv2.circle(mask, (int(x), int(y)), int(r), 1.0, -1)

    # 3. เกลี่ยขอบวงกลมให้นุ่มนวลตามขนาดรัศมีที่ใหญ่ที่สุด
    if soft and circles:
        edge = int(max(r for _, _, r in circles) * 0.5) * 2 + 1
        mask = cv2.GaussianBlur(mask, (edge, edge), 0)

    # 4. ขยายมิติ Mask เป็น 3D (H, W, 1) และผสมสี BGR
    mask = mask[:, :, None]
    out = img * (1 - mask) + blurred * mask
    return out.astype(np.uint8)
```

---

## 4. เจาะลึกระบบย่อยที่ 2: Hand Gesture Recognition (ตรวจจับท่าทางมือ)

### 4.1 สถาปัตยกรรม Hand Landmarks 21 จุด
โมเดลของ MediaPipe ตรวจจับข้อต่อกระดูกมือทั้งหมด 21 จุดในพิกัด 3 มิติ $(X, Y, Z)$ แบบ Normalized Coordinate (0.0 - 1.0):
* **ข้อมือ (Wrist)**: จุดที่ 0
* **นิ้วโป้ง (Thumb)**: จุดที่ 1-4 (CMC, MCP, IP, Tip)
* **นิ้วชี้ (Index Finger)**: จุดที่ 5-8 (MCP, PIP, DIP, Tip)
* **นิ้วกลาง (Middle Finger)**: จุดที่ 9-12 (MCP, PIP, DIP, Tip)
* **นิ้วนาง (Ring Finger)**: จุดที่ 13-16 (MCP, PIP, DIP, Tip)
* **นิ้วก้อย (Pinky)**: จุดที่ 17-20 (MCP, PIP, DIP, Tip)

### 4.2 ตารางท่าทางมาตรฐานที่ระบบจำแนกได้ (7 ท่าทางหลัก)
| ท่าทาง (Category Name) | คำอธิบายภาษาไทย | ลักษณะที่สังเกต |
| :---: | :---: | :--- |
| `Closed_Fist` | กำมือ | ปลายนิ้วทั้ง 4 พับลงมาแตะที่โคนฝ่ามือ |
| `Open_Palm` | แบมือ | นิ้วทุกนิ้วเหยียดตรงและกางออก |
| `Pointing_Up` | ชี้นิ้วขึ้น | นิ้วชี้ชี้ขึ้น นิ้วอื่นกำพับลง |
| `Thumb_Down` | คว่ำนิ้วโป้ง | นิ้วโป้งชี้ลง นิ้วอื่นพับชิด |
| `Thumb_Up` | ชูนิ้วโป้ง | นิ้วโป้งชี้ขึ้น แสดงความยอดเยี่ยม |
| `Victory` | ชูสองนิ้ว | นิ้วชี้และนิ้วกลางเหยียดเป็นรูปตัว V |
| `ILoveYou` | I Love You | ชูนิ้วโป้ง นิ้วชี้ และนิ้วก้อย (นิ้วกลางและนิ้วนางพับ) |
| `None` | ไม่ตรงกับท่าที่รู้จัก | มีมือในภาพแต่องศาไม่ตรงกับเกณฑ์มาตรฐาน |

### 4.3 การแยกระหว่างโหมดรูปนิ่ง (Image) กับโหมดเว็บแคม (Video)
* **โหมดรูปนิ่ง (`RunningMode.IMAGE`)**:
  - ประมวลผลทีละรูป จบงานแล้วไม่ต้องจดจำประวัติ
  - ระบบใช้แคช `_image_recognizers[(num_hands, min_confidence)]` เพื่อแชร์ Recognizer Instance ระหว่างผู้ใช้ ช่วยประหยัดเวลาโหลดโมเดล
* **โหมดเว็บแคม (`RunningMode.VIDEO`)**:
  - ได้รับเฟรมต่อเนื่อง 15-30 เฟรม/วินาที
  - โมเดลต้องรักษา **Tracking State** เพื่อจำตำแหน่งมือจากเฟรมก่อนหน้า ทำให้ผลลัพธ์มือนิ่ง ไม่กระตุก
  - **การแก้ปัญหาผู้ใช้หลายคน**: แยก Session ต่อ `user_id` (`_sessions[user_id]`) เพื่อป้องกันไม่ให้ข้อมูลมือของผู้ใช้ A ไปปะปนกับผู้ใช้ B
  - **การคืนหน่วยความจำอัตโนมัติ**: ฟังก์ชัน `_close_idle_sessions()` จะปิด Recognizer ของผู้ใช้ที่หยุดส่งเฟรมเกิน `SESSION_IDLE_SECONDS = 60` วินาทีโดยอัตโนมัติ

---

## 5. เจาะลึกระบบย่อยที่ 3: Remove Background (การตัดพื้นหลังบุคคล)

ระบบตัดพื้นหลังถูกออกแบบขึ้นในรูปแบบ **Hybrid Pipeline** ที่รวมเอา Deep Learning AI, อัลกอริทึม Interactive GrabCut, และกระบวนการ Color Decontamination เข้าด้วยกัน

```
ภาพต้นฉบับ (BGR)
       │
       ▼
ย่อขนาดลงมาที่ WORK_SIDE = 900px (เพื่อความเร็ว Sub-second)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
AI Selfie Segmenter             ผู้ใช้กำหนดกรอบ (Rect)
(selfie_multiclass_256x256)       และเส้นแปรง Keep/Remove (Strokes)
       │                                 │
       └────────────────┬────────────────┘
                        ▼
       สร้าง Initial GrabCut Mask (GC_BGD, GC_PR_BGD, GC_PR_FGD, GC_FGD)
                        │
                        ▼
       รัน cv2.grabCut() (4 Iterations) คำนวณ GMM Model
                        │
                        ▼
       กรอง Noise ด้วย cv2.connectedComponentsWithStats
                        │
                        ▼
       ขยาย Mask กลับขนาดภาพจริง (W, H) ด้วย Linear Interpolation + Gaussian Feathering
                        │
                        ▼
       ลบสีสะท้อนของฉากหลังเดิม (Color Decontamination Matting Equation)
                        │
                        ▼
   ส่งออกภาพผลลัพธ์: PNG โปร่งใส (BGRA) หรือ แทนที่ด้วยสีพื้นหลังใหม่ (BGR)
```

### 5.1 การเพิ่มประสิทธิภาพด้วยการย่อส่วน (Optimization via Downscaling)
อัลกอริทึม GrabCut มีความซับซ้อนในการคำนวณ Gaussian Mixture Models (GMM) บนทุกพิกเซล หากคำนวณบนภาพขนาดจริง (เช่น $4000 \times 3000$) จะใช้เวลาเกิน 5 วินาที ระบบจึงย่อภาพลงมาที่ `WORK_SIDE = 900` ทำให้รันเสร็จในเวลาเพียง ~0.2 วินาที จากนั้นจึงนำผลลัพธ์ Mask ขยายสัดส่วนกลับขึ้นมาพร้อมทำ Gaussian Smoothing

### 5.2 การกำจัดขอบสีสะท้อน (Color Decontamination / Alpha Matting)
เมื่อตัดพื้นหลังออกจากรูปถ่าย ขอบเส้นผมมักจะมีสีของฉากหลังเดิมสะท้อนติดอยู่ (เช่น ขอบเขียวหรือขอบขาว) ระบบแก้ปัญหานี้ด้วยการถอดสีพื้นหลังเดิมออกตามสมการ Matting Equation:
$$I = \alpha F + (1 - \alpha) B \implies F = \frac{I - (1 - \alpha) B}{\alpha}$$
* $I$: สีของพิกเซลที่ปรากฏในรูปต้นฉบับ
* $B$: สีของฉากหลังเดิม (คำนวณจากค่าเฉลี่ยถ่วงน้ำหนักของพื้นหลังรอบ ๆ ด้วย Gaussian Blur)
* $\alpha$: ค่าความทึบของ Mask (0.0 ถึง 1.0)
* $F$: สีเนื้อจริงของเส้นผมที่ผ่านการหักลบสีฉากหลังออกแล้ว

---

## 6. สรุปรายละเอียด API Endpoints (`/api/v1/process/*`)

### 6.1 `POST /api/v1/process/spot-blur` 🔒
* **Headers**: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
* **Form Fields**:
  - `image`: ไฟล์ภาพ (.jpg, .jpeg, .png, .webp)
  - `circles`: JSON String ของพิกัด `[[x, y, radius], ...]`
  - `strength`: ตัวเลขความแรงของการเบลอ `1-30`
  - `soft`: `"true"` หรือ `"false"`
* **Response**: ข้อมูลไบนารีสตรีมภาพ PNG (`Content-Type: image/png`)

### 6.2 `POST /api/v1/process/gesture` 🔒
* **Form Fields**:
  - `image`: ไฟล์ภาพนิ่ง
  - `num_hands`: จำนวนมือสูงสุดที่จะตรวจจับ (`1-4`, ค่าเริ่มต้น `2`)
  - `min_confidence`: ความมั่นใจขั้นต่ำ (`0.1-1.0`, ค่าเริ่มต้น `0.5`)
* **Response**: JSON ผลลัพธ์
  ```json
  {
    "success": true,
    "data": {
      "found": true,
      "hand_count": 1,
      "gesture": "Victory",
      "gesture_th": "ชูสองนิ้ว",
      "confidence": 98.45,
      "handedness": "Right",
      "inference_time_ms": 14.2,
      "hands": [ ... ]
    }
  }
  ```

### 6.3 `POST /api/v1/process/gesture/frame` 🔒
* **หน้าที่**: รับภาพเฟรมต่อเนื่องจากเว็บแคม ใช้ Recognizer แยกเฉพาะของผู้ใช้คนนั้น
* **Form Fields**: `image` (Blob จาก canvas.toBlob), `num_hands`, `min_confidence`
* **Response**: JSON ผลลัพธ์พร้อมตำแหน่งกระดูกมือ 21 จุดเพื่อวาดบน Frontend

### 6.4 `POST /api/v1/process/gesture/stop` 🔒
* **หน้าที่**: แจ้งเมื่อผู้ใช้ปิดกล้องเว็บแคม เพื่อทำลาย Recognizer Session และคืนหน่วยความจำทันที

### 6.5 `POST /api/v1/process/remove-bg` 🔒
* **Form Fields**:
  - `image`: ไฟล์ภาพบุคคล
  - `use_ai`: `"true"` (ใช้โมเดลตัดอัตโนมัติ) หรือ `"false"` (ใช้ GrabCut ล้วน)
  - `rect`: JSON Array `[x, y, width, height]` (กำหนดกรอบตัดเฉพาะส่วน)
  - `strokes`: JSON Array ของเส้นแปรงที่ผู้ใช้ระบาย `[{"type": "keep"/"remove", "r": 12, "points": [[x,y], ...]}]`
  - `bg`: `"transparent"` หรือรหัสสี Hex เช่น `"#FFFFFF"`
* **Response**: ข้อมูลไบนารีสตรีมภาพ PNG โปร่งใส 4 ช่องสี (BGRA) หรือภาพสีใหม่ 3 ช่องสี (BGR)

### 6.6 `POST /api/v1/process/cartoonize` 🔒
* **หน้าที่**: อัปโหลดรูปภาพใหม่เพื่อแปลงเป็นสไตล์ภาพการ์ตูน/อนิเมะ (Anime / Comic Stylization)
* **Form Fields**: `image`, `num_colors` (2-32), `line_thickness` (1-5), `smoothness` (1-10)
* **Response**: ข้อมูลไบนารีสตรีมภาพ PNG

### 6.7 `POST /api/v1/process/cartoonize/:generation_id` 🔒
* **หน้าที่**: ดึงภาพที่เคยสร้างไว้จากประวัติมาแปลงเป็นภาพการ์ตูน และบันทึกเป็นประวัติแบบที่ 2 (`category="image_filter"`, `action_type="cartoonize"`)
* **JSON Body**: `{"num_colors": 8, "line_thickness": 2, "smoothness": 5}`
* **Response**: JSON รายละเอียดภาพใหม่ที่บันทึกลงฐานข้อมูล

---

## 7. แนวทางการตอบคำถามสำหรับการสอบพรีเซนต์ (Computer Vision Defense Q&A)

#### Q1: "ทำไมใน Gesture Recognition โหมดเว็บแคม ถึงต้องแยก Session ต่อผู้ใช้?"
* **แนวทางการตอบ:**  
  *"เพราะโมเดลของ MediaPipe ในโหมด `RunningMode.VIDEO` ถูกออกแบบมาให้จดจำตำแหน่งมือของเฟรมก่อนหน้า (Tracking State) เพื่อให้การติดตามมือในเฟรมถัดไปมีความต่อเนื่องและมือนิ่งไม่กระตุกครับ หากเราใช้ตัว Recognizer ตัวเดียวกันแชร์ข้ามผู้ใช้ มือของผู้ใช้ A จะไปกระตุกปนกับผู้ใช้ B ทันที เราจึงต้องจัดเก็บตัว Recognizer แยกตาม `user_id` และมีระบบตั้งเวลาทำลายเซสชันอัตโนมัติเมื่อไม่มีการส่งภาพเกิน 60 วินาทีเพื่อคืน RAM ครับ"*

#### Q2: "ทำไมต้องย่อรูปเป็นขนาด 900px ก่อนตัดพื้นหลังด้วย GrabCut?"
* **แนวทางการตอบ:**  
  *"เพราะอัลกอริทึม GrabCut มีความซับซ้อนในการคำนวณกราฟสี (Graph Cut Optimization) สูงมาก หากเราใช้ภาพขนาดต้นฉบับ เช่น 12 ล้านพิกเซล เซิร์ฟเวอร์จะใช้เวลาคำนวณนานถึง 4-6 วินาที การย่อภาพด้านยาวลงมาที่ `WORK_SIDE = 900px` ทำให้การประมวลผลเสร็จสิ้นในเสี้ยววินาที (~0.2 วินาที) จากนั้นจึงนำผลลัพธ์ Mask ขยายสัดส่วนกลับขึ้นมาพร้อมทำ Gaussian Feathering จึงได้ทั้งความเร็วและขอบที่เนียนคมชัดครับ"*

#### Q3: "สมการ Color Decontamination ช่วยแก้ปัญหาอะไรในการตัดพื้นหลัง?"
* **แนวทางการตอบ:**  
  *"เวลาตัดพื้นหลัง ภาพถ่ายมักจะมีแสงสะท้อนหรือสีของฉากหลังเดิมติดอยู่ที่ไรผมหรือขอบเสื้อผ้าครับ เช่น ถ้าฉากหลังเป็นกำแพงสีเขียว ไรผมก็จะมีสีเขียวติดมาด้วย สมการ Matting Equation จะคำนวณหักลบสีของฉากหลังเดิมออกจากสีพิกเซลที่เห็นตามสัดส่วนค่า Alpha ทำให้เส้นผมกลับมาเป็นสีธรรมชาติต้นฉบับ ไม่มีขอบเรืองแสงครับ"*
