import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.email import send_email
from app.core.config import settings
from app.models import User, VerificationToken, RefreshToken
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        existing_user = (
            await self.db.execute(select(User).where(User.email == user_data.email))
        ).scalars().first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_verified=False,
        )
        
        self.db.add(new_user)
        await self.db.flush()
        
        token = str(uuid4())
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        verification_token = VerificationToken(
            user_id=new_user.id,
            token=token,
            expires_at=expires,
            token_type="email_verification"
        )
        self.db.add(verification_token)
        await self.db.commit()
        
        if settings.EMAIL_VERIFICATION_ENABLED:
            try:
                verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
                await send_email(
                    to_email=new_user.email,
                    subject="Verify your email",
                    template_name="email_verification.html",
                    context={"verification_url": verification_url}
                )
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
        
        return new_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def create_tokens(self, user: User) -> dict:
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at
        )
        self.db.add(db_refresh_token)
        await self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def verify_email(self, token: str) -> bool:
        verification_token = (
            await self.db.execute(
                select(VerificationToken)
                .where(VerificationToken.token == token)
                .where(VerificationToken.token_type == "email_verification")
                .where(VerificationToken.revoked == False)
                .where(VerificationToken.expires_at > datetime.now(timezone.utc))
            )
        ).scalars().first()
        
        if not verification_token:
            return False
        
        user = await self.db.get(User, verification_token.user_id)
        if not user:
            return False
        
        user.is_verified = True
        verification_token.revoked = True
        verification_token.revoked_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        return True
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        token_record = (
            await self.db.execute(
                select(RefreshToken)
                .where(RefreshToken.token == refresh_token)
                .where(RefreshToken.revoked == False)
                .where(RefreshToken.expires_at > datetime.now(timezone.utc))
            )
        ).scalars().first()
        
        if not token_record:
            return None
        
        return create_access_token({"sub": str(token_record.user_id)})
