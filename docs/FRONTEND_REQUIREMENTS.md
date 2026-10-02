# Frontend Requirements (สิ่งที่ frontend เรียกใช้จาก backend)

สกัดจากโค้ดจริงใน `frontend/luma-frontend/src/` เท่านั้น (อ่านอย่างเดียว) — path ทั้งหมดเทียบกับ `src/`
Base URL: `VITE_API_BASE_URL` หรือ default `http://localhost:5000/api/v1` (`api/client.js:7`)
Auth: ทุก request แนบ `Authorization: Bearer <luma_token>` ถ้ามี (`client.js:24-30`)
Envelope: JSON endpoint อ่าน `res.data.data` (`client.js:73`); error อ่าน `err.response.data.error.{code,message}` (`client.js:75-78`)
Global: ถ้า error code === `UNAUTHORIZED` (รวมกรณี body เป็น Blob) → ลบ `luma_token`/`luma_user` แล้ว redirect `/login` (`client.js:55-61`)
Fallback code: `ECONNABORTED` → `AI_SERVER_TIMEOUT`, อย่างอื่นที่ไม่มี code → `NETWORK_ERROR` (`client.js:78,92`)

---

## 1. Endpoint ทั้งหมด

| # | Method + Path | client.js | Timeout | Response |
|---|---|---|---|---|
| 1 | POST `/register` | :112 | 20s | JSON envelope |
| 2 | POST `/login` | :117 | 20s | JSON envelope |
| 3 | GET `/models` | :122 | 20s | JSON envelope |
| 4 | POST `/generate` | :134 | 90s (`GENERATE_TIMEOUT` :10) | JSON envelope |
| 5 | GET `/history` | :144 | 20s | JSON envelope |
| 6 | GET `/history/:id` | :152 | 20s | JSON envelope |
| 7 | DELETE `/history/:id` | :157 | 20s | JSON envelope |
| 8 | GET `/profile` | :162 | 20s | JSON envelope |
| 9 | GET `<imageUrl>` (ใช้จริง: `/api/v1/images/:id` หรือ `data.image_url`) | :171 | 20s | binary blob |
| 10 | POST `/process/spot-blur` | :189 | 20s | binary blob (PNG) |
| 11 | POST `/process/cartoonize` | :252→`processImage` :99-107 (call :198) | 20s | binary blob |
| 12 | POST `/process/tilt-shift` | call :207 | 20s | binary blob |
| 13 | POST `/process/hdr-enhancer` | call :217 | 20s | binary blob |
| 14 | POST `/process/gesture` | :233 | 20s | JSON envelope |
| 15 | POST `/process/remove-bg` | call :252 | 20s | binary blob |

หมายเหตุ #9: `getImageBlob` ตัด `/api/v1` ออกจาก base URL แล้วเรียก path ที่ได้รับตรงๆ (`client.js:171`) — ดังนั้น path ที่ component ส่งต้องมี `/api/v1/` นำหน้าเอง (`History.jsx:88`, `Home.jsx:79`) ส่วน `Result.jsx:21` ส่ง `data.image_url` จาก backend ตรงๆ → **ค่า `image_url` ต้องเป็น path เต็มที่รวม `/api/v1/...` ไม่แน่ใจ — ต้องตรวจสอบ** (mock ใช้ `/mock/images/:id`, contract test ใช้ `/images/42` ซึ่งไม่มี `/api/v1`)

หมายเหตุ: /process/* ที่เป็น blob ไม่มี timeout พิเศษ (ใช้ 20s default) — ไม่แน่ใจว่าพอสำหรับ remove-bg (AI) — ต้องตรวจสอบ

---

## 2. Field ที่ frontend ส่ง (request)

### POST /register  (`client.js:112`)
JSON body: `email`, `password` — จาก `pages/Register.jsx:37` → `AuthContext.jsx:32`

### POST /login  (`client.js:117`)
JSON body: `email`, `password` — จาก `pages/Login.jsx:30` → `AuthContext.jsx:26`
(frontend validate email ด้วย regex `^\S+@\S+\.\S+$` ที่ `Login.jsx:19`)

### POST /generate  (`client.js:134`, payload สร้างที่ `Generate.jsx:66-73`)
JSON body (ทั้งหมดมาจาก `form` state `Generate.jsx:8-18`):
| field | type | ค่า/ข้อจำกัดที่ frontend บังคับ (`Generate.jsx:45-54`) |
|---|---|---|
| `prompt` | string | จำเป็น, ≤2000 |
| `negative_prompt` | string | ≤2000 (default `''`) |
| `checkpoint` | string | = `models[].model_name` (`:34,115`) |
| `width`,`height` | number | 512/768/1024 เท่านั้น |
| `steps` | number | 1–50 |
| `cfg_scale` | number | 1–20 (step 0.5) |
| `sampler` | string | `DPM++ 2M Karras` / `Euler a` / `Euler` |
| `seed` | number | `-1` = random, หรือ 0–2147483647 (`:158`) |

### GET /history  (`client.js:144`) — ดู §4

### GET `/history/:id` (`client.js:152`) — จาก `Result.jsx:18` (`id` จาก useParams)
### DELETE `/history/:id` (`client.js:157`) — จาก `History.jsx:35`
### GET `/profile` (`client.js:162`) — ไม่ส่ง field จาก `Profile.jsx:11`

### POST /process/spot-blur (`client.js:184-188`, เรียกจาก `SpotBlurTool.jsx:48`)
multipart: `image` (file), `circles` (JSON string `[[x,y,r],...]` พิกเซลภาพต้นฉบับ), `strength` (ส่ง number ตรงๆ ผ่าน FormData → กลายเป็น string), `soft` (`"true"` เสมอจาก SpotBlurTool :48)

### POST /process/cartoonize (`client.js:198`, เรียกจาก `CartoonizeTool.jsx:38-40`)
multipart: `image`, `num_colors` (default 8), `line_thickness` (default 2), `smoothness` (default 5)

### POST /process/tilt-shift (`client.js:207`, `TiltShiftTool.jsx:40-46`)
multipart: `image`, `focus_position` (0.5), `focus_width` (0.2), `blur_strength` (15), `saturation_boost` (1.4), `contrast_boost` (1.2) — ค่าในวงเล็บคือ default ใน client.js:203-205

### POST /process/hdr-enhancer (`client.js:217`, `HdrEnhancerTool.jsx:39-44`)
multipart: `image`, `clahe_clip_limit` (3.0), `clahe_grid_size` (8), `detail_strength` (1.5), `color_balance` (`"true"`/`"false"`, default true)

### POST /process/gesture (`client.js:230-232`, `HandGestureTool.jsx:40`)
multipart: `image`, `num_hands` (1–4, UI slider `HandGestureTool.jsx:77`), `min_confidence` (0.1–1.0 step 0.1, `:82`)

### POST /process/remove-bg (`client.js:247-252`, `RemoveBackgroundTool.jsx:78-82`)
multipart: `image`, `bg` (default `"transparent"`; component ไม่เคยส่งค่าอื่น), `use_ai` (`"true"`/`"false"`), `rect` (JSON `[x,y,w,h]` — ส่งเฉพาะเมื่อมี), `strokes` (JSON `[{type:'keep'|'remove', r:int, points:[[x,y],..]}]` — ส่งเฉพาะเมื่อมี; shape จาก `RemoveBackgroundCanvas.jsx:157,204-208`)
Limit ฝั่ง frontend: ≤200 strokes, ≤5000 points รวม (`RemoveBackgroundTool.jsx:29-30,70`)
Rule: `use_ai=false` ต้องมี `rect` (`RemoveBackgroundTool.jsx:64`)

ไฟล์ที่รับ (frontend เช็คเอง): `ACCEPTED_IMAGE_TYPES` ใน `ImageUploader.jsx:23` (ข้อความ error ระบุ jpg/jpeg/png/webp)

---

## 3. Field จาก response ที่ frontend อ่านจริง

### POST /login → `data`
| field | อ่านที่ |
|---|---|
| `access_token` | `AuthContext.jsx:27` |
| `user` (ทั้ง object ถูกเก็บลง localStorage `luma_user`) | `AuthContext.jsx:27,20` |
| `user.email` | `Home.jsx:12,13`, `SoftLayout.jsx:48,50,51` |

(อ่านเฉพาะ `user.email`; ไม่พบการอ่าน `user.id` — แต่ contract test ใส่ `user.id`)

### POST /register → ไม่อ่าน field ใดจาก response (`Register.jsx:37` await เฉย ๆ). ไม่ได้เช็ค `message`.

### GET /models → `data`
- `data.models` — `Generate.jsx:32,33`
- `models[].model_name` — `Generate.jsx:34,115`
- `models[].title` — `Generate.jsx:115`
- Error: `.catch(() => setModels([]))` กลืน error ทั้งหมด (`Generate.jsx:37`)

### POST /generate → `data`
- `data.generation_id` — `Generate.jsx:75` (ใช้ navigate `/result/:id`)
- `image_url`, `seed`, `created_at` — **ไม่ถูกอ่าน** ที่ Generate (มีแค่ใน mock/contract test)

### GET /history → `data`
- `data.history` — `History.jsx:22`, `Home.jsx:24`
- `data.pagination` — `History.jsx:23`
  - `pagination.total` — `History.jsx:68` (`?? items.length` ถ้าไม่มี)
  - `pagination.total_pages` — `History.jsx:104,107,108`
  - `pagination.page` — `History.jsx:106,107,108`
  - (`pagination.limit` ไม่ถูกอ่าน)
- item fields: ดู §5

### GET /history/:id → `data` (`Result.jsx:18-21`)
| field | อ่านที่ |
|---|---|
| `image_url` | `Result.jsx:21` (ส่งเข้า `getImageBlob`) |
| `prompt` | `Result.jsx:45,72,77` |
| `negative_prompt` | `Result.jsx:46,78` |
| `checkpoint` | `Result.jsx:47,79` |
| `sampler` | `Result.jsx:52,80` |
| `width`,`height` | `Result.jsx:48,49,81` |
| `steps` | `Result.jsx:50,82` |
| `cfg_scale` | `Result.jsx:51,83` |
| `seed` | `Result.jsx:84` |
| `created_at` | `Result.jsx:85` (แสดงดิบ ไม่ format) |
| `generation_id` | `Result.jsx:67` (`generation.generation_id || id` — optional, มี fallback) |
(`id` ของ response ไม่ถูกอ่าน; ใช้ `id` จาก URL param)
ถ้าไม่มี `generation` ที่ปรับ prefill ใน Result: `steps/cfg_scale/sampler/negative_prompt` ถูกส่งต่อตรงๆ ไม่มี fallback (`Result.jsx:46,50-52`) — ถ้า backend ไม่ส่งจะได้ `undefined` แล้วถูก override ด้วย default ผ่าน `{...DEFAULTS, ...prefill}` เฉพาะกรณี key หายไปทั้งหมด (undefined value ใน spread จะ **ทับ** default เป็น undefined — ไม่แน่ใจ — ต้องตรวจสอบพฤติกรรมจริง)

### DELETE /history/:id → ไม่อ่าน field (`History.jsx:35`); ใช้แค่ success/failure. error → `err.message` toast (`History.jsx:39`)

### GET /profile → ดู §6

### GET image blob → binary (ใช้ `URL.createObjectURL(res.data)` `client.js:172`). ไม่อ่าน header.

### /process/spot-blur, cartoonize, tilt-shift, hdr-enhancer, remove-bg → binary body ใช้ทำ blob URL (`client.js:106,192`); ไม่อ่าน field/header ใด (ไม่เช็ค Content-Type)

### POST /process/gesture → `data` (`HandGestureTool.jsx`)
| field | อ่านที่ |
|---|---|
| `found` | :52 |
| `gesture` | :52 (`!= null`) |
| `gesture_th` | :92, :100 (fallback `'ไม่พบมือในภาพ'`) |
| `confidence` | :94 (`.toFixed(1)` → ต้องเป็น number ไม่เช่นนั้นพัง เมื่อ recognized) |
| `hand_count` | :95 |
| `inference_time_ms` | :96 (`.toFixed(1)` → ต้องเป็น number) |
ไม่อ่าน: `handedness`, `hands[]` (landmarks) — แม้ contract test จะ mock ไว้

---

## 4. Query parameters ที่ส่งจริง

| Endpoint | params | ที่มา |
|---|---|---|
| GET `/history` | `page` (default 1), `limit` (default 20) | `client.js:137,144`; เรียกที่ `History.jsx:20` (page, 20) และ `Home.jsx:23` (1, 4) |

**ไม่มีการส่ง `type` param** (หรือ `category`/filter ใดๆ) ไปที่ `/history` — ยืนยันจาก `client.js:144` ที่ส่งเฉพาะ `{ page, limit }`
Endpoint อื่นไม่ส่ง query param ใดเลย (id อยู่ใน path)

---

## 5. ส่วนพิเศษ: /history — field ที่อ่านจาก `history[]` item และความพร้อมรองรับ category ใหม่

### ทุกจุดที่อ่าน field จาก item
| field | ไฟล์:บรรทัด | ใช้ทำอะไร |
|---|---|---|
| `id` | `History.jsx:36,86,87,88,95,96`; `Home.jsx:77,79` | React key, link `/result/:id`, URL รูป `/api/v1/images/:id`, delete |
| `prompt` | `History.jsx:50,88(alt),91`; `Home.jsx:79(alt),82` | แสดง + prefill |
| `checkpoint` | `History.jsx:52,92`; `Home.jsx:84` | แสดง + prefill |
| `width`,`height` | `History.jsx:53,54,92`; `Home.jsx:85` | แสดง + prefill |
| `negative_prompt` | `History.jsx:51` | prefill (`|| ''`) |
| `steps` | `History.jsx:55` | prefill (`|| 20`) |
| `cfg_scale` | `History.jsx:56` | prefill (`|| 7`) |
| `sampler` | `History.jsx:57` | prefill (`|| 'DPM++ 2M Karras'`) |

### ผลการตรวจ
- **ไม่มีการอ่าน** `.category`, `.action_type`, `.type`, `.filter` ฯลฯ ที่ item ใดเลย (grep ทั้ง `src/**/*.jsx` ไม่พบ `.category`/`action_type`)
- **ไม่มีการ filter/แยกกลุ่ม/switch ตามค่า field ใด** — แสดงทุก item ในรูปแบบ card เดียวกันหมด
- ⇒ ถ้า backend เพิ่ม field/ค่า category ใหม่ (เช่น `"image_filter"`) frontend **จะไม่พัง ณ ระดับ field** (ไม่มีโค้ดที่ branch ตาม category) แต่ผลข้างเคียงที่เกิดได้ถ้า item ใหม่ปะปนใน list:
  1. **ทุก item ถูกเรนเดอร์เป็น generation เสมอ**: รูปโหลดจาก `/api/v1/images/:id` (`History.jsx:88`, `Home.jsx:79`) — ถ้า item ประเภท filter ไม่มีรูปที่ endpoint นี้ จะขึ้น "Image unavailable" (`AuthImage.jsx:37-39`) ไม่ crash
  2. ปุ่ม **"Again"** (`History.jsx:45-62`) จะ prefill ฟอร์ม Generate ด้วย `prompt/checkpoint/width/height` — ถ้า item ใหม่ไม่มี `checkpoint`/`prompt` (null) จะได้ค่า `undefined`/`null` ใน form → `Generate.jsx:46` `form.prompt.trim()` อาจ throw ถ้า `prompt` เป็น `null` (ไม่แน่ใจ — ต้องตรวจสอบ; `undefined` ถูกแทนด้วย default จาก spread? ไม่แน่ใจเช่นกัน, ดู §3 หมายเหตุ)
  3. `item.prompt` เป็น `alt` และแสดง div; null → แสดงว่างเปล่า ไม่ crash
  4. ลิงก์ไป `/result/:id` → `Result.jsx` อ่าน `generation.prompt` ฯลฯ ถ้า `GET /history/:id` คืน shape ต่างจากเดิมจะแสดง `undefined`/ว่าง ไม่ crash (ยกเว้น `data.image_url` หาย → `getImageBlob(undefined)` → `imageUrl.split` ใน mock / axios get undefined ใน real → error แสดงผ่าน `err.message`)
  5. count `pagination.total` (`History.jsx:68`) จะนับรวม item ประเภทใหม่ด้วย — ป้ายเขียนว่า "total generations"
- `history` ต้องเป็น array เสมอ: `History.jsx:22` set ตรง → `items.length`/`map` (`:77,85`) จะ crash ถ้าเป็น `undefined`/ไม่ใช่ array (contract test `.skip` อ้างปัญหานี้ที่ `contract.test.js:134`)
- เรียงลำดับ/แบ่งหน้า: frontend ไม่เรียงเอง เชื่อตามลำดับ backend

**สรุป: frontend ยังไม่พร้อมรองรับ category ใหม่ในแง่ UX (ไม่แยก/ไม่ filter/ไม่ส่ง `type`) แต่ไม่พังจาก category ที่ไม่คาดคิดเพราะไม่เคยอ่านค่านั้น**

---

## 6. ส่วนพิเศษ: /profile — field ที่ Profile.jsx อ่าน

`Profile.jsx:11` เก็บ `data` ทั้งก้อนลง state แล้วอ่าน:
| field | บรรทัด |
|---|---|
| `generation_count` | `Profile.jsx:26` |
| `email` | `Profile.jsx:31` |
| `id` | `Profile.jsx:32` (แสดงเป็น "User ID") |
| `created_at` | `Profile.jsx:33` (แสดงดิบ) |

- ไม่มีการเช็ค error code เฉพาะ — แสดง `err.message` (`Profile.jsx:11`)
- ถ้า backend แยก count (เช่น filter_count) ตัว frontend จะไม่แสดง — มีแค่ `generation_count`
- Field อื่นใน response ถูกเก็บใน state แต่ไม่ถูกใช้
- (ปุ่ม Change Password ถูก `disabled` — ไม่เรียก endpoint ใดๆ `Profile.jsx:36`)

---

## 7. Error code ที่ component เช็คเฉพาะเจาะจง

| Code | ไฟล์:บรรทัด | พฤติกรรม |
|---|---|---|
| `UNAUTHORIZED` | `client.js:55` | logout + redirect `/login` (ทุก endpoint ผ่าน interceptor, รวม blob error `:52-54`) |
| `AI_SERVER_BUSY` | `Generate.jsx:77` | ข้อความ "AI server is busy..." |
| `AI_SERVER_TIMEOUT` | `Generate.jsx:79` | ข้อความ "took too long..." (ยังเป็น code ที่ client.js สร้างเองเมื่อ `ECONNABORTED` `:78,92` ด้วย) |
| `GENERATION_NOT_FOUND` | `Result.jsx:25` | "This generation was not found." |
| `VALIDATION_ERROR`, `UNSUPPORTED_FILE_TYPE`, `INVALID_IMAGE`, `UNAUTHORIZED`, `MODEL_UNAVAILABLE` | `HandGestureTool.jsx:9-15` (lookup `:17`) | ข้อความไทย map ตาม code; code อื่น → `err.message` |
| `VALIDATION_ERROR`, `UNSUPPORTED_FILE_TYPE`, `INVALID_IMAGE`, `MODEL_UNAVAILABLE`, `GENERATION_FAILED`, `UNAUTHORIZED` | `RemoveBackgroundTool.jsx:8-15` (lookup `:17`) | ข้อความไทย map ตาม code |
| `NETWORK_ERROR` | สร้างที่ `client.js:78,92` | ไม่มี component เช็คเฉพาะ |

ที่ **ไม่เช็ค code** (ใช้ `err.message` ล้วน): Login (`Login.jsx:33`), Register (`Register.jsx:41`), History load/delete (`History.jsx:25,39`), Profile (`Profile.jsx:11`), SpotBlur (`SpotBlurTool.jsx:52`), Cartoonize (`CartoonizeTool.jsx:44`), TiltShift (`TiltShiftTool.jsx:50`), HdrEnhancer (`HdrEnhancerTool.jsx:48`)
⇒ `INVALID_CREDENTIALS` (ที่ contract test ใช้) ไม่ได้ถูกเช็คโดย component ใด — แสดงผ่าน `message` เท่านั้น. `Result.jsx` ส่วน 401/404 อื่นๆ ใช้ message.
`message` จาก backend จึงถูกแสดงต่อ user ตรงๆ ในหลายหน้า — ควรเป็นข้อความอ่านได้

---

## 8. `src/test/contract.test.js` — contract ที่ lock ไว้

(mock axios; ทดสอบผ่าน `api.*` ใน client.js)

| describe / it | Endpoint ที่ครอบคลุม | บรรทัด | สิ่งที่ lock |
|---|---|---|---|
| login contract / returns access_token and user | POST /login | :38-46 | `access_token`, `user.email` |
| login / throws with .code on invalid credentials | POST /login | :48-55 | `INVALID_CREDENTIALS` map → `.code` |
| getModels contract | GET /models | :58-67 | `models[].model_name`, `.title` |
| generate contract / returns generation_id | POST /generate | :70-78 | `generation_id` (response ตัวอย่างมี `image_url/seed/created_at` แต่ไม่ assert) |
| getHistory contract | GET /history | :81-97 | `history[]` มี `id`,`prompt`(string); `pagination.page`,`total_pages` (number) |
| getGeneration contract | GET /history/:id | :100-109 | `image_url`,`seed`,`created_at` (ไม่ assert `prompt/checkpoint/steps/...` ที่ Result อ่านจริง) |
| getProfile contract | GET /profile | :112-121 | `generation_count`,`email`,`created_at` (ไม่ assert `id` ที่ Profile.jsx:32 อ่าน) |
| error normalization | POST /generate | :124-131 | `ECONNABORTED` → `AI_SERVER_TIMEOUT` |
| regression (bare array) | GET /history | :133-145 | **`it.skip`** — ไม่ได้รันจริง |
| processSpotBlur (2 tests) | POST /process/spot-blur | :146-188 | multipart `image/circles/strength/soft`, blob URL, config, blob error → `.code` |
| processCartoonize (2) | POST /process/cartoonize | :190-231 | ฟิลด์ 3 ตัว, blob error `VALIDATION_ERROR` |
| processTiltShift (2) | POST /process/tilt-shift | :233-282 | ฟิลด์ 5 ตัว, blob error |
| processHdrEnhancer (2) | POST /process/hdr-enhancer | :284-331 | ฟิลด์ 4 ตัว (`color_balance` เป็น string), blob error |
| processGesture (5) | POST /process/gesture | :333-431 | ฟิลด์ที่ส่ง, default 2/0.5, found:false/null, `VALIDATION_ERROR`, `MODEL_UNAVAILABLE`; ไม่มี responseType |
| processRemoveBackground (7) | POST /process/remove-bg | :433-540 | bg, default transparent, rect/strokes JSON, use_ai string, omit rect/strokes, `UNSUPPORTED_FILE_TYPE`, `MODEL_UNAVAILABLE` |
| response interceptor — UNAUTHORIZED (2) | ทุก endpoint (interceptor) | :542-576 | blob body และ JSON body → ล้าง `luma_token`/`luma_user` |

**ไม่มี test ครอบคลุม**: POST `/register`, DELETE `/history/:id`, GET image blob (`getImageBlob`), `GET /history` ที่ส่ง `params {page,limit}` (ไม่ assert query), และ **ไม่มี test ของ category/type/filter ใดๆ**

---

## 9. สิ่งที่ "ไม่แน่ใจ — ต้องตรวจสอบ" (สรุป)
1. ค่า `image_url` จาก `/generate` และ `/history/:id` ต้องมี prefix `/api/v1` หรือไม่ (`Result.jsx:21` + `client.js:171`) — contract test ใช้ `/images/:id`
2. Timeout 20s ของ /process/* (โดยเฉพาะ remove-bg/AI) เพียงพอหรือไม่
3. พฤติกรรม prefill เมื่อ item ใน history/result ไม่มี `prompt`/`checkpoint`/`steps` ฯลฯ (null/undefined) กับ `Generate.jsx` validate
4. ค่า `user` object ที่ `/login` คืน — frontend ใช้แค่ `email` (ไม่ทราบว่าควรมี field อื่น)
5. ไฟล์ type/ขนาดที่ backend รับจริง — frontend ตรวจเฉพาะ `ACCEPTED_IMAGE_TYPES` (`ImageUploader.jsx:23`) ไม่ตรวจขนาดไฟล์ (ไม่ได้ตรวจเจาะรายละเอียดบรรทัดนี้ — ต้องตรวจสอบ)
