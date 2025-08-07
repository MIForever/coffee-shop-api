"""
Test that the FastAPI application can start without configuration errors.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_startup():
    """Test that the application starts without configuration errors."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_app_has_correct_title():
    """Test that the application has the correct title."""
    assert app.title == "Coffee Shop API"
    assert app.version == "1.0.0"
