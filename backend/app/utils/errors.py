from flask import jsonify

ERROR_CODES = {
    "VALIDATION_ERROR": 400,
    "INVALID_CREDENTIALS": 401,
    "UNAUTHORIZED": 401,
    "EMAIL_EXISTS": 409,
    "GENERATION_NOT_FOUND": 404,
    "IMAGE_NOT_FOUND": 404,
    "AI_SERVER_BUSY": 409,
    "MODEL_UNAVAILABLE": 503,
    "AI_SERVER_ERROR": 502,
    "AI_SERVER_TIMEOUT": 504,
    "GENERATION_FAILED": 500,
    "INTERNAL_SERVER_ERROR": 500,
}
class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code or ERROR_CODES.get(code, 500)

def error_response(code: str, message: str, status_code: int | None = None):
    status_code = status_code or ERROR_CODES.get(code, 500)
    return (
        jsonify({"success": False, "error": {"code": code, "message": message}}),
        status_code,
    )

def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        return error_response(err.code, err.message, err.status_code)

    @app.errorhandler(404)
    def handle_404(_err):
        return error_response("INTERNAL_SERVER_ERROR", "ไม่พบ route นี้", 404)

    @app.errorhandler(405)
    def handle_405(_err):
        return error_response("INTERNAL_SERVER_ERROR", "HTTP method ไม่ถูกต้องสำหรับ route นี้", 405)

    @app.errorhandler(500)
    def handle_500(_err):
        return error_response("INTERNAL_SERVER_ERROR", "เกิดข้อผิดพลาดที่ server", 500)