"""
Simple authentication tests to verify basic functionality.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_imports():
    """Test that the app can be imported without errors."""
    assert app is not None
    assert app.title == "Coffee Shop API"


def test_health_endpoint():
    """Test that the health endpoint works."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_auth_endpoints_exist():
    """Test that auth endpoints are registered."""
    client = TestClient(app)
    
    # Test signup endpoint exists
    response = client.post("/api/v1/auth/signup", json={})
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code in [422, 400]
    
    # Test login endpoint exists
    response = client.post("/api/v1/auth/login", json={})
    # Should return 422 (validation error) not 404 (not found)
    assert response.status_code in [422, 400]
