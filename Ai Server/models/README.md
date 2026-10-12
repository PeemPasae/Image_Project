# models/

โฟลเดอร์สำหรับวางไฟล์ checkpoint — **ไฟล์จริงไม่ถูก commit ขึ้น git** (ดู `.gitignore`)

```
models/
├── Stable-diffusion/   # .safetensors / .ckpt  (checkpoint หลัก)
├── VAE/                # .vae.pt / .safetensors
└── Lora/               # LoRA เสริม
```

## checkpoint ที่ใช้ในโปรเจกต์นี้

| ชื่อ (model_name ที่ Backend เห็น) | ไฟล์ | ที่มา | ขนาด |
|---|---|---|---|
| _(เติมเมื่อโหลดจริง)_ | `sd_xl_base_1.0.safetensors` | huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 | ~6.9 GB |

> ชื่อในคอลัมน์แรกคือค่าที่ Frontend ส่งกลับมาเป็น `checkpoint` และ Backend เอาไปใส่
> `override_settings.sd_model_checkpoint` ตรวจชื่อจริงได้ด้วย
> `python scripts/check_server.py`

## วิธีเพิ่ม checkpoint ใหม่

1. วางไฟล์ใน `models/Stable-diffusion/`
2. เรียก `POST /sdapi/v1/refresh-checkpoints` หรือ restart webui
3. `python scripts/check_server.py` เพื่อดูว่าชื่อขึ้นแล้ว
4. แจ้งพี่นาย (Backend) + กร (Frontend) ว่ามีตัวเลือกใหม่
