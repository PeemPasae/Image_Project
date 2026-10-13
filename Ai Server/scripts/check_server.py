"""
check_server.py — เช็คสุขภาพ AI Server ก่อนบอกทีมว่า "เซิร์ฟเวอร์พร้อมแล้ว"

ตรวจ 3 อย่างตามลำดับ:
  1. /internal/ping หรือ /sdapi/v1/options  -> เซิร์ฟเวอร์ตอบไหม / เปิด --api หรือยัง
  2. /sdapi/v1/sd-models                    -> endpoint ที่ Backend เรียกตอน GET /api/models
  3. /sdapi/v1/samplers                     -> ชื่อ sampler ที่ frontend เลือกได้จริง

    python scripts/check_server.py
    python scripts/check_server.py --url http://127.0.0.1:8088
"""

import argparse
import os
import sys

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


def get(base, path, timeout=10):
    return requests.get(f"{base}{path}", timeout=timeout)


def main():
    p = argparse.ArgumentParser(description="health check ของ AI Server")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--timeout", type=int, default=10)
    args = p.parse_args()
    base = args.url.rstrip("/")

    print(f"ตรวจ AI Server: {base}\n" + "-" * 60)
    failed = False

    # 1) เซิร์ฟเวอร์ตอบไหม
    try:
        res = get(base, "/sdapi/v1/options", args.timeout)
    except requests.exceptions.RequestException as e:
        sys.exit(f"[FAIL] ต่อไม่ได้: {e}\n       เช็ค: webui รันอยู่ไหม / --listen --port 8088 / firewall เปิดพอร์ต 8088 หรือยัง")

    if res.status_code == 404:
        sys.exit("[FAIL] เซิร์ฟเวอร์ตอบ แต่ไม่มี /sdapi/v1/* — ลืมใส่ --api ใน COMMANDLINE_ARGS")
    if res.status_code != 200:
        sys.exit(f"[FAIL] /sdapi/v1/options -> HTTP {res.status_code}")

    opts = res.json()
    print("[OK] API online")
    print(f"     checkpoint ที่โหลดอยู่: {opts.get('sd_model_checkpoint')}")

    # 2) รายชื่อ model ที่ Backend จะเอาไปโชว์
    try:
        res = get(base, "/sdapi/v1/sd-models", args.timeout)
        res.raise_for_status()
        models = res.json()
        if not models:
            print("[WARN] ไม่มี checkpoint เลย — วางไฟล์ .safetensors ใน models/Stable-diffusion/ ก่อน")
            failed = True
        else:
            print(f"[OK] sd-models: {len(models)} ตัว")
            for m in models:
                print(f"     - {m['model_name']}")
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] /sdapi/v1/sd-models: {e}")
        failed = True

    # 3) sampler ที่ใช้ได้จริง (backend default = 'Euler a')
    try:
        res = get(base, "/sdapi/v1/samplers", args.timeout)
        res.raise_for_status()
        names = [s["name"] for s in res.json()]
        print(f"[OK] samplers: {len(names)} ตัว -> {', '.join(names[:8])}{' ...' if len(names) > 8 else ''}")
        if "Euler a" not in names:
            print("[WARN] ไม่มี 'Euler a' ซึ่งเป็นค่า default ของ Backend — ต้องบอกพี่นายให้เปลี่ยน")
            failed = True
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] /sdapi/v1/samplers: {e}")
        failed = True

    print("-" * 60)
    print("สรุป: " + ("มีบางอย่างต้องแก้ ดู [FAIL]/[WARN] ด้านบน" if failed else "AI Server พร้อมใช้งาน"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
