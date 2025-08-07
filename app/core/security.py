import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.schemas.token import TokenData, TokenType

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt", "argon2", "django_argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    argon2__hash_len=32,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login",
    scopes={
        "user:read": "Read access to user data",
        "user:write": "Write access to user data",
        "admin": "Admin access",
    },
)

limiter = Limiter(key_func=get_remote_address)

def validate_password_strength(password: str) -> bool:
    if len(password) < 12:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r'[!@#$%^&*(),.\":{}|<>]', password):
        return False
    return True

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(
    data: Dict[str, Any],
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    
    if expires_delta:
        expire = now + expires_delta
    else:
        if token_type == TokenType.ACCESS:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "type": token_type,
            "iss": settings.JWT_ISSUER,
        }
    )
    
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

def create_access_token(data: Dict[str, Any]) -> str:
    return create_token(
        data,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(data: Dict[str, Any]) -> str:
    return create_token(
        data,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

def get_current_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        token_type = payload.get("type")
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = TokenData(scopes=token_scopes, user_id=user_id)
        
    except (JWTError, ValidationError) as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception
    
    if security_scopes.scopes:
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )
    
    return {"user_id": token_data.user_id, "scopes": token_data.scopes}

def get_cors_middleware():
    return CORSMiddleware(
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def get_rate_limit_key(request: Request) -> str:
    if request.client:
        return request.client.host
    return "global"

async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
