# API สั่งงาน AI Server และดึง Models
import requests
from flask import Blueprint, request, jsonify
from db import get_db_connection

ai_bp = Blueprint('ai', __name__)
AI_SERVER_URL = "http://172.20.57.51:8088"

@ai_bp.route('/api/models', methods=['GET'])
def get_models():
    try:
        res = requests.get(f"{AI_SERVER_URL}/sdapi/v1/sd-models", timeout=5)
        models = [m['title'] for m in res.json()]
        return jsonify({"status": "success", "models": models})
    except Exception:
        return jsonify({"status": "error", "message": "ไม่สามารถติดต่อ AI Server ได้"}), 500

@ai_bp.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.json
    user_id = data.get('user_id')
    prompt = data.get('prompt')
    
    payload = {
        "prompt": prompt,
        "negative_prompt": data.get('negative_prompt', ''),
        "override_settings": {"sd_model_checkpoint": data.get('checkpoint')},
        "width": data.get('width', 512),
        "height": data.get('height', 512),
        "sampler_name": data.get('sampler_name', 'Euler a'),
        "steps": data.get('steps', 20),
        "cfg_scale": data.get('cfg_scale', 7)
    }

    try:
        response = requests.post(f"{AI_SERVER_URL}/sdapi/v1/txt2img", json=payload, timeout=120)
        res_data = response.json()
        
        if 'images' in res_data and len(res_data['images']) > 0:
            img_b64 = "data:image/png;base64," + res_data['images'][0]
            
            conn = get_db_connection()
            conn.execute('INSERT INTO history (user_id, prompt, image_base64) VALUES (?, ?, ?)',
                         (user_id, prompt, img_b64))
            conn.commit()
            conn.close()

            return jsonify({"status": "success", "image": img_b64})
        return jsonify({"status": "error", "message": "AI ไม่สามารถสร้างรูปภาพได้"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"การเชื่อมต่อ AI ล้มเหลว: {str(e)}"}), 500