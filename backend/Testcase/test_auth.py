def test_register_success(client):
    """TC-AUTH-001: ลงทะเบียนสำเร็จ"""
    res = client.post(
        "/api/v1/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    data = res.get_json()
    assert res.status_code == 201
    assert data["success"] is True
    assert data["data"]["email"] == "newuser@example.com"


def test_register_invalid_email(client):
    """TC-AUTH-002: อีเมลผิดฟอร์แมต"""
    res = client.post(
        "/api/v1/register",
        json={"email": "invalid-email", "password": "password123"},
    )
    data = res.get_json()
    assert res.status_code == 400
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_register_duplicate_email(client):
    """TC-AUTH-004: อีเมลซ้ำ"""
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post("/api/v1/register", json=payload)

    res = client.post("/api/v1/register", json=payload)
    data = res.get_json()
    assert res.status_code == 409
    assert data["error"]["code"] == "EMAIL_EXISTS"


def test_login_success(client):
    """TC-AUTH-005: เข้าสู่ระบบสำเร็จ"""
    client.post(
        "/api/v1/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    res = client.post(
        "/api/v1/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    data = res.get_json()
    assert res.status_code == 200
    assert "access_token" in data["data"]


def test_login_wrong_password(client):
    """TC-AUTH-006: รหัสผ่านผิด"""
    client.post(
        "/api/v1/register",
        json={"email": "login2@example.com", "password": "password123"},
    )

    res = client.post(
        "/api/v1/login",
        json={"email": "login2@example.com", "password": "wrongpass"},
    )
    data = res.get_json()
    assert res.status_code == 401
    assert data["error"]["code"] == "INVALID_CREDENTIALS"