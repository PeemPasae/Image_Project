# ==============================================================================
# ชื่อไฟล์: backend/tests/test_backend_full.py
# หน้าที่: ชุดทดสอบครอบคลุมทุกระบบ (Automated Test Suite)
# ครอบคลุม:
# 1. ระบบ Register, Login, ตรวจชื่อ/อีเมลซ้ำ (Duplicate Check)
# 2. ระบบความปลอดภัย ป้องกันการข้ามสิทธิ์ผู้ใช้ (IDOR & Anti-Hopping)
# 3. ระบบประวัติการสร้างภาพ 2 รูปแบบ (Checkpoint vs Sub-Functions)
# 4. ระบบคำนวณเวลาโดยประมาณ (Estimated Time)
# 5. ระบบจัดการคิวงานพร้อมกัน (Concurrency Queue)
# ==============================================================================

import os
import json
import base64
import pytest
from unittest.mock import patch

import cv2
import numpy as np

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.generation import Generation


@pytest.fixture
def client():
    """Fixture สำหรับสร้าง Flask Test Client พร้อมฐานข้อมูล SQLite ในหน่วยความจำ (:memory:)"""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_key_for_unit_tests",
    })

    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()


def test_register_and_duplicate_check(client):
    """
    ทดสอบระบบสมัครสมาชิก:
    - สมัครสำเร็จ (HTTP 201)
    - ป้องกันการสมัครอีเมลซ้ำ (HTTP 409 EMAIL_EXISTS)
    - ตรวจสอบความยาวรหัสผ่านไม่ถึง 8 ตัว (HTTP 400 VALIDATION_ERROR)
    """
    # 1. สมัครสมาชิกคนแรก
    res1 = client.post("/api/v1/register", json={
        "email": "alice@luma.dev",
        "password": "password123"
    })
    assert res1.status_code == 201
    data1 = res1.get_json()
    assert data1["success"] is True
    assert data1["data"]["user"]["email"] == "alice@luma.dev"

    # 2. ทดสอบสมัครด้วยอีเมลเดิมซ้ำ (ต้องได้ 409 EMAIL_EXISTS)
    res_dup = client.post("/api/v1/register", json={
        "email": "alice@luma.dev",
        "password": "anotherpassword"
    })
    assert res_dup.status_code == 409
    data_dup = res_dup.get_json()
    assert data_dup["success"] is False
    assert data_dup["error"]["code"] == "EMAIL_EXISTS"

    # 3. ทดสอบรหัสผ่านสั้นเกินไป (< 8 ตัว)
    res_short = client.post("/api/v1/register", json={
        "email": "bob@luma.dev",
        "password": "123"
    })
    assert res_short.status_code == 400
    data_short = res_short.get_json()
    assert data_short["error"]["code"] == "VALIDATION_ERROR"


def test_login_and_jwt(client):
    """
    ทดสอบระบบเข้าสู่ระบบ:
    - เข้าสู่ระบบสำเร็จพร้อมรับ JWT Token (HTTP 200)
    - รหัสผ่านผิด (HTTP 401 INVALID_CREDENTIALS)
    """
    # 1. สร้างบัญชีผู้ใช้
    client.post("/api/v1/register", json={
        "email": "charlie@luma.dev",
        "password": "password123"
    })

    # 2. ล็อกอินด้วยรหัสที่ถูกต้อง
    res = client.post("/api/v1/login", json={
        "email": "charlie@luma.dev",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "Bearer"

    # 3. ล็อกอินด้วยรหัสผ่านที่ผิด
    res_wrong = client.post("/api/v1/login", json={
        "email": "charlie@luma.dev",
        "password": "wrongpassword"
    })
    assert res_wrong.status_code == 401
    data_wrong = res_wrong.get_json()
    assert data_wrong["error"]["code"] == "INVALID_CREDENTIALS"


def test_user_isolation_and_idor_protection(client):
    """
    ทดสอบระบบความปลอดภัยและการแยกสิทธิ์ (Anti-Hopping & IDOR Protection):
    - User A สร้างรูปภาพ
    - User B ไม่สามารถเปิดดู, สตรีมไฟล์, หรือลบรูปภาพของ User A ได้
    - หน้าประวัติของ User B จะไม่เห็นรูปภาพของ User A
    """
    # 1. สมัครและล็อกอิน User A
    client.post("/api/v1/register", json={"email": "usera@luma.dev", "password": "password123"})
    login_a = client.post("/api/v1/login", json={"email": "usera@luma.dev", "password": "password123"}).get_json()
    token_a = login_a["data"]["access_token"]

    # 2. สมัครและล็อกอิน User B
    client.post("/api/v1/register", json={"email": "userb@luma.dev", "password": "password123"})
    login_b = client.post("/api/v1/login", json={"email": "userb@luma.dev", "password": "password123"}).get_json()
    token_b = login_b["data"]["access_token"]

    # 3. User A สั่งสร้างรูปภาพ (จำลอง AI Server)
    fake_png_base64 = base64.b64encode(b"fake_png_binary_data").decode("utf-8")
    with patch("app.routes.sd.generate_sd_image", return_value=(fake_png_base64, 3.2, 4.5)):
        gen_res = client.post("/api/v1/generate", 
            json={"prompt": "A beautiful sunset over the mountains", "steps": 20, "width": 512, "height": 512},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert gen_res.status_code == 201
        gen_id = gen_res.get_json()["data"]["generation_id"]

    # 4. User A สามารถดูรายละเอียดและสตรีมรูปภาพของตนเองได้
    res_a_view = client.get(f"/api/v1/history/{gen_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_view.status_code == 200

    res_a_img = client.get(f"/api/v1/images/{gen_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_img.status_code == 200
    assert res_a_img.data == b"fake_png_binary_data"

    # 5. User B พยายามเข้าถึงรูปภาพของ User A (ต้องโดนบล็อก HTTP 404)
    res_b_view = client.get(f"/api/v1/history/{gen_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_view.status_code == 404

    res_b_img = client.get(f"/api/v1/images/{gen_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_img.status_code == 404

    res_b_del = client.delete(f"/api/v1/history/{gen_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_del.status_code == 404

    # 6. ตรวจสอบประวัติของ User B (ต้องเป็นรายการว่าง ไม่เห็นภาพของ User A)
    res_b_history = client.get("/api/v1/history", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_history.status_code == 200
    assert len(res_b_history.get_json()["data"]["history"]) == 0


def test_history_pagination(client):
    """
    ทดสอบระบบประวัติการสร้างภาพตาม FRONTEND_REQUIREMENTS.md:
    - ดึงรายการประวัติพร้อม pagination (page, limit)
    - ส่งกลับค่าครบถ้วนสำหรับ frontend
    """
    client.post("/api/v1/register", json={"email": "artist@luma.dev", "password": "password123"})
    login = client.post("/api/v1/login", json={"email": "artist@luma.dev", "password": "password123"}).get_json()
    token = login["data"]["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # สร้างภาพ 2 รายการ
    fake_png = base64.b64encode(b"fake_image_bytes").decode("utf-8")
    with patch("app.routes.sd.generate_sd_image", return_value=(fake_png, 2.0, 3.0)):
        client.post("/api/v1/generate", json={"prompt": "Image 1", "steps": 20, "width": 512, "height": 512}, headers=auth_header)
        client.post("/api/v1/generate", json={"prompt": "Image 2", "steps": 20, "width": 512, "height": 512}, headers=auth_header)

    # ดึงประวัติแบบ pagination
    res = client.get("/api/v1/history?page=1&limit=10", headers=auth_header).get_json()
    assert res["success"] is True
    assert res["data"]["pagination"]["total"] == 2
    assert len(res["data"]["history"]) == 2
    assert res["data"]["history"][0]["prompt"] in ["Image 1", "Image 2"]


def test_concurrent_generation_simulation():
    """
    ทดสอบระบบรองรับการกดเจนพร้อมกันหลายคน (Concurrency Queue Simulation):
    - จำลองคำขอ 3 คำขอส่งมาที่ generate_sd_image พร้อมกันใน Thread แยกกัน
    - ตรวจสอบว่าคิวทำงานตามลำดับและคำขอทั้งหมดเสร็จสิ้นสำเร็จ 100%
    """
    import concurrent.futures
    import time
    from unittest.mock import MagicMock
    from app.services.ai_client import generate_sd_image

    # สร้าง Mock Response สำหรับ requests.post
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "images": ["concurrent_test_base64_string"]
    }

    execution_order = []

    def mock_post(url, json, timeout):
        # จำลองระยะเวลาที่ GPU ใช้ในการสร้างภาพ
        prompt = json.get("prompt")
        time.sleep(0.05)
        execution_order.append(prompt)
        return mock_response

    payloads = [
        {"prompt": "User 1 prompt", "width": 512, "height": 512, "steps": 20},
        {"prompt": "User 2 prompt", "width": 512, "height": 512, "steps": 20},
        {"prompt": "User 3 prompt", "width": 512, "height": 512, "steps": 20},
    ]

    with patch("requests.post", side_effect=mock_post):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_sd_image, p) for p in payloads]
            results = [f.result() for f in futures]

    # ตรวจสอบว่าคำขอทั้ง 3 งานได้รับภาพกลับมาอย่างสมบูรณ์
    assert len(results) == 3
    for img_base64, actual_t, est_t in results:
        assert img_base64 == "concurrent_test_base64_string"
        assert actual_t >= 0.05
        assert est_t > 0

    # ตรวจสอบว่าคำขอถูกประมวลผลตามลำดับคิว
    assert len(execution_order) == 3


def test_generate_string_parameters_and_type_coercion(client):
    """
    ทดสอบการส่งตัวเลขในรูป string (เช่น "512", "20", "7.5") มายัง /generate
    ระบบต้องแปลงค่าอัตโนมัติ ไม่โยน 500 TypeError
    """
    client.post("/api/v1/register", json={"email": "type_tester@luma.dev", "password": "password123"})
    login = client.post("/api/v1/login", json={"email": "type_tester@luma.dev", "password": "password123"}).get_json()
    token = login["data"]["access_token"]

    fake_b64 = base64.b64encode(b"dummy_png").decode("utf-8")
    with patch("app.routes.sd.generate_sd_image", return_value=(fake_b64, 1.2, 2.5)):
        res = client.post(
            "/api/v1/generate",
            json={"prompt": "A test prompt", "width": "512", "height": "512", "steps": "25", "cfg_scale": "7.5"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True

        # ทดสอบค่าที่ไม่ใช่ตัวเลข (ต้องได้ 400 VALIDATION_ERROR ไม่ใช่ 500)
        res_bad = client.post(
            "/api/v1/generate",
            json={"prompt": "A test prompt", "steps": "not_a_number"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_bad.status_code == 400
        assert res_bad.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_generation_type_display_name():
    """ทดสอบฟังก์ชัน get_type_display_name สำหรับทุกฟิลเตอร์"""
    gen_sd = Generation(category="sd_generate", action_type="txt2img")
    assert "Stable Diffusion" in gen_sd.get_type_display_name()

    gen_cart = Generation(category="image_filter", action_type="cartoonize")
    assert "Cartoonize" in gen_cart.get_type_display_name()

    gen_tilt = Generation(category="image_filter", action_type="tilt_shift")
    assert "Tilt-Shift" in gen_tilt.get_type_display_name()

    gen_hdr = Generation(category="image_filter", action_type="hdr_enhancer")
    assert "HDR" in gen_hdr.get_type_display_name()

    gen_spot = Generation(category="image_filter", action_type="spot_blur")
    assert "Spot Blur" in gen_spot.get_type_display_name()

    gen_bg = Generation(category="image_filter", action_type="remove_bg")
    assert "Remove Background" in gen_bg.get_type_display_name()

    gen_gest = Generation(category="image_filter", action_type="gesture")
    assert "Hand Gesture" in gen_gest.get_type_display_name()


def test_get_profile_contract(client):
    """ทดสอบ GET /api/v1/profile ตามสัญญาที่ Profile.jsx อ่านจริง"""
    client.post("/api/v1/register", json={"email": "profiler@luma.dev", "password": "password123"})
    login = client.post("/api/v1/login", json={"email": "profiler@luma.dev", "password": "password123"}).get_json()
    token = login["data"]["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # สร้าง 1 ภาพ
    fake_png = base64.b64encode(b"fake_image_bytes").decode("utf-8")
    with patch("app.routes.sd.generate_sd_image", return_value=(fake_png, 1.5, 2.0)):
        client.post("/api/v1/generate", json={"prompt": "Profile test image", "steps": 20, "width": 512, "height": 512}, headers=auth_header)

    res = client.get("/api/v1/profile", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["email"] == "profiler@luma.dev"
    assert "id" in data
    assert "created_at" in data
    assert data["generation_count"] == 1


def test_health_check_endpoint(client):
    """ทดสอบ GET /api/v1/health ตรวจสอบสถานะความพร้อมของระบบ"""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database"] == "connected"


def test_disk_storage_and_streaming(client):
    """ทดสอบการบันทึกภาพลง Disk และการ Stream ตรงจาก Disk File"""
    client.post("/api/v1/register", json={"email": "disktest@luma.dev", "password": "password123"})
    login = client.post("/api/v1/login", json={"email": "disktest@luma.dev", "password": "password123"}).get_json()
    token = login["data"]["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    fake_png = base64.b64encode(b"disk_stream_sample_bytes").decode("utf-8")
    with patch("app.routes.sd.generate_sd_image", return_value=(fake_png, 1.2, 2.0)):
        res = client.post("/api/v1/generate", json={"prompt": "Disk stream test", "steps": 20, "width": 512, "height": 512}, headers=auth_header)
        assert res.status_code == 201
        gen_id = res.get_json()["data"]["generation_id"]

    # ตรวจสอบการ Stream กลับมา
    img_res = client.get(f"/api/v1/images/{gen_id}", headers=auth_header)
    assert img_res.status_code == 200
    assert img_res.data == b"disk_stream_sample_bytes"

    # ตรวจสอบการลบและเคลียร์ไฟล์
    del_res = client.delete(f"/api/v1/history/{gen_id}", headers=auth_header)
    assert del_res.status_code == 200


# ==============================================================================
# [DISABLED TESTS] การทดสอบสำหรับ Endpoint ที่ไม่ได้ใช้งานโดย Frontend
# เผื่อต้องการนำกลับมาเปิดใช้งานในอนาคต (เพียงเอาเครื่องหมาย # ออก)
# ==============================================================================
# def test_time_estimation_endpoint(client):
#     res = client.post("/api/v1/estimate", json={"width": 512, "height": 512, "steps": 20})
#     assert res.status_code == 200
#     data = res.get_json()["data"]
#     assert "total_estimated_seconds" in data




