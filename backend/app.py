import os
import sqlite3
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# อัปเดต IP ของ AI Server (เครื่อง 172.20.57.51:8088)
AI_SERVER_IP = os.getenv('AI_SERVER_IP', 'http://172.20.57.51:8088')
DB_PATH = os.path.join(os.path.dirname(__file__), '../database/app.db')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            negative_prompt TEXT,
            checkpoint TEXT,
            image_base64 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Backend System Ready"}), 200

# 1. Register
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "ลงทะเบียนสำเร็จแล้ว!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "ชื่อผู้ใช้นี้ถูกใช้งานแล้ว"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 2. Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"status": "success", "user": {"id": user['id'], "username": user['username']}}), 200
    return jsonify({"status": "error", "message": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}), 401

# 3. Fetch Models จาก AI Server (172.20.57.51:8088)
@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        res = requests.get(f"{AI_SERVER_IP}/sdapi/v1/sd-models", timeout=10)
        models = [m['model_name'] for m in res.json()]
        return jsonify({"status": "success", "models": models}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"ไม่สามารถดึง Model จาก AI Server ({AI_SERVER_IP}) ได้: {str(e)}"}), 500

# 4. Generate Image
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json or {}
    user_id = data.get('user_id')
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    checkpoint = data.get('checkpoint', '')
    
    width = data.get('width', 1024)
    height = data.get('height', 1024)
    steps = data.get('steps', 20)
    cfg_scale = data.get('cfg_scale', 7)
    sampler_name = data.get('sampler_name', 'Euler a')

    if not user_id or not prompt:
        return jsonify({"status": "error", "message": "กรุณากรอก Prompt ให้ครบถ้วน"}), 400

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler_name
    }

    if checkpoint:
        payload["override_settings"] = {
            "sd_model_checkpoint": checkpoint
        }

    try:
        res = requests.post(f"{AI_SERVER_IP}/sdapi/v1/txt2img", json=payload, timeout=300)
        
        if res.status_code != 200:
            return jsonify({"status": "error", "message": f"AI Server Error ({res.status_code}): {res.text}"}), 400

        r = res.json()

        if 'images' in r and len(r['images']) > 0:
            img_b64 = f"data:image/png;base64,{r['images'][0]}"
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (user_id, prompt, negative_prompt, checkpoint, image_base64) VALUES (?, ?, ?, ?, ?)",
                (user_id, prompt, negative_prompt, checkpoint, img_b64)
            )
            conn.commit()
            conn.close()

            return jsonify({"status": "success", "image": img_b64}), 200
        
        return jsonify({"status": "error", "message": r.get('detail', 'AI ไม่สามารถสร้างรูปภาพได้')}), 400

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "AI Server ใช้เวลานานเกินไป (Timeout)"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Backend Error: {str(e)}"}), 500

# 5. History รายบุคคล
@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT prompt, negative_prompt, checkpoint, image_base64, created_at FROM history WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    history_list = [dict(row) for row in rows]
    return jsonify({"status": "success", "history": history_list}), 200

if __name__ == '__main__':
    # รันบนพอร์ต 5000 ของเครื่อง Backend Server (172.20.57.59)
    app.run(host='0.0.0.0', port=5000, debug=True)