# API สมัครสมาชิก / เข้าสู่ระบบ
import sqlite3
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "กรอกข้อมูลไม่ครบ"}), 400

    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return jsonify({"status": "success", "message": "ลงทะเบียนสำเร็จ"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username นี้ถูกใช้งานแล้ว"}), 400
    finally:
        conn.close()

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({
            "status": "success",
            "user": {"id": user['id'], "username": user['username']}
        })
    return jsonify({"status": "error", "message": "Username หรือ Password ไม่ถูกต้อง"}), 401