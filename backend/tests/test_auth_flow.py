"""
Tests for Authentication API Routes: Registration, Login, Profile & Password Update
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_auth_full_lifecycle():
    unique_email = f"analyst_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "securepassword123"

    # 1. Register
    payload = {
        "email": unique_email,
        "password": pwd,
        "full_name": "Test Analyst"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == unique_email
    assert data["user"]["full_name"] == "Test Analyst"

    # 2. Duplicate registration rejected
    dup_res = client.post("/api/v1/auth/register", json=payload)
    assert dup_res.status_code == 409

    # 3. Login success
    login_res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": pwd})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token

    # 4. Login with incorrect password
    bad_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "wrongpassword"})
    assert bad_login.status_code == 401

    # 5. Get current user profile
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email
    assert "total_verifications" in me_data
    assert "verdict_stats" in me_data

    # 6. Update user profile name
    update_res = client.put("/api/v1/auth/me", json={"full_name": "Updated Senior Analyst"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Updated Senior Analyst"

    # 7. Update password
    pwd_update_res = client.put("/api/v1/auth/me", json={"current_password": pwd, "new_password": "newsecurepassword456"}, headers=headers)
    assert pwd_update_res.status_code == 200

    # 8. Re-login with new password
    new_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "newsecurepassword456"})
    assert new_login.status_code == 200
