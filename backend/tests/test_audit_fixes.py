# ==============================================================================
# ชื่อไฟล์: backend/tests/test_audit_fixes.py
# หน้าที่: เทสต์สำหรับบัคที่เจอตอนตรวจระบบ (1 เทสต์ = 1 บัค) กันไม่ให้บัคกลับมาอีก
# รัน: cd backend && pytest tests
# ==============================================================================

import io
import base64
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from app import create_app
from app.extensions import db
from app.models.user import User

PASSWORD = "password123"
FAKE_PNG = base64.b64encode(cv2.imencode(".png", np.zeros((8, 8, 3), np.uint8))[1].tobytes()).decode()


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_for_audit_fixes",
    })
    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()


def register_and_login(client, email):
    client.post("/api/v1/register", json={"email": email, "password": PASSWORD})
    res = client.post("/api/v1/login", json={"email": email, "password": PASSWORD}).get_json()
    return {"Authorization": f"Bearer {res['data']['access_token']}"}


def png_upload(width, height):
    ok, buf = cv2.imencode(".png", np.zeros((height, width, 3), np.uint8))
    return (io.BytesIO(buf.tobytes()), "test.png")


# ---------------------------------------------------------------- บัค #2
def test_backend_refuses_to_start_without_jwt_secret():
    """ไม่มีรหัสลับ JWT -> ต้องไม่ยอมเปิด backend (เดิมใช้รหัสสำรองที่อยู่บน GitHub)"""
    with pytest.raises(RuntimeError):
        create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": ""})


# ---------------------------------------------------------------- บัค #1 และ #13
def test_token_of_deleted_user_is_rejected_even_if_id_is_reused(client):
    """ลบผู้ใช้แล้ว token เก่าต้องใช้ไม่ได้ แม้มีคนสมัครใหม่ได้ ID เดิม"""
    old_headers = register_and_login(client, "old@luma.dev")
    old_user = User.query.filter_by(email="old@luma.dev").first()
    old_id = old_user.id
    db.session.delete(old_user)
    db.session.commit()

    # token ของคนที่ถูกลบใช้ไม่ได้ทันที
    assert client.get("/api/v1/profile", headers=old_headers).status_code == 401

    # คนใหม่สมัครแล้วได้ ID เดิม -> token เก่าก็ยังต้องเข้าบัญชีคนใหม่ไม่ได้
    client.post("/api/v1/register", json={"email": "new@luma.dev", "password": PASSWORD})
    assert User.query.filter_by(email="new@luma.dev").first().id == old_id
    assert client.get("/api/v1/profile", headers=old_headers).status_code == 401


# ---------------------------------------------------------------- บัค #9
def test_email_is_case_insensitive(client):
    client.post("/api/v1/register", json={"email": "Peem@Luma.dev", "password": PASSWORD})
    dup = client.post("/api/v1/register", json={"email": "peem@luma.dev", "password": PASSWORD})
    assert dup.status_code == 409
    login = client.post("/api/v1/login", json={"email": "PEEM@LUMA.DEV", "password": PASSWORD})
    assert login.status_code == 200


# ---------------------------------------------------------------- บัค #7, #11, #12
def test_generate_saves_real_seed_and_only_known_params(client):
    headers = register_and_login(client, "seed@luma.dev")
    with patch("app.routes.sd.generate_sd_image", return_value=(FAKE_PNG, 1.0, 2.0)) as fake_ai:
        res = client.post("/api/v1/generate", headers=headers,
                          json={"prompt": "cat", "seed": -1, "junk": "x" * 1000})
        assert res.status_code == 201
        seed_sent_to_ai = fake_ai.call_args[0][0]["seed"]

    data = res.get_json()["data"]
    assert data["seed"] != -1                      # ได้เลขจริง ไม่ใช่ -1
    assert data["seed"] == seed_sent_to_ai          # เลขเดียวกับที่ส่งให้ AI
    detail = client.get(f"/api/v1/history/{data['generation_id']}", headers=headers).get_json()["data"]
    assert "junk" not in detail["params"]           # ไม่เก็บข้อมูลขยะ


def test_seed_out_of_range_is_rejected_before_calling_ai(client):
    headers = register_and_login(client, "seed2@luma.dev")
    with patch("app.routes.sd.generate_sd_image") as fake_ai:
        res = client.post("/api/v1/generate", headers=headers, json={"prompt": "cat", "seed": 2 ** 70})
        assert res.status_code == 400
        fake_ai.assert_not_called()                 # ไม่เสียเวลา GPU


# ---------------------------------------------------------------- บัค #10
def test_errors_are_json_not_html(client):
    headers = register_and_login(client, "json@luma.dev")
    not_found = client.get("/api/v1/does-not-exist", headers=headers)
    assert not_found.status_code == 404
    assert not_found.get_json()["success"] is False

    null_field = client.post("/api/v1/generate", headers=headers, json={"prompt": "cat", "negative_prompt": None, "seed": "abc"})
    assert null_field.status_code == 400
    assert null_field.get_json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------- บัค #18, #19
def test_history_limit_is_capped_and_health_hides_ai_url(client):
    headers = register_and_login(client, "limit@luma.dev")
    page = client.get("/api/v1/history?limit=100000", headers=headers).get_json()["data"]["pagination"]
    assert page["limit"] == 100
    assert "ai_server_url" not in client.get("/api/v1/health").get_json()["data"]


# ---------------------------------------------------------------- บัค #3
def test_spot_blur_rejects_huge_or_invalid_radius(client):
    headers = register_and_login(client, "blur@luma.dev")
    for circles in ("[[10, 10, 200000]]", "[[10, 10, NaN]]", "[[10, 10, Infinity]]"):
        res = client.post("/api/v1/process/spot-blur", headers=headers, content_type="multipart/form-data",
                          data={"image": png_upload(100, 100), "circles": circles, "strength": "10", "soft": "true"})
        assert res.status_code == 400, circles


# ---------------------------------------------------------------- บัค #4
def test_image_larger_than_20_megapixels_is_rejected(client):
    headers = register_and_login(client, "big@luma.dev")
    res = client.post("/api/v1/process/hdr-enhancer", headers=headers, content_type="multipart/form-data",
                      data={"image": png_upload(5000, 5000)})   # 25 ล้านพิกเซล แต่ไฟล์เล็กนิดเดียว
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_IMAGE"
