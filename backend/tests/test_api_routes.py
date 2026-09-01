"""
Tests for API Routes & Input Validation
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /api/v1/health returns 200 with structured status"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "running"
    assert "dependencies" in data
    assert "groq_llm" in data["dependencies"]
    assert "news_api" in data["dependencies"]
    assert "qdrant_vector_db" in data["dependencies"]


def test_verify_validation_both_url_and_text():
    """Verify that providing both URL and text fails with 422 Unprocessable Entity"""
    payload = {
        "url": "https://reuters.com/article",
        "text": "Some text claim"
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 422


def test_verify_validation_neither_url_nor_text():
    """Verify that providing neither URL nor text fails with 422"""
    payload = {
        "url": "",
        "text": ""
    }
    response = client.post("/api/v1/verify", json=payload)
    assert response.status_code == 422


def test_verify_empty_body():
    """Verify that sending empty JSON body fails with 422"""
    response = client.post("/api/v1/verify", json={})
    assert response.status_code == 422
