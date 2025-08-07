import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.db.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", summary="Basic health check")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/db", summary="Database health check")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/cache", summary="Redis cache health check")
async def cache_health_check() -> Dict[str, Any]:
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        await redis_client.ping()
        
        test_key = "health_check_test"
        await redis_client.set(test_key, "test_value", ex=10)
        value = await redis_client.get(test_key)
        await redis_client.delete(test_key)
        
        if value != "test_value":
            raise Exception("Redis read/write test failed")
        
        await redis_client.close()
        
        return {
            "status": "healthy",
            "cache": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cache connection failed: {str(e)}"
        )


@router.get("/full", summary="Comprehensive health check")
async def full_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["cache"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    try:
        if settings.EMAIL_VERIFICATION_ENABLED:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                health_status["checks"]["email"] = {"status": "configured"}
            else:
                health_status["checks"]["email"] = {"status": "mock_mode"}
        else:
            health_status["checks"]["email"] = {"status": "disabled"}
    except Exception as e:
        health_status["checks"]["email"] = {"status": "error", "error": str(e)}
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status
