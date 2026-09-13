from unittest.mock import patch
from app.services.ai_client import (
    AIServerBusyException,
    AIServerTimeoutException,
)


def test_generate_validation_error(client, auth_headers):
    """TC-VAL-001 & TC-VAL-002: ตรวจสอบ Validation พารามิเตอร์ไม่ถูกต้อง"""
    # Prompt ว่าง
    res = client.post("/api/v1/generate", json={"prompt": ""}, headers=auth_headers)
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"

    # ขนาดภาพไม่ตรงกับ Whitelist
    payload = {
        "prompt": "a cat",
        "width": 600,
        "height": 600,
        "steps": 20,
        "cfg_scale": 7.0,
        "seed": -1,
        "sampler": "Euler a",
    }
    res = client.post("/api/v1/generate", json=payload, headers=auth_headers)
    assert res.status_code == 400


@patch("app.routes.sd.generate_sd_image")
def test_generate_image_success(mock_sd, client, auth_headers):
    """TC-SD-002: สั่งสร้างรูปภาพสำเร็จ (Mock AI Response)"""
    # จำลอง Base64 1x1 Pixel PNG
    mock_sd.return_value = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    payload = {
        "prompt": "A beautiful landscape",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg_scale": 7.0,
        "seed": -1,
        "sampler": "Euler a",
    }

    res = client.post("/api/v1/generate", json=payload, headers=auth_headers)
    data = res.get_json()

    assert res.status_code == 201
    assert data["success"] is True
    assert "image_url" in data["data"]


@patch("app.routes.sd.generate_sd_image")
def test_generate_ai_busy(mock_sd, client, auth_headers):
    """TC-SD-003: AI Server ติดงานอื่นอยู่ (Busy)"""
    mock_sd.side_effect = AIServerBusyException("AI Server is busy")

    payload = {
        "prompt": "test",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg_scale": 7.0,
        "seed": -1,
        "sampler": "Euler a",
    }
    res = client.post("/api/v1/generate", json=payload, headers=auth_headers)
    assert res.status_code == 409
    assert res.get_json()["error"]["code"] == "AI_SERVER_BUSY"