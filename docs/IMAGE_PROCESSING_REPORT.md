# รายงานระบบประมวลผลภาพและปัญญาประดิษฐ์ตรวจจับท่าทาง (Image Processing & Computer Vision Report)

---

## 1. ภาพรวมระบบ (Overview)

โมดูล **Image Processing Services** (`backend/app/services/image_filters/`) เป็นบริการประมวลผล ตกแต่งภาพ และวิเคราะห์ท่าทางแบบ Edge / Local Service ของโปรเจกต์ LUMA โดยทำงานอยู่บนเซิร์ฟเวอร์ Backend (Flask) โดยตรง **ไม่ต้องพึ่งพา Stable Diffusion AI Server หรือ GPU ภายนอก**

บริการนี้ถูกรวมเข้าสู่ระบบหลักผ่าน **Flask Blueprint** ชื่อ `process_bp` (Prefix: `/api/v1/process/*`) และได้รับการปกป้องด้วย Decorator `@token_required` (JWT Authentication) เช่นเดียวกับโมดูลหลัก

### เทคโนโลยีและเครื่องมือหลักที่ใช้งาน
1. **OpenCV (cv2) & NumPy**: ใช้ในการคำนวณเมทริกซ์ภาพ, การสร้าง Mask, Gaussian Blur, Alpha Blending, การค้นหา Connected Components, และอัลกอริทึม GrabCut
2. **Google MediaPipe Tasks (Python Vision API)**: 
   * **Gesture Recognizer (`gesture_recognizer.task`)**: โมเดล Deep Learning สำหรับระบุโครงสร้างกระดูกมือ (Hand Landmarks) 21 จุด และจำแนกท่าทางมือ
   * **Selfie Segmenter (`selfie_multiclass_256x256.tflite`)**: โมเดล Deep Learning สำหรับแยกบุคคลออกจากพื้นหลัง (Multi-class Segmentation)

---

## 2. โครงสร้างไฟล์และความรับผิดชอบ (Module Architecture)

```
backend/app/services/image_filters/
├── __init__.py          # ส่งออก Blueprint (process_bp) เพื่อลงทะเบียนเข้ากับ Flask App
├── routes.py            # จุดรับคำขอ (API Endpoints), ตรวจสอบความถูกต้องของ Input, เรียกใช้ Engine
├── spot_blur.py         # ฟังก์ชันเบลอภาพเฉพาะจุดตามตำแหน่งพิกัดวงกลม (Spot Blur Engine)
├── gesture.py           # ระบบตรวจจับท่าทางมือจากภาพนิ่งและเว็บแคมแบบ Real-time (Gesture Engine)
└── remove_bg.py         # ระบบตัดพื้นหลังภาพบุคคลแบบ Hybrid (AI + Interactive GrabCut Engine)
```

---

## 3. เจาะลึกระบบย่อยที่ 1: Spot Blur (ระบบเบลอเฉพาะจุด)

### 3.1 คอนเซปต์แบบเข้าใจง่าย (ภาษาคน)
> **เปรียบเทียบ:** ลองนึกภาพว่าเรามีรูปถ่าย 1 ใบวางอยู่บนโต๊ะ
> 1. เราเอาแผ่นฟิล์มเบลอ ๆ แปะทับภาพทั้งใบไว้ก่อน (ภาพเบลอเตรียมพร้อม)
> 2. จากนั้นเราหยิบกระดาษสีดำขนาดเท่ารูปมาแผ่นหนึ่ง แล้วใช้กรรไกร **เจาะรูกลม ๆ** ตรงตำแหน่งที่ผู้ใช้เอานิ้วหรือเมาส์จิ้มไว้ (กระดาษนี้เรียกว่า **Mask**)
> 3. ขอบรอยเจาะถ้าเอากรรไกรตัดตรง ๆ มันจะคมบาดตา ดูไม่เนียน เราเลยเอาสำลีมาเกลี่ย ๆ ขอบรอยเจาะให้ฟุ้งละมุน (**Feathered Soft Edges**)
> 4. สุดท้าย เอาแผ่นกระดาษนี้ไปทับ: ส่วนที่เจาะรูจะเห็นภาพเบลอโผล่ขึ้นมา ส่วนที่ทึบจะโชว์ภาพคมชัดปกติเดิม

---

### 3.2 ซอร์สโค้ดจริงและการทำงาน (`backend/app/services/image_filters/spot_blur.py`)

```python
import cv2
import numpy as np

def spot_blur(img, circles, strength=10, soft=True):
    """เบลอเฉพาะจุดเป็นวงกลม
    img      : ภาพ (BGR)
    circles  : รายการวงกลม [(x, y, radius), ...] หน่วยเป็น pixel ของภาพจริง
    strength : ความแรงของการเบลอ 1-30
    soft     : True = ขอบวงกลมค่อย ๆ จางลง (ดูเนียน), False = ขอบคม
    """
    # --------------------------------------------------------------------------
    # ขั้นที่ 1: เบลอทั้งภาพเตรียมรอไว้เลย
    # --------------------------------------------------------------------------
    # Kernel ของ GaussianBlur ต้องเป็นเลขคี่เสมอ จึงใช้สูตร (strength * 2 + 1)
    k = strength * 2 + 1
    blurred = cv2.GaussianBlur(img, (k, k), 0)

    # --------------------------------------------------------------------------
    # ขั้นที่ 2: สร้างแผ่น Mask (สีดำ 0.0 ทั้งแผ่น แล้วแต้มวงกลมสีขาว 1.0)
    # --------------------------------------------------------------------------
    mask = np.zeros(img.shape[:2], np.float32)
    for x, y, r in circles:
        # -1 หมายถึงให้ระบายสีขาวทึบเต็มวงกลม
        cv2.circle(mask, (int(x), int(y)), int(r), 1.0, -1)

    # --------------------------------------------------------------------------
    # ขั้นที่ 3: ทำให้ขอบวงกลมฟุ้งนุ่ม (Soft Edges) ไม่ให้รอยต่อตัดกันแข็งทื่อ
    # --------------------------------------------------------------------------
    if soft and circles:
        # คำนวณความฟุ้งตามขนาดรัศมีวงกลมที่ใหญ่ที่สุด
        edge = int(max(r for _, _, r in circles) * 0.5) * 2 + 1
        mask = cv2.GaussianBlur(mask, (edge, edge), 0)

    # --------------------------------------------------------------------------
    # ขั้นที่ 4: ผสมภาพจริงกับภาพเบลอด้วยสมการ Alpha Blending
    # --------------------------------------------------------------------------
    # ขยายมิติ Mask จาก 2 มิติ (กว้าง x ยาว) เป็น 3 มิติ เพื่อให้คูณกับสี BGR 3 ช่องได้
    mask = mask[:, :, None]
    
    # ตรงไหน mask = 1.0 (สีขาว) จะได้ภาพ blurred 100%
    # ตรงไหน mask = 0.0 (สีดำ) จะได้ภาพ img เดิม 100%
    # ตรงขอบที่เป็นสีเทา (เช่น 0.5) จะผสมกันอย่างละครึ่ง ดูนุ่มนวลเป็นธรรมชาติ
    out = img * (1 - mask) + blurred * mask
    
    return out.astype(np.uint8)
```

---

### 3.3 คำอธิบายแต่ละบรรทัดแบบเจาะลึก
1. `k = strength * 2 + 1`: OpenCV บังคับว่าตารางคำนวณเบลอ (Kernel) ต้องมีจุดศูนย์กลางชัดเจน จึงต้องเป็นเลขคี่เสมอ เช่น ผู้ใช้ส่ง strength = 10 จะได้เคอร์เนลขนาด $21 \times 21$
2. `np.zeros(img.shape[:2], np.float32)`: สร้างแผ่นพลาสติกใสสีดำมืด (ค่า 0.0) ขนาดกว้างยาวเท่ากับรูปภาพ
3. `cv2.circle(...)`: ผู้ใช้ลากเมาส์เป็นทางยาว Frontend จะส่งลิสต์ของวงกลมต่อกันมาเรื่อย ๆ โค้ดจะนำพิกัดมาระบายสีขาว (ค่า 1.0) ลงบนแผ่นดำ
4. `cv2.GaussianBlur(mask, ...)`: **ไม้เด็ดของความเนียน** แทนที่จะให้สีดำตัดกับสีขาวทันที (ขอบคมกระด้าง) เรานำตัวแผ่น Mask เองไปเบลอ ผลลัพธ์คือขอบวงกลมจะค่อย ๆ เฟดไล่โทนสีเทา ทำให้ภาพที่ผสมออกมาดูไม่ออกว่าตัดแปะ
5. `img * (1 - mask) + blurred * mask`: สมการ Linear Interpolation (Lerp) ทางคณิตศาสตร์คอมพิวเตอร์กราฟิกส์ที่ทำงานได้เร็วที่สุดบนหน่วยความจำของ NumPy

---

## 4. เจาะลึกระบบย่อยที่ 2: Hand Gesture Recognition (ตรวจจับท่าทางมือ)

### 4.1 คอนเซปต์แบบเข้าใจง่าย (ภาษาคน)
> **เปรียบเทียบ:**
> * **กระดูกมือ 21 จุด (Landmarks):** เหมือน AI เอาชอล์กมาจุดตามข้อนิ้วแต่ละข้อ ตั้งแต่โคนนิ้ว กลางนิ้ว ปลายนิ้ว ยันข้อมือ รวม 21 จุด ทำให้คอมพิวเตอร์ "รู้ว่านิ้วไหนกำลังงอ นิ้วไหนกำลังชี้ขึ้น"
> * **ทำไมต้องแยกโหมดรูปนิ่งกับโหมดเว็บแคม?**
>   * **โหมดรูปนิ่ง:** เหมือนส่งรูปถ่ายมาให้ดู 1 ใบ คอมพิวเตอร์มองแวบเดียวแล้วตอบ จบแล้วลืมได้เลย ไม่ต้องจำอะไรต่อ
>   * **โหมดเว็บแคม (วิดีโอ):** เหมือนคนกำลังเต้นอยู่หน้ากล้อง กล้องส่งภาพมาวินาทีละ 20-30 เฟรม ถ้าคอมพิวเตอร์ต้องมานั่งควานหามือใหม่ทุก ๆ เฟรมจะกระตุกและช้ามาก AI จึงต้อง "จำตำแหน่งจากเฟรมที่แล้ว" เพื่อตามมือต่อได้ทันที
>   * **ทำไมต้องแยก Session ต่อผู้ใช้?** เปรียบเหมือนเล่นเกม ถ้าผู้ใช้ A กับผู้ใช้ B ส่งภาพกล้องมาพร้อมกัน แล้วใช้ตัวจำเดียวกัน มือของนาย A จะไปกระตุกใส่นาย B ทันที! ระบบจึงต้องสร้างห้องจำลองแยกให้แต่ละคน (`_sessions[user_id]`)

---

### 4.2 ท่าทางมาตรฐานที่ระบบตรวจจับได้ (7 ท่าหลัก)

| ท่าทางที่ตรวจจับได้ | ชื่อภาษาไทย | ลักษณะที่ AI มองเห็น |
| :---: | :---: | :--- |
| **`Closed_Fist`** | กำมือ | ปลายนิ้วทั้ง 4 พับลงมาแตะที่โคนฝ่ามือ |
| **`Open_Palm`** | แบมือ | ปลายนิ้วทั้ง 5 กางออกและเหยียดตรง |
| **`Pointing_Up`** | ชี้นิ้วขึ้น | นิ้วชี้เหยียดขึ้นด้านบน นิ้วอื่นพับเก็บ |
| **`Thumb_Up`** | ชูนิ้วโป้ง | นิ้วโป้งชี้ขึ้น นิ้วทั้งสี่กำไว้ (ยอดเยี่ยม / Like) |
| **`Thumb_Down`** | คว่ำนิ้วโป้ง | นิ้วโป้งชี้ลงด้านล่าง นิ้วทั้งสี่กำไว้ (ไม่ชอบ / Dislike) |
| **`Victory`** | ชูสองนิ้ว | นิ้วชี้และนิ้วกลางกางเป็นรูปตัว V นิ้วอื่นพับเก็บ |
| **`ILoveYou`** | I Love You | นิ้วโป้ง, นิ้วชี้, นิ้วก้อยเหยียดออก นิ้วกลางและนางพับลง |

---

### 4.3 ซอร์สโค้ดจริงและการทำงาน (`backend/app/services/image_filters/gesture.py`)

#### โค้ดส่วนที่ 1: ระบบดาวน์โหลดโมเดลอัตโนมัติ (Auto-Download Model)
```python
# ไม่ต้องให้ผู้ใช้โหลดไฟล์เอง โค้ดจะจัดการให้ตั้งแต่รันครั้งแรก
def _model_path():
    """หาไฟล์โมเดล ถ้าในเครื่องยังไม่มี ให้ดาวน์โหลดจาก Google Storage มาเก็บไว้ให้อัตโนมัติ"""
    with _model_lock:
        if not MODEL_PATH.is_file():
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = MODEL_PATH.with_suffix(".part")
            # ดาวน์โหลดไฟล์ชั่วคราว (.part) ก่อน เพื่อป้องกันไฟล์เสียหากเน็ตหลุดกลางคัน
            urllib.request.urlretrieve(MODEL_URL, tmp)
            tmp.replace(MODEL_PATH)
    return str(MODEL_PATH)
```

#### โค้ดส่วนที่ 2: โหมดวิเคราะห์รูปภาพนิ่ง (Static Image)
```python
def recognize_gesture(img, num_hands=2, min_confidence=0.5):
    """โหมดรูปนิ่ง: ตรวจท่ามือจากภาพถ่ายเดี่ยว ๆ"""
    # OpenCV โหลดภาพเป็นสี BGR แต่โมเดลของ Google MediaPipe ต้องการสี RGB
    mp_image = _to_mp_image(img)
    
    # แคชโมเดลไว้ตามค่า Setting (เพื่อไม่ต้องสร้างโมเดลใหม่ทุกครั้งที่ผู้ใช้ส่งรูปมา)
    key = (num_hands, round(min_confidence, 1))

    with _image_lock:
        if key not in _image_recognizers:
            _image_recognizers[key] = _create_recognizer(vision.RunningMode.IMAGE, *key)
        
        # จับเวลาความเร็วในการประมวลผล (Inference Time)
        start = time.perf_counter()
        result = _image_recognizers[key].recognize(mp_image)
        inference_ms = (time.perf_counter() - start) * 1000

    # แปลงผลลัพธ์เป็น JSON Dictionary ภาษาไทย ส่งกลับหน้าเว็บ
    return _format(result, inference_ms)
```

#### โค้ดส่วนที่ 3: โหมดเว็บแคมเรียลไทม์ (Webcam Stream)
```python
def recognize_gesture_frame(img, user_id, num_hands=2, min_confidence=0.5):
    """โหมดเว็บแคม: รับภาพวิดีโอจากกล้องผู้ใช้คนใดคนหนึ่งแบบเรียลไทม์"""
    mp_image = _to_mp_image(img)
    key = (num_hands, round(min_confidence, 1))
    now = time.monotonic()

    with _video_lock:
        # ปิดโมเดลของคนที่ปิดกล้องหรือทิ้งหน้าเว็บไปเกิน 60 วินาที เพื่อคืนแรมให้เซิร์ฟเวอร์
        _close_idle_sessions(now)

        # ดึงห้องประจำตัว (Session) ของผู้ใช้คนนี้ ถ้าเพิ่งเปิดกล้องครั้งแรก ให้สร้างใหม่
        session = _sessions.get(user_id)
        if session is None or session["key"] != key:
            if session is not None:
                session["recognizer"].close()
            session = {
                "key": key,
                "recognizer": _create_recognizer(vision.RunningMode.VIDEO, *key),
                "last_ts": 0,
            }
            _sessions[user_id] = session

        # MediaPipe Video Mode บังคับว่าเวลา Timestamp ของแต่ละเฟรม ต้องเดินหน้าเสมอ ห้ามถอยหลัง
        # เราจึงใช้เวลาของเซิร์ฟเวอร์คุมเอง (+1 เพื่อป้องกันเฟรมมาชนกันในเสี้ยว millisecond เดียวกัน)
        timestamp_ms = max(session["last_ts"] + 1, int(now * 1000))
        session["last_ts"] = timestamp_ms
        session["last_used"] = now

        # สั่งให้ AI ทำนายท่าทางมือจากวิดีโอ
        start = time.perf_counter()
        result = session["recognizer"].recognize_for_video(mp_image, timestamp_ms)
        inference_ms = (time.perf_counter() - start) * 1000

    return _format(result, inference_ms)
```

---

## 5. เจาะลึกระบบย่อยที่ 3: Hybrid Background Removal (ระบบลบพื้นหลัง)

### 5.1 คอนเซปต์แบบเข้าใจง่าย (ภาษาคน)
> **ทำไมต้องเป็น "ไฮบริด (Hybrid)"?**
> * ถ้าใช้ **AI อย่างเดียว**: ตัดเร็วมาก แต่อาจจะมีบางจุดที่ AI ฉลาดไม่พอ เช่น ตัดสายนาฬิกาแหว่ง ตัดนิ้วเท้าหาย หรือตัดกระเป๋าเสื้อผ้าหลุดออกไป
> * ถ้าใช้ **มือตัดเอง (ลากกรอบ/ระบายแปรง)**: แม่นยำตรงใจผู้ใช้ แต่เหนื่อยและเสียเวลามาก
> * **ทางออกที่ดีที่สุด (Hybrid):** 
>   1. ให้ **AI MediaPipe วาดร่างนำไปก่อน** ว่าตรงไหนคือคน
>   2. ถ้าจุดไหน AI มองพลาด ผู้ใช้สามารถเอา **แปรงสีเขียว (Keep) มาป้ายบอกว่า "ตรงนี้เอาไว้"** หรือเอา **แปรงสีแดง (Remove) มาป้ายว่า "ตรงนี้ลบทิ้ง"**
>   3. จากนั้นส่งให้ **OpenCV GrabCut** (สุดยอดอัลกอริทึมวิเคราะห์สีกราฟ) คำนวณรอยต่อเส้นผมอย่างแม่นยำ
>   4. สุดท้ายใช้สูตร **Color Decontamination** ถอนสีสะท้อนของฉากหลังเดิมออกจากไรผม ทำให้ขอบไม่เรืองแสง ไม่ลอย

---

### 5.2 ซอร์สโค้ดจริงและการทำงาน (`backend/app/services/image_filters/remove_bg.py`)

#### โค้ดส่วนที่ 1: การลดขนาดรูปเพื่อความเร็ว และเตรียมข้อมูล
```python
def remove_background(img, rect=None, strokes=None, use_ai=True, bg_color=None):
    strokes = strokes or []
    H, W = img.shape[:2]

    # 1) ย่อรูปให้อยู่ในขนาดด้านยาวไม่เกิน 900px (WORK_SIDE = 900)
    # ภาษาคน: รูปถ่ายจากมือถือมักจะขนาด 4000x3000px ถ้าเอารูปยักษ์ไปตัด GrabCut เซิร์ฟเวอร์จะค้าง 5-10 วินาที
    # เราจึงย่อภาพลงมาคำนวณแบบเร็วจัด (เสร็จใน 0.2 วินาที) แล้วค่อยขยายผลลัพธ์กลับขนาดเดิม!
    s = min(1.0, WORK_SIDE / max(H, W))
    small = cv2.resize(img, (round(W * s), round(H * s)), interpolation=cv2.INTER_AREA) if s < 1 else img
    
    # ย่อสัดส่วนของกรอบสี่เหลี่ยมและเส้นแปรงที่ผู้ใช้วาดให้เล็กลงตามภาพ
    small_rect = [v * s for v in rect] if rect is not None else None
    small_strokes = [
        {"type": st["type"], "r": max(1, round(st["r"] * s)),
         "points": [[p[0] * s, p[1] * s] for p in st["points"]]}
        for st in strokes
    ]

    # 2) ส่งให้ AI หาความน่าจะเป็นของคน (0.0 - 1.0) ที่รูปย่อ
    person = _person_prob(small) if use_ai else None
    
    # 3) ทำการตัดฉากหลัง (ได้ค่า Alpha ความโปร่งใส 0 ถึง 1 ออกมา)
    alpha_small = _cut(small, person, small_rect, small_strokes)
```

#### โค้ดส่วนที่ 2: ผสมพลัง AI + แปรงระบาย + GrabCut
```python
def _cut(img, person, rect, strokes):
    H, W = img.shape[:2]

    # กรณีที่ 1: ผู้ใช้กดปุ่มออโต้ (ไม่ลากกรอบและไม่ระบายแปรง)
    # -> ใช้ผลลัพธ์จาก AI 100% เลย ทำงานเสร็จไวที่สุดในพริบตา
    if rect is None and not strokes:
        soft = np.clip((person - 0.3) / 0.4, 0, 1) # ทำขอบนุ่มตามความมั่นใจของ AI
        return _largest_blob(person > 0.5).astype(np.float32) * soft

    # กรณีที่ 2: มีการตีกรอบ หรือผู้ใช้วาดแปรงแก้ไขเพิ่มเติม -> ใช้ GrabCut
    # เตรียม Mask กำหนดสถานะ 4 รูปแบบให้ GrabCut:
    # GC_BGD    = พื้นหลังแน่นอน 100% (ข้างนอกกรอบที่ลาก)
    # GC_PR_BGD = น่าจะเป็นพื้นหลัง (ในกรอบ แต่ AI บอกว่าไม่ใช่คน)
    # GC_PR_FGD = น่าจะเป็นคน (ในกรอบ และ AI บอกว่าน่าจะใช่คน)
    # GC_FGD    = คนแน่นอน 100% (จุดที่ AI มั่นใจเกิน 90% หรือจุดที่ผู้ใช้เอาแปรง Keep ระบายทับ)
    mask = np.full((H, W), cv2.GC_BGD, np.uint8)
    
    # นำเส้นแปรงที่ผู้ใช้วาดมาระบายทับลงบน Mask (คำสั่งของผู้ใช้ถือเป็นเด็ดขาดที่สุด)
    for s in strokes:
        pts = np.array(s["points"], np.int32).reshape(-1, 2)
        value = cv2.GC_FGD if s["type"] == "keep" else cv2.GC_BGD
        r = max(1, int(s["r"]))
        if len(pts) == 1:
            cv2.circle(mask, (int(pts[0][0]), int(pts[0][1])), r, value, -1)
        else:
            cv2.polylines(mask, [pts], False, value, r * 2)

    # รันอัลกอริทึม GrabCut เพื่อคำนวณเส้นผมและขอบวัตถุ
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd_model, fgd_model, 4, cv2.GC_INIT_WITH_MASK)

    # กรองเศษฝุ่น Noise เล็ก ๆ ทิ้ง แต่เก็บตัวคนและจุดที่ผู้ใช้แต้ม keep ไว้เสมอ
    fg = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD))
    return _largest_blob(fg, extra=(mask == cv2.GC_FGD)).astype(np.float32)
```

#### โค้ดส่วนที่ 3: กำจัดขอบเรืองแสง (Color Decontamination)
```python
    # --------------------------------------------------------------------------
    # ถอนสีพื้นหลังเดิมที่สะท้อนติดขอบผม/ขอบเสื้อผ้าออก (Matting Equation)
    # --------------------------------------------------------------------------
    # ขยาย Mask กลับเป็นขนาดภาพจริงความละเอียดสูง
    alpha = cv2.resize(alpha_small, (W, H), interpolation=cv2.INTER_LINEAR)
    alpha = cv2.GaussianBlur(alpha, (0, 0), max(1.0, 1.0 / s))
    bg_old = cv2.resize(bg_small, (W, H), interpolation=cv2.INTER_LINEAR)

    # สมการ: สีจริง (F) = [สีที่เห็นในรูป (I) - (1 - alpha) * สีฉากหลังเดิม (B)] / alpha
    # ประโยชน์: ไรผมที่เคยมีสีเขียว/สีขาวของกำแพงติดอยู่ จะถูกหักสีนั้นทิ้งไป ทำให้ขอบผมเป็นสีธรรมชาติ
    a = alpha[:, :, None]
    I = img.astype(np.float32)
    F = np.clip((I - (1 - a) * bg_old) / np.maximum(a, 0.15), 0, 255)
    F = np.where(a > 0.95, I, F) # บริเวณกลางลำตัวคนใช้สีเดิม 100% ไม่ต้องคำนวณใหม่

    # ส่งออกภาพผลลัพธ์
    if bg_color is None:
        # คืนค่าเป็นภาพ PNG โปร่งใส 4 แชนเนล (Blue, Green, Red, Alpha)
        return np.dstack([F, alpha * 255]).astype(np.uint8)
    else:
        # นำสีฉากหลังใหม่ที่ผู้ใช้เลือก (เช่น สีขาว, สีฟ้า) มาเทใส่แทนที่
        out = F * a + np.array(bg_color, np.float32) * (1 - a)
        return out.astype(np.uint8)
```

---

## 6. จุดเชื่อมต่อ API ฝั่งเซิร์ฟเวอร์ (`backend/app/services/image_filters/routes.py`)

โค้ดส่วนนี้ทำหน้าที่เป็น **ยามเฝ้าประตู (Gatekeeper)** คอยตรวจความปลอดภัย รับไฟล์จากหน้าเว็บ แปลงไฟล์ และส่งคำตอบกลับ:

```python
@process_bp.route("/process/spot-blur", methods=["POST"])
@token_required # ตรวจสอบ JWT Token ป้องกันคนนอกยิง API
def process_spot_blur():
    # 1. ตรวจสอบไฟล์ภาพ
    file = request.files.get("image")
    if not file or not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return error_response(UNSUPPORTED_FILE_TYPE, "Only .jpg, .jpeg, .png, .webp are supported", 415)

    # 2. อ่านพิกัดวงกลม และระดับความแรง
    circles = json.loads(request.form.get("circles", "[]"))
    strength = int(request.form.get("strength", "10"))
    soft = request.form.get("soft", "true") == "true"

    # 3. แปลงไบนารีจากผู้ใช้ให้เป็น Image Matrix ของ OpenCV (BGR)
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # 4. ส่งให้ฟังก์ชันเบลอทำงาน
    result = spot_blur(img, circles, strength=strength, soft=soft)

    # 5. เข้ารหัสผลลัพธ์เป็นไฟล์ PNG แล้วสตรีมกลับไปให้ Browser แสดงผล
    png = cv2.imencode(".png", result)[1].tobytes()
    return send_file(BytesIO(png), mimetype="image/png")
```

---

## 7. สรุปภาพรวมแบบตาราง

| ฟีเจอร์ | เทคโนโลยีหลัก | ข้อดีที่ออกแบบไว้ | ปัญหาที่แก้ไข |
| :--- | :--- | :--- | :--- |
| **Spot Blur** | OpenCV Gaussian Blur | เกลี่ยขอบนุ่มด้วย Feathering | ขอบวงกลมไม่แข็งกระด้าง กลืนเข้ากับเนื้อภาพเดิม |
| **Gesture (รูปนิ่ง)** | MediaPipe Image Mode | มีระบบ Cache Recognizer ตามค่า Setting | ไม่ต้องเสียเวลาโหลดโมเดลใหม่ซ้ำ ๆ |
| **Gesture (เว็บแคม)** | MediaPipe Video Mode | แยก Session ต่อผู้ใช้ + สั่งปิดอัตโนมัติเมื่อหยุดใช้ | มือนิ่ง ไม่กระตุก และไม่กินแรมเซิร์ฟเวอร์ค้างไว้ |
| **Remove Background** | AI + GrabCut + Matting | ย่อรูปคำนวณเร็ว + ลบสีสะท้อนของฉากหลังเดิม | ประมวลผลไวในเสี้ยววินาที และขอบผมไม่เรืองแสง |
