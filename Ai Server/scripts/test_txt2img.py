"""
test_txt2img.py — ยิง /sdapi/v1/txt2img ตรงเข้า AI Server (ไม่ผ่าน Backend)

ใช้ payload ชุดเดียวกับที่ backend/app.py ส่งมาเป๊ะๆ
เพื่อให้ถ้าสคริปต์นี้ผ่าน แปลว่าปัญหาไม่ได้อยู่ที่ฝั่ง AI Server

ตัวอย่าง:
    python scripts/test_txt2img.py
    python scripts/test_txt2img.py -p "a cat astronaut, cinematic lighting" --steps 30
    python scripts/test_txt2img.py --checkpoint "sd_xl_base_1.0" --width 768 --height 768
    python scripts/test_txt2img.py --url http://127.0.0.1:8088
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime

# Windows console default เป็น cp1252 พิมพ์ภาษาไทยแล้ว UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

try:
    import requests
except ImportError:
    sys.exit("ยังไม่ได้ติดตั้ง requests -> pip install -r scripts/requirements.txt")

DEFAULT_URL = os.getenv("AI_SERVER_URL", "http://172.20.57.51:8088")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")


def parse_args():
    p = argparse.ArgumentParser(description="ทดสอบ txt2img ตรงเข้า AI Server")
    p.add_argument("--url", default=DEFAULT_URL, help=f"base URL ของ AI Server (default: {DEFAULT_URL})")
    p.add_argument("-p", "--prompt", default="a photo of a red apple on a wooden table, 4k, sharp focus")
    p.add_argument("-n", "--negative-prompt", default="blurry, lowres, watermark, text")
    p.add_argument("--checkpoint", default="", help="ชื่อ model_name จาก /sdapi/v1/sd-models (ปล่อยว่าง = ใช้ตัวที่โหลดอยู่)")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--cfg-scale", type=float, default=7)
    p.add_argument("--sampler-name", default="Euler a")
    p.add_argument("--timeout", type=int, default=300, help="วินาที (backend ตั้งไว้ 300)")
    p.add_argument("--no-save", action="store_true", help="ไม่ต้องเซฟรูปลง outputs/")
    return p.parse_args()


def build_payload(a):
    """payload ต้องตรงกับ backend/app.py -> /api/generate"""
    payload = {
        "prompt": a.prompt,
        "negative_prompt": a.negative_prompt,
        "steps": a.steps,
        "width": a.width,
        "height": a.height,
        "cfg_scale": a.cfg_scale,
        "sampler_name": a.sampler_name,
    }
    if a.checkpoint:
        payload["override_settings"] = {"sd_model_checkpoint": a.checkpoint}
    return payload


def main():
    a = parse_args()
    base = a.url.rstrip("/")
    payload = build_payload(a)

    print(f"AI Server : {base}")
    print(f"Payload   : {json.dumps(payload, ensure_ascii=False, indent=2)}")
    print("-" * 60)

    started = time.time()
    try:
        res = requests.post(f"{base}/sdapi/v1/txt2img", json=payload, timeout=a.timeout)
    except requests.exceptions.Timeout:
        sys.exit(f"[FAIL] Timeout เกิน {a.timeout}s — steps/ขนาดรูปสูงไป หรือ GPU ยังโหลด model อยู่")
    except requests.exceptions.ConnectionError as e:
        sys.exit(f"[FAIL] ต่อ {base} ไม่ได้ — เช็คว่า webui รันด้วย --api --listen --port 8088 แล้วหรือยัง\n{e}")

    elapsed = time.time() - started

    if res.status_code != 200:
        sys.exit(f"[FAIL] HTTP {res.status_code}\n{res.text[:2000]}")

    body = res.json()
    images = body.get("images") or []
    if not images:
        sys.exit(f"[FAIL] ไม่มี images กลับมา: {body.get('detail', body)}")

    print(f"[OK] สร้างรูปสำเร็จใน {elapsed:.1f}s  ({len(images)} รูป)")

    info = body.get("info")
    if info:
        try:
            i = json.loads(info)
            print(f"     model  : {i.get('sd_model_name')}")
            print(f"     seed   : {i.get('seed')}")
            print(f"     sampler: {i.get('sampler_name')}")
        except (ValueError, TypeError):
            pass

    if a.no_save:
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for idx, b64 in enumerate(images):
        # ตัด data URI prefix ถ้ามี (backend เป็นคนเติมเองตอนส่งให้ frontend)
        raw = b64.split(",", 1)[-1] if b64.startswith("data:") else b64
        path = os.path.join(OUTPUT_DIR, f"test_{stamp}_{idx}.png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(raw))
        print(f"     saved  : {path}")


if __name__ == "__main__":
    main()
