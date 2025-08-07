"""
Basic configuration tests that don't require database connections.
"""
import pytest
from app.core.config import settings


def test_basic_settings():
    """Test that basic settings are loaded correctly."""
    assert settings.PROJECT_NAME == "Coffee Shop API"
    assert settings.API_VERSION == "1.0.0"
    assert settings.API_PREFIX == "/api/v1"


def test_security_settings():
    """Test that security settings are loaded correctly."""
    assert settings.SECRET_KEY == "test-secret-key-for-testing-only"
    assert settings.JWT_SECRET_KEY == "test-jwt-secret-key-for-testing-only"
    assert settings.JWT_REFRESH_SECRET_KEY == "test-jwt-refresh-secret-key-for-testing-only"
    assert settings.JWT_ALGORITHM == "HS256"


def test_database_settings():
    """Test that database settings are loaded correctly."""
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_PASSWORD == "postgres"
    assert settings.POSTGRES_DB == "test_coffee_shop"  # Overridden in conftest.py
    assert settings.POSTGRES_HOST == "localhost"  # Overridden in conftest.py
    assert settings.POSTGRES_PORT == "5432"


def test_environment_settings():
    """Test that environment settings are loaded correctly."""
    assert settings.ENVIRONMENT == "test"  # Overridden in conftest.py
