"""
Tests for Celery tasks.
"""
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.verification_token import VerificationToken
from app.schemas.user import UserCreate, UserRole
from app.services.auth import AuthService
from app.tasks.cleanup import delete_unverified_users, cleanup_expired_tokens

# Test data
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_FULL_NAME = "Test User"

@pytest.mark.asyncio
async def test_delete_unverified_users(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    
    # Create verified user (should not be deleted)
    verified_user = await auth_service.register_user(
        UserCreate(
            email="verified@example.com",
            password=TEST_PASSWORD,
            full_name="Verified User",
        )
    )
    verified_user.is_verified = True
    verified_user.created_at = datetime.now(timezone.utc) - timedelta(days=3)
    
    # Create unverified user older than threshold (should be deleted)
    old_unverified_user = await auth_service.register_user(
        UserCreate(
            email="old_unverified@example.com",
            password=TEST_PASSWORD,
            full_name="Old Unverified User",
        )
    )
    old_unverified_user.created_at = datetime.now(timezone.utc) - timedelta(days=3)
    
    # Create unverified user within threshold (should not be deleted)
    new_unverified_user = await auth_service.register_user(
        UserCreate(
            email="new_unverified@example.com",
            password=TEST_PASSWORD,
            full_name="New Unverified User",
        )
    )
    new_unverified_user.created_at = datetime.now(timezone.utc) - timedelta(hours=23)
    
    await db_session.commit()
    
    # Run the cleanup task
    result = await delete_unverified_users(days_old=2)
    
    # Verify the task completed successfully
    assert result["status"] == "success"
    assert result["deleted_count"] == 1
    
    # Verify the correct user was deleted
    deleted_user = await db_session.get(User, old_unverified_user.id)
    assert deleted_user is None
    
    # Verify other users still exist
    assert await db_session.get(User, verified_user.id) is not None
    assert await db_session.get(User, new_unverified_user.id) is not None

@pytest.mark.asyncio
async def test_delete_unverified_users_empty(db_session: AsyncSession):
    result = await delete_unverified_users()
    assert result["status"] == "success"
    assert result["deleted_count"] == 0

@pytest.mark.asyncio
async def test_cleanup_expired_tokens(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    
    # Create test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create expired tokens
    expired_refresh_token = RefreshToken(
        user_id=user.id,
        token="expired_refresh_token",
        expires_at=now - timedelta(days=1),
        created_at=now - timedelta(days=2)
    )
    
    expired_verification_token = VerificationToken(
        user_id=user.id,
        token="expired_verification_token",
        expires_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=2)
    )
    
    # Create non-expired tokens
    valid_refresh_token = RefreshToken(
        user_id=user.id,
        token="valid_refresh_token",
        expires_at=now + timedelta(days=1),
        created_at=now
    )
    
    db_session.add_all([expired_refresh_token, expired_verification_token, valid_refresh_token])
    await db_session.commit()
    
    # Run the cleanup task
    result = await cleanup_expired_tokens()
    
    # Verify the task completed successfully
    assert result["status"] == "success"
    assert result["deleted_refresh_tokens"] == 1
    assert result["deleted_verification_tokens"] == 1
    
    # Verify only expired tokens were deleted
    assert await db_session.get(RefreshToken, expired_refresh_token.id) is None
    assert await db_session.get(VerificationToken, expired_verification_token.id) is None
    assert await db_session.get(RefreshToken, valid_refresh_token.id) is not None

@pytest.mark.asyncio
@patch("app.tasks.cleanup.get_db")
async def test_cleanup_error_handling(mock_get_db, db_session: AsyncSession):
    mock_session = MagicMock()
    mock_session.begin.side_effect = Exception("Database error")
    mock_get_db.return_value = mock_session
    
    # Test delete_unverified_users error handling
    result = await delete_unverified_users()
    assert result["status"] == "error"
    
    # Test cleanup_expired_tokens error handling
    result = await cleanup_expired_tokens()
    assert result["status"] == "error"
