import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_creation():
    """Test that the FastAPI application is created correctly."""
    assert app.title == "Coffee Shop API"
    assert app.version == "1.0.0"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"


def test_app_has_routers():
    """Test that the application has the expected routers."""
    routes = [route.path for route in app.routes]
    # Check for some expected routes
    assert any("/api/v1/health" in route for route in routes)
    assert any("/api/v1/auth" in route for route in routes)
    assert any("/api/v1/user" in route for route in routes)


def test_app_has_cors_middleware():
    """Test that the application has CORS middleware configured."""
    middleware_types = [type(middleware.cls) for middleware in app.user_middleware]
    from fastapi.middleware.cors import CORSMiddleware
    assert any(issubclass(middleware_type, CORSMiddleware) for middleware_type in middleware_types)
