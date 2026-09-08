from unittest.mock import patch


def test_get_history_unauthorized(client):
    """TC-SEC-001: เข้าถึง history โดยไม่มี Token"""
    res = client.get("/api/v1/history")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "UNAUTHORIZED"


@patch("app.routes.sd.generate_sd_image")
def test_history_idor_protection(mock_sd, client, auth_headers):
    """TC-SEC-003: ป้องกัน IDOR - User A ไม่สามารถดู/ลบ รูปของ User B ได้"""
    mock_sd.return_value = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    # User A สร้างรูปภาพ
    gen_res = client.post(
        "/api/v1/generate",
        json={
            "prompt": "User A photo",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7,
            "seed": -1,
            "sampler": "Euler a",
        },
        headers=auth_headers,
    )
    gen_id = gen_res.get_json()["data"]["id"]

    # สมัคร User B
    client.post(
        "/api/v1/register",
        json={"email": "userB@example.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/login",
        json={"email": "userB@example.com", "password": "password123"},
    )
    token_b = login_b.get_json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B พยายามเข้าถึงรูปของ User A
    res_get = client.get(f"/api/v1/history/{gen_id}", headers=headers_b)
    assert res_get.status_code == 404

    # User B พยายามลบรูปของ User A
    res_del = client.delete(f"/api/v1/history/{gen_id}", headers=headers_b)
    assert res_del.status_code == 404
    