"""
Tests for authentication endpoints.
"""
from datetime import datetime, timedelta

import pytest
from fastapi import status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User, UserRole
from app.schemas.token import TokenData, TokenType
from app.schemas.user import UserCreate
from app.services.auth import AuthService

# Test data
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123!"  # Meets password policy
TEST_FIRST_NAME = "Test"
TEST_LAST_NAME = "User"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminPassword123!"

@pytest.mark.asyncio
async def test_register_user(client, db_session: AsyncSession):
    """Test user registration."""
    # Test successful registration
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": TEST_FIRST_NAME,
            "last_name": TEST_LAST_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "message" in data
    assert "registered successfully" in data["message"]

    # Test duplicate email registration
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": TEST_EMAIL,
            "password": "AnotherPassword123!",
            "first_name": "Duplicate",
            "last_name": "User",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()
    
    # Test password policy validation
    weak_password = "weak"
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "new@example.com",
            "password": weak_password,
            "first_name": "Weak",
            "last_name": "User",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "password" in response.text.lower()

@pytest.mark.asyncio
async def test_login_user(client, db_session: AsyncSession):
    """Test user login and token generation."""
    # First register a user
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        UserCreate(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name=TEST_FIRST_NAME,
            last_name=TEST_LAST_NAME,
        )
    )
    
    # Mark user as verified
    user.is_verified = True
    await db_session.commit()
    await db_session.refresh(user)

    # Test successful login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
    # Verify tokens are valid
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # Test access token
    payload = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == str(user.id)
    assert payload["type"] == TokenType.ACCESS
    
    # Test refresh token
    refresh_payload = jwt.decode(
        refresh_token,
        settings.JWT_REFRESH_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert refresh_payload["sub"] == str(user.id)
    assert refresh_payload["type"] == TokenType.REFRESH

    # Test login with unverified email
    unverified_user = await auth_service.register_user(
        UserCreate(
            email="unverified@example.com",
            password=TEST_PASSWORD,
            first_name="Unverified",
            last_name="User",
        )
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unverified@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email not verified" in response.json()["detail"].lower()

    # Test invalid password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect email or password" in response.json()["detail"].lower()

    # Test non-existent user
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect email or password" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_read_users_me(client, db_session: AsyncSession):
    """Test retrieving current user information."""
    # Register and login a user
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        UserCreate(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            first_name=TEST_FIRST_NAME,
            last_name=TEST_LAST_NAME,
        )
    )
    
    # Mark user as verified
    user.is_verified = True
    await db_session.commit()
    
    # Get access token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    access_token = login_response.json()["access_token"]
    
    # Test successful retrieval with valid token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["email"] == TEST_EMAIL
    assert data["first_name"] == TEST_FIRST_NAME
    assert data["last_name"] == TEST_LAST_NAME
    assert "hashed_password" not in data
    assert "password" not in data
    
    # Test with expired token
    expired_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(seconds=-1)  # Expired token
    )
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "token" in response.json()["detail"].lower()
    
    # Test with invalid token
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test without token
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
