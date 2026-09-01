"""
Tests for Verification History API Routes: List, Filter, Detail, and Deletion
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import SessionLocal
from backend.db.models import User, VerificationHistory

client = TestClient(app)


def test_history_flow():
    # 1. Register a dedicated test user for history with unique email
    unique_email = f"historyuser_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "email": unique_email,
        "password": "mypassword123",
        "full_name": "History Tester"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Insert dummy verification history records directly
    db = SessionLocal()
    h1 = VerificationHistory(
        user_id=user_id,
        verification_id="v_101",
        input_type="text",
        input_content="Sample claim 1",
        verdict="REAL",
        confidence=90,
        primary_claim="Sample claim 1 is real",
        summary="Summary of claim 1",
        explanation="Explanation 1",
        evidence_summary_json={"supporting": 2, "contradicting": 0, "neutral": 0, "total_sources_evaluated": 2},
        sources_json=[],
        pipeline_stages_json=[]
    )
    h2 = VerificationHistory(
        user_id=user_id,
        verification_id="v_102",
        input_type="url",
        input_content="https://fake-news.com/hoax",
        verdict="FALSE",
        confidence=85,
        primary_claim="Sample hoax claim",
        summary="Summary of hoax",
        explanation="Explanation hoax",
        evidence_summary_json={"supporting": 0, "contradicting": 3, "neutral": 0, "total_sources_evaluated": 3},
        sources_json=[],
        pipeline_stages_json=[]
    )
    db.add_all([h1, h2])
    db.commit()
    db.refresh(h1)
    db.refresh(h2)
    h1_id = h1.id
    db.close()

    # 3. List all history
    list_res = client.get("/api/v1/history", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 4. Filter history by verdict
    filter_res = client.get("/api/v1/history?verdict=REAL", headers=headers)
    assert filter_res.status_code == 200
    f_data = filter_res.json()
    assert f_data["total"] == 1
    assert f_data["items"][0]["verdict"] == "REAL"

    # 5. Get history detail
    detail_res = client.get(f"/api/v1/history/{h1_id}", headers=headers)
    assert detail_res.status_code == 200
    d_data = detail_res.json()
    assert d_data["verdict"] == "REAL"
    assert d_data["claim"]["primary_claim"] == "Sample claim 1 is real"

    # 6. Delete single item
    del_res = client.delete(f"/api/v1/history/{h1_id}", headers=headers)
    assert del_res.status_code == 204

    # 7. Confirm item count is now 1
    list_res2 = client.get("/api/v1/history", headers=headers)
    assert list_res2.json()["total"] == 1

    # 8. Clear all history
    clear_res = client.delete("/api/v1/history", headers=headers)
    assert clear_res.status_code == 200
    list_res3 = client.get("/api/v1/history", headers=headers)
    assert list_res3.json()["total"] == 0
