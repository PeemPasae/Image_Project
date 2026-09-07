import datetime
import re

import jwt
from flask import Blueprint, current_app, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.utils.errors import APIError
from app.utils.response import success_response

auth_bp = Blueprint("auth", __name__)

MOCK_USERS_DB = {}
_next_id = 1
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_register_payload(data):
    email = (data or {}).get("email", "").strip().lower()
    password = (data or {}).get("password", "")
    if not email or not EMAIL_REGEX.match(email):
        raise APIError("VALIDATION_ERROR", "อีเมลไม่ถูกต้องหรือไม่ได้ระบุ")
    if not password or len(password) < 8:
        raise APIError("VALIDATION_ERROR", "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
    return email, password


@auth_bp.route("/register", methods=["POST"])
def register():
    global _next_id
    data = request.get_json(silent=True)
    email, password = _validate_register_payload(data)

    if email in MOCK_USERS_DB:
        raise APIError("EMAIL_EXISTS", "อีเมลนี้ถูกใช้ลงทะเบียนแล้ว")

    user = {
        "id": _next_id,
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    MOCK_USERS_DB[email] = user
    _next_id += 1

    return success_response(
        {"id": user["id"], "email": user["email"], "created_at": user["created_at"]},
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    email = (data or {}).get("email", "").strip().lower()
    password = (data or {}).get("password", "")

    if not email or not password:
        raise APIError("VALIDATION_ERROR", "ต้องระบุ email และ password")

    user = MOCK_USERS_DB.get(email)
    if not user or not check_password_hash(user["password_hash"], password):
        raise APIError("INVALID_CREDENTIALS", "อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    token = jwt.encode(
        {
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + current_app.config["JWT_EXPIRES_IN"],
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return success_response(
        {"token": token, "user": {"id": user["id"], "email": user["email"]}}
    )