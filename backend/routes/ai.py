import requests
from flask import Blueprint, request, jsonify
from config import AI_SERVER_URL
from db import get_db_connection

ai_bp = Blueprint('ai', __name__)

# Helper function สำหรับจัดการการดึง API ฝั่ง AI Server ป้องกันแอปดับถ้า AI ล่ม
def call_sd_api(endpoint, method='GET', payload=None, timeout=60):
    url = f"{AI_SERVER_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        if method.upper() == 'POST':
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, timeout=timeout)
        
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"ไม่สามารถเชื่อมต่อ AI Server ({url}): {str(e)}"


# ===================================================================
# 1. CORE GENERATION (การสร้างและดัดแปลงรูปภาพ)
# ===================================================================

# [POST] Text-to-Image (สร้างภาพจากข้อความ)
@ai_bp.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.json
    user_id = data.get('user_id')
    prompt = data.get('prompt', '')

    payload = {
        "prompt": prompt,
        "negative_prompt": data.get('negative_prompt', ''),
        "seed": data.get('seed', -1),
        "steps": data.get('steps', 20),
        "cfg_scale": data.get('cfg_scale', 7),
        "width": data.get('width', 512),
        "height": data.get('height', 512),
        "sampler_name": data.get('sampler_name', 'Euler a'),
        "override_settings": {}
    }

    if data.get('checkpoint'):
        payload["override_settings"]["sd_model_checkpoint"] = data.get('checkpoint')

    res, error = call_sd_api("/sdapi/v1/txt2img", method='POST', payload=payload, timeout=120)
    if error:
        return jsonify({"status": "error", "message": error}), 500

    if res and 'images' in res and len(res['images']) > 0:
        img_b64 = "data:image/png;base64," + res['images'][0]
        
        # บันทึกลง Database
        if user_id:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO history (user_id, prompt, image_base64) VALUES (?, ?, ?)',
                (user_id, prompt, img_b64)
            )
            conn.commit()
            conn.close()

        return jsonify({"status": "success", "image": img_b64, "info": res.get("info")})
    
    return jsonify({"status": "error", "message": "AI ไม่สามารถสร้างรูปภาพได้"}), 500


# [POST] Image-to-Image (ปรับแปลงภาพเดิมด้วย Prompt - รองรับงานอนาคต)
@ai_bp.route('/api/img2img', methods=['POST'])
def img2img():
    data = request.json
    init_images = data.get('init_images', [])  # ส่งเป็น list ของ base64
    
    if not init_images:
        return jsonify({"status": "error", "message": "กรุณาส่งรูปภาพต้นฉบับ (init_images)"}), 400

    payload = {
        "init_images": init_images,
        "prompt": data.get('prompt', ''),
        "negative_prompt": data.get('negative_prompt', ''),
        "denoising_strength": data.get('denoising_strength', 0.75), # ค่าความเปลี่ยนแปลงจากรูปเดิม (0.0 - 1.0)
        "steps": data.get('steps', 20),
        "cfg_scale": data.get('cfg_scale', 7),
        "width": data.get('width', 512),
        "height": data.get('height', 512),
        "sampler_name": data.get('sampler_name', 'Euler a')
    }

    res, error = call_sd_api("/sdapi/v1/img2img", method='POST', payload=payload, timeout=120)
    if error:
        return jsonify({"status": "error", "message": error}), 500

    return jsonify({"status": "success", "images": res.get('images', [])})


# [POST] Extra / Upscale Image (ขยายขนาดภาพให้คมชัดขึ้น)
@ai_bp.route('/api/upscale', methods=['POST'])
def upscale_image():
    data = request.json
    image_base64 = data.get('image')

    payload = {
        "upscaling_resize": data.get('resize_factor', 2), # เช่น 2 เท่า
        "upscaler_1": data.get('upscaler', 'R-ESRGAN 4x+'),
        "image": image_base64
    }

    res, error = call_sd_api("/sdapi/v1/extra-single-image", method='POST', payload=payload, timeout=120)
    if error:
        return jsonify({"status": "error", "message": error}), 500

    return jsonify({"status": "success", "image": "data:image/png;base64," + res.get('image', '')})


# ===================================================================
# 2. MODEL & OPTIONS GETTERS (ดึงตัวเลือกต่าง ๆ ไปแสดงที่ UI)
# ===================================================================

# [GET] ดึงรายชื่อ Checkpoints/Models ทั้งหมด
@ai_bp.route('/api/models', methods=['GET'])
def get_models():
    res, error = call_sd_api("/sdapi/v1/sd-models", method='GET')
    if error:
        return jsonify({"status": "error", "message": error}), 500
    
    models = [m['title'] for m in res]
    return jsonify({"status": "success", "models": models})


# [GET] ดึงรายชื่อ Samplers ทั้งหมด (เช่น Euler a, DPM++ 2M)
@ai_bp.route('/api/samplers', methods=['GET'])
def get_samplers():
    res, error = call_sd_api("/sdapi/v1/samplers", method='GET')
    if error:
        return jsonify({"status": "error", "message": error}), 500

    samplers = [s['name'] for s in res]
    return jsonify({"status": "success", "samplers": samplers})


# [GET] ดึงรายชื่อ LoRA ทั้งหมดที่มีในเซิร์ฟเวอร์
@ai_bp.route('/api/loras', methods=['GET'])
def get_loras():
    res, error = call_sd_api("/sdapi/v1/loras", method='GET')
    if error:
        return jsonify({"status": "error", "message": error}), 500

    loras = [l['name'] for l in res]
    return jsonify({"status": "success", "loras": loras})


# ===================================================================
# 3. SYSTEM CONTROL (ตรวจสอบสถานะและตั้งค่า AI Server)
# ===================================================================

# [POST] สลับ Checkpoint Model ที่กำลังใช้งานหลักบนเซิร์ฟเวอร์
@ai_bp.route('/api/set-model', methods=['POST'])
def set_active_model():
    model_name = request.json.get('model_name')
    payload = {"sd_model_checkpoint": model_name}

    res, error = call_sd_api("/sdapi/v1/options", method='POST', payload=payload)
    if error:
        return jsonify({"status": "error", "message": error}), 500

    return jsonify({"status": "success", "message": f"เปลี่ยนโมเดลเป็น {model_name} เรียบร้อย"})


# [GET] เช็กสถานะการประมวลผล (Progress / Queue Status)
@ai_bp.route('/api/progress', methods=['GET'])
def get_progress():
    res, error = call_sd_api("/sdapi/v1/progress", method='GET')
    if error:
        return jsonify({"status": "error", "message": error}), 500

    return jsonify({
        "status": "success",
        "progress": res.get("progress", 0),
        "eta_relative": res.get("eta_relative", 0),
        "state": res.get("state", {})
    })