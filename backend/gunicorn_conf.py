# ==============================================================================
# ชื่อไฟล์: backend/gunicorn_conf.py
# หน้าที่: คอนฟิกูเรชันสำหรับรัน Production WSGI Server (Gunicorn) บน Linux / Docker
# วิธีรัน: gunicorn -c gunicorn_conf.py run:app
# ==============================================================================

import os
import multiprocessing

# ที่อยู่และพอร์ตที่ต้องการเปิดรับการเชื่อมต่อ
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 5000)}"

# ------------------------------------------------------------------------------
# ⚠️ สถาปัตยกรรมสำคัญ: ทำไมต้อง workers = 1 และใช้ threads ?
# ------------------------------------------------------------------------------
# ระบบนี้มีการใช้ threading.Lock() เพื่อคุมคิวการประมวลผลบน GPU (AI Stable Diffusion)
# หากใช้ workers > 1 (หลาย OS Process) แต่ละ Worker จะไม่แชร์ Memory Lock กัน
# ส่งผลให้หลาย Process ส่งคำขอเข้าไปชนกันบน GPU จนเกิด Out-of-Memory (OOM)
# 
# ทางเลือกที่เสถียรที่สุดสำหรับเซิร์ฟเวอร์เดี่ยว (Single Node) คือ:
# - workers = 1 (Single Process เพื่อให้ GPU Mutex Lock มีผลสมบูรณ์ 100%)
# - threads = 8 ถึง 16 (ใช้ Multi-threading เพื่อรับคำขอทั่วไป เช่น Profile, History, Stream Image ได้พร้อมกัน)
workers = int(os.getenv("GUNICORN_WORKERS", 1))
threads = int(os.getenv("GUNICORN_THREADS", 8))

# เวลาสูงสุดที่ยอมให้คำขอประมวลผล (วินาที)
# กำหนดเป็น 120 เพื่อให้ครอบคลุมการเจนภาพ AI (timeout 75s + overhead) ไม่ให้ถูกตัดก่อน
timeout = 120
graceful_timeout = 30
keepalive = 5

# การบันทึก Log ของ Gunicorn
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"   # ส่งออก stdout
errorlog = "-"    # ส่งออก stderr

# รูปแบบ Log มาตรฐาน
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(D)s µs)'

