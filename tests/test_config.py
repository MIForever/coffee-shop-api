"""
Test configuration loading in test environment.
"""
import os
import pytest
from app.core.config import settings


def test_settings_load_in_test_environment():
    """Test that settings load properly in test environment."""
    assert settings.ENVIRONMENT == "test"
    assert settings.SECRET_KEY == "test-secret-key-for-testing-only"
    assert settings.JWT_SECRET_KEY == "test-jwt-secret-key-for-testing-only"
    assert settings.JWT_REFRESH_SECRET_KEY == "test-jwt-refresh-secret-key-for-testing-only"
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_PASSWORD == "postgres"
    assert settings.POSTGRES_DB == "test_coffee_shop"


def test_database_url_assembly():
    """Test that database URL is assembled correctly."""
    expected_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_coffee_shop"
    assert settings.DATABASE_URL == expected_url


def test_celery_url_assembly():
    """Test that Celery URLs are assembled correctly."""
    expected_url = "redis://redis:6379/0"
    assert settings.CELERY_BROKER_URL == expected_url
    assert settings.CELERY_BACKEND_URL == expected_url
