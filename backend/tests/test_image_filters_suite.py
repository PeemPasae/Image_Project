# ==============================================================================
# ชื่อไฟล์: backend/tests/test_image_filters_suite.py
# หน้าที่: ชุดทดสอบครอบคลุมโมดูล Image Processing (Remove BG, Spot Blur, Gesture, Cartoonize)
# ==============================================================================

import numpy as np
import pytest
import cv2
from app import create_app
from app.extensions import db
from app.models.generation import Generation
from app.services.image_filters.cartoonize import cartoonize
from app.services.image_filters.spot_blur import spot_blur


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_for_filters",
    })
    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_header(client):
    client.post("/api/v1/register", json={"email": "cv_tester@luma.dev", "password": "password123"})
    login = client.post("/api/v1/login", json={"email": "cv_tester@luma.dev", "password": "password123"}).get_json()
    token = login["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = [0, 0, 255]
    img[40:60, 40:60] = [255, 0, 0]
    return img


def test_cartoonize_algorithm(sample_image):
    """ทดสอบอัลกอริทึม Cartoonize"""
    res = cartoonize(sample_image, num_colors=6, line_thickness=2)
    assert res.shape == sample_image.shape
    assert res.dtype == np.uint8


def test_spot_blur_algorithm(sample_image):
    """ทดสอบอัลกอริทึม Spot Blur"""
    circles = [[50, 50, 20]]
    res = spot_blur(sample_image, circles, strength=10, soft=True)
    assert res.shape == sample_image.shape


def test_cartoonize_upload_endpoint(client, auth_header, sample_image):
    """ทดสอบ POST /api/v1/process/cartoonize (Upload)"""
    from io import BytesIO
    png_bytes = cv2.imencode(".png", sample_image)[1].tobytes()
    res = client.post(
        "/api/v1/process/cartoonize",
        data={
            "image": (BytesIO(png_bytes), "sample.png"),
            "num_colors": "6",
            "line_thickness": "2",
            "smoothness": "4",
        },
        content_type="multipart/form-data",
        headers=auth_header,
    )
    assert res.status_code == 200
    assert res.mimetype == "image/png"
    assert len(res.data) > 0


def test_cartoonize_generation_endpoint(client, auth_header, sample_image):
    """ทดสอบ POST /api/v1/process/cartoonize/:generation_id"""
    png_bytes = cv2.imencode(".png", sample_image)[1].tobytes()

    with client.application.app_context():
        gen0 = Generation(
            user_id=1,
            category="sd_generate",
            action_type="txt2img",
            image_data=png_bytes,
        )
        db.session.add(gen0)
        db.session.commit()
        gen0_id = gen0.id

    res = client.post(
        f"/api/v1/process/cartoonize/{gen0_id}",
        json={"num_colors": 4, "line_thickness": 2, "smoothness": 3},
        headers=auth_header,
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["category"] == "image_filter"
    assert data["data"]["action_type"] == "cartoonize"
    assert data["data"]["source_image_id"] == gen0_id
