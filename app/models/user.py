from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base
from datetime import datetime
from sqlalchemy.types import Boolean, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from enum import Enum

class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole, name="userrole"), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)