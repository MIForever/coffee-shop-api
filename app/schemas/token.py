from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TokenType(str, Enum):
    """Enum for token types."""
    ACCESS = "access"
    REFRESH = "refresh"

class TokenData(BaseModel):
    """Token payload data."""
    sub: str = Field(..., description="Subject (user ID)")
    scopes: List[str] = Field(default_factory=list, description="List of scopes")
    type: TokenType = Field(..., description="Token type (access or refresh)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    iss: str = Field(..., description="Issuer")
    jti: Optional[str] = Field(None, description="JWT ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sub": "user123",
                "scopes": ["user:read"],
                "type": "access",
                "exp": 1640995200,
                "iat": 1640991600,
                "iss": "Coffee Shop API",
                "jti": "abc123"
            }
        }

class Token(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Time in seconds until the token expires")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }

class TokenRefresh(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
