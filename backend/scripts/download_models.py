# ==============================================================================
# ชื่อไฟล์: backend/scripts/download_models.py
# หน้าที่: สคริปต์สำหรับ Pre-download AI Models (MediaPipe / TFLite) ล่วงหน้า
#         เพื่อป้องกันปัญหา Cold Start และ Network Timeout ขณะที่ผู้ใช้เรียกใช้งาน
# ใช้งาน: python backend/scripts/download_models.py [--force]
# ==============================================================================

import os
import sys
import argparse
import urllib.request
from pathlib import Path

# ตำแหน่งโฟลเดอร์เก็บ Model: backend/ai_models/ หรือ backend/models/
BACKEND_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = (
    BACKEND_DIR / "ai_models"
    if (BACKEND_DIR / "ai_models").is_dir()
    else BACKEND_DIR / "models"
)

MODELS = [
    {
        "name": "Selfie Multiclass Segmentation (Remove Background)",
        "filename": "selfie_multiclass_256x256.tflite",
        "url": (
            "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
            "selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"
        ),
        "expected_min_bytes": 15 * 1024 * 1024,  # ~16 MB
    },
    {
        "name": "Gesture Recognizer (Hand Gesture Recognition)",
        "filename": "gesture_recognizer.task",
        "url": (
            "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
            "gesture_recognizer/float16/1/gesture_recognizer.task"
        ),
        "expected_min_bytes": 7 * 1024 * 1024,   # ~8 MB
    },
]


def _show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100.0, downloaded * 100.0 / total_size)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r    Progress: {percent:5.1f}% [{mb_downloaded:.1f} / {mb_total:.1f} MB]")
        sys.stdout.flush()


def download_all_models(force: bool = False) -> bool:
    """
    ตรวจสอบและดาวน์โหลดโมเดลทั้งหมดที่ระบบจำเป็นต้องใช้งาน
    :param force: บังคับดาวน์โหลดใหม่ทับของเดิม
    :return: True หากโมเดลทั้งหมดพร้อมใช้งาน
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print(f"[*] Checking and Pre-downloading AI Models into: {MODELS_DIR}")
    print("=" * 65)

    all_ok = True
    for item in MODELS:
        filepath = MODELS_DIR / item["filename"]
        print(f"\n[+] Model: {item['name']}")
        print(f"    Target: {filepath.name}")

        if filepath.is_file() and not force:
            size = filepath.stat().st_size
            if size >= item["expected_min_bytes"]:
                print(f"    Status: [READY] Already exists ({size / (1024 * 1024):.2f} MB)")
                continue
            else:
                print(f"    Status: Incomplete or corrupted file ({size} bytes). Re-downloading...")

        print(f"    Downloading from: {item['url']} ...")
        tmp_file = filepath.with_suffix(".download.part")
        try:
            urllib.request.urlretrieve(item["url"], tmp_file, reporthook=_show_progress)
            print()
            tmp_file.replace(filepath)
            final_size = filepath.stat().st_size
            print(f"    Status: [SUCCESS] Download completed ({final_size / (1024 * 1024):.2f} MB)")
        except Exception as e:
            print(f"\n    Status: [FAILED] Download error: {str(e)}")
            if tmp_file.exists():
                tmp_file.unlink()
            all_ok = False

    print("\n" + "=" * 65)
    if all_ok:
        print("[*] All AI Models are verified and ready for production use!")
    else:
        print("[!] Warning: Some models failed to download. Please check your internet connection.")
    print("=" * 65)
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-download AI models for LUMA image processing")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files already exist")
    args = parser.parse_args()
    success = download_all_models(force=args.force)
    sys.exit(0 if success else 1)
