from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.deps import get_db
from app.models import User, VerificationToken, RefreshToken
from app.schemas.user import UserCreate
from app.schemas.auth import LoginInput, RefreshTokenInput, VerifyInput, Token
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.email import send_email
from app.core.config import settings

# Fixed router - removed invalid parameters
router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/signup", summary="Register a new user", status_code=201)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and send email verification if enabled."""
    existing_user = (
        await db.execute(select(User).where(User.email == user_in.email))
    ).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=user_in.role,
        is_verified=False,
    )
    db.add(new_user)
    await db.flush()

    token = str(uuid4())
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    v_token = VerificationToken(
        user_id=new_user.id,
        token=token,
        expires_at=expires,
        token_type="email_verification"
    )
    db.add(v_token)
    await db.commit()

    if settings.EMAIL_VERIFICATION_ENABLED:
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        await send_email(
            to_email=new_user.email,
            subject="Verify your email",
            template_name="email_verification.html",
            context={"verification_url": verification_url}
        )

    return {"message": "User registered successfully. Please check your email to verify your account."}


@router.post("/login", response_model=Token, summary="Authenticate user")
async def login(credentials: LoginInput, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access and refresh tokens."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(data: RefreshTokenInput, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    try:
        payload = verify_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid refresh token") from e

    token = (await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == data.refresh_token)
        .where(RefreshToken.revoked == False)
        .where(RefreshToken.expires_at > datetime.now(timezone.utc))
    )).scalars().first()
    
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired refresh token")

    access_token = create_access_token({"sub": str(token.user_id)})
    
    return {
        "access_token": access_token,
        "refresh_token": data.refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify", summary="Verify email address")
async def verify_email(data: VerifyInput, db: AsyncSession = Depends(get_db)):
    """Verify user's email address using verification token."""
    token = (await db.execute(
        select(VerificationToken)
        .where(VerificationToken.token == data.token)
        .where(VerificationToken.token_type == "email_verification")
        .where(VerificationToken.revoked == False)
        .where(VerificationToken.expires_at > datetime.now(timezone.utc))
    )).scalars().first()
    
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = await db.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_verified = True
    token.revoked = True
    token.revoked_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {"message": "Email verified successfully"}