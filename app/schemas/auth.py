from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user ID
    exp: int

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenInput(BaseModel):
    refresh_token: str

class VerifyInput(BaseModel):
    token: str
