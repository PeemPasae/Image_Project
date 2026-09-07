from functools import wraps
import jwt
from flask import current_app, g, request
from app.utils.errors import APIError


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise APIError("UNAUTHORIZED", "ไม่พบ token หรือ header ผิดรูปแบบ (ต้องเป็น 'Bearer <token>')")
        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise APIError("UNAUTHORIZED", "Token หมดอายุแล้ว กรุณา login ใหม่")
        except jwt.InvalidTokenError:
            raise APIError("UNAUTHORIZED", "Token ไม่ถูกต้อง")

        g.user_id = payload.get("user_id")
        g.user_email = payload.get("email")
        return f(*args, **kwargs)

    return decorated