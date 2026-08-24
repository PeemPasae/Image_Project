# API ดึงประวัติการใช้งาน
from flask import Blueprint, jsonify
from db import get_db_connection

history_bp = Blueprint('history', __name__)

@history_bp.route('/api/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT prompt, image_base64, created_at FROM history WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    
    history = [dict(row) for row in rows]
    return jsonify({"status": "success", "history": history})