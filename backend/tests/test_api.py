import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") in ("healthy", "ok")

import uuid

def test_readiness_check():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json().get("status") == "ready"

def test_register_and_login_driver():
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"test_driver_{unique_id}@trafficguard.vn"
    test_password = "SecurePassword123!"
    test_name = f"Tài Xế Thử Nghiệm {unique_id}"

    # 1. Đăng ký tài xế mới
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": test_name,
            "role": "FLEET_DRIVER"
        }
    )
    assert reg_response.status_code == 200, f"Register failed: {reg_response.text}"
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data.get("token_type") == "bearer"
    assert reg_data.get("full_name") == test_name

    # 2. Đăng nhập với tài khoản vừa tạo
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_email,
            "password": test_password
        }
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data.get("token_type") == "bearer"

