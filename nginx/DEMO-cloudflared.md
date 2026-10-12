# เปิดเดโมนอกวง LAN ด้วย Cloudflare Tunnel (ชั่วคราว)

> ใช้ตอน **เดโมให้รุ่นน้อง/อาจารย์เข้ามาลองเล่น** จากที่ไหนก็ได้ ไม่ต้องอยู่วง Wi‑Fi เดียวกัน
> เป็น **quick tunnel** — เปิดเฉพาะตอนเดโม กด Ctrl+C แล้ว URL ตายทันที ไม่ต้องมีบัญชี Cloudflare

## หลักการ

```
รุ่นน้อง (เน็ตที่ไหนก็ได้)
   │  https://xxx.trycloudflare.com
   ▼
Cloudflare ──(tunnel)──▶ cloudflared บนเครื่องเรา ──▶ nginx :80 ──┬─ / (หน้าเว็บ)
                                                                  └─ /api/v1/* (Flask)
```

cloudflared ชี้เข้า **nginx :80 อย่างเดียว** → หลังบ้าน (`:8089` SD WebUI, `:5000`, `:8088`) **ไม่ออกไปนอกเน็ต** และได้ **HTTPS ฟรี** จาก Cloudflare (JWT ไม่วิ่ง plain text)

## เตรียมก่อนเดโม (ทำครั้งเดียว — ทำไปแล้ว)

- ✅ `cloudflared.exe` อยู่ที่ `C:\nginx\cloudflared.exe`
- ✅ nginx อ่าน IP จริงจาก `CF-Connecting-IP` แล้ว (rate limit นับแยกรายคน ไม่ใช่รวมกันเป็น 127.0.0.1)

## ขั้นตอนวันเดโม

**1. เปิดของหลังบ้านให้ครบก่อน** (3 อย่าง)
```powershell
# backend
cd "C:\Learn Uni\Y3\Term1\Image processing\ProjectFinal\Image_Project\backend"
python run.py
# SD WebUI (webui-user.bat)  — อีกหน้าต่าง
# nginx — ถ้ายังไม่รัน:  cd C:\nginx ; .\nginx.exe
```
เช็ค: เปิด `http://172.20.56.158/` ในเครื่องตัวเองต้องเห็นหน้าเว็บ + login/generate ได้

**2. เปิด tunnel**
```powershell
cd "C:\Learn Uni\Y3\Term1\Image processing\ProjectFinal\Image_Project"
powershell -ExecutionPolicy Bypass -File nginx\scripts\demo-tunnel.ps1
```
รอสักครู่จะเห็นบรรทัดแบบนี้ในหน้าต่าง:
```
https://random-words-xxxx.trycloudflare.com
```
**นั่นคือ URL เดโม** — ก๊อปแจกในกลุ่ม/ฉายบนจอ

**3. เดโมเสร็จ → กด `Ctrl+C`** ในหน้าต่าง tunnel → URL ใช้ไม่ได้ทันที

## ระหว่างเดโม ดูว่าใครเข้ามาบ้าง

```powershell
Get-Content C:\nginx\logs\luma.access.log -Wait -Tail 15
```
จะเห็น **IP จริงของรุ่นน้องแต่ละคน** (ไม่ใช่ 127.0.0.1) พร้อม status

## ข้อควรรู้ / ข้อจำกัด (สำคัญตอนเดโม)

| เรื่อง | รายละเอียด |
|---|---|
| **GPU ทำทีละคน** | SD เจนได้ทีละรูป ถ้ารุ่นน้องกดพร้อมกัน คนที่ 2 จะได้ `AI_SERVER_BUSY` (ถูกต้องตาม spec) — บอกให้ผลัดกันกด |
| **user เก็บใน memory** | สมัคร/ล็อกอินได้ แต่ถ้า restart backend ข้อมูล user + ประวัติหายหมด (auth.py ยังใช้ MOCK DB) |
| **URL เปลี่ยนทุกครั้ง** | quick tunnel สุ่ม URL ใหม่ทุกรอบที่เปิด — แจกใหม่ทุกครั้ง |
| **หลังบ้านปลอดภัย** | `:8089`/`:5000`/`:8088` ไม่ออก tunnel; `/_dev/` ต่อให้เดา URL ได้ก็เจอ 403 (IP จริงไม่อยู่ใน allowlist) |
| **rate limit** | login 10/นาที/คน, API 120/นาที/คน — พอสำหรับเล่น ถ้าเจอ 429 บ่อยตอนคนเยอะ บอกผมปรับเพิ่มได้ |

## ไม่ต้องแก้ nginx.conf กลับ

config เดียวใช้ได้ทั้ง LAN ปกติและตอนเดโม — real_ip เชื่อเฉพาะ 127.0.0.1 (cloudflared) เท่านั้น เวลาไม่เปิด tunnel ก็ไม่มีผลอะไร
