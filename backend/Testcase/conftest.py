import os
import pytest
from app import create_app
from app.routes.auth import MOCK_USERS_DB
from app.routes.sd import MOCK_GENERATIONS_DB


@pytest.fixture
def app():
    """สร้าง App Instance สำหรับ Testing Environment"""
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345"
    app = create_app()
    app.config.update({"TESTING": True})

    # Clear mock databases before test
    MOCK_USERS_DB.clear()
    MOCK_GENERATIONS_DB.clear()

    yield app

    # Clean up after test
    MOCK_USERS_DB.clear()
    MOCK_GENERATIONS_DB.clear()


@pytest.fixture
def client(app):
    """สร้าง Test Client สำหรับยิง Request เสมือน"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Helper Fixture สำหรับสมัครสมาชิก Login แล้วดึง Token มาใส่ Header"""
    client.post(
        "/api/v1/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = response.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}