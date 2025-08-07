"""
Health check schemas.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field

class HealthStatus(str, Enum):
    """Health status values."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEGRADED = "degraded"

class ServiceHealth(BaseModel):
    """Health status of a service."""
    service: str = Field(..., description="Name of the service")
    status: HealthStatus = Field(..., description="Health status")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional details about the service health"
    )

    class Config:
        schema_extra = {
            "example": {
                "service": "database",
                "status": "ok",
                "details": {"database": "postgresql", "status": "connected"}
            }
        }

class HealthCheck(BaseModel):
    """Basic health check response."""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Current server time")
    service: str = Field(..., description="Name of the service")
    version: str = Field(..., description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2023-01-01T12:00:00Z",
                "service": "coffee-shop-api",
                "version": "1.0.0"
            }
        }
