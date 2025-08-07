from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base
from sqlalchemy.types import Boolean, DateTime
from sqlalchemy.sql import func

class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False)
    token_type = Column(String, nullable=False, default="email_verification")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False)