import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.config import settings
from app.db.deps import get_db
from app.models import User, RefreshToken, VerificationToken

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name="cleanup.delete_unverified_users",
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=600,
    time_limit=660,
    acks_late=True,
)
async def delete_unverified_users(self, days_old: int = 2):
    logger.info(f"Starting cleanup of unverified users older than {days_old} days")
    
    try:
        deleted_count = 0
        batch_size = 100
        
        async with get_db() as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            while True:
                async with session.begin():
                    result = await session.execute(
                        select(User)
                        .where(
                            and_(
                                User.is_verified == False,
                                User.created_at < cutoff_time
                            )
                        )
                        .limit(batch_size)
                        .with_for_update(skip_locked=True)
                    )
                    users = result.scalars().all()
                    
                    if not users:
                        break
                        
                    for user in users:
                        await session.delete(user)
                        deleted_count += 1
                    
                    await session.commit()
                    
        logger.info(f"Successfully deleted {deleted_count} unverified users")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error deleting unverified users: {e}")
        raise self.retry(exc=e, countdown=60 * 5)

@celery_app.task(
    bind=True,
    name="cleanup.expired_tokens",
    max_retries=3,
    default_retry_delay=300,
    soft_time_limit=300,
    time_limit=360,
    acks_late=True,
)
async def cleanup_expired_tokens(self):
    logger.info("Starting cleanup of expired tokens")
    
    try:
        async with get_db() as session:
            now = datetime.now(timezone.utc)
            
            result = await session.execute(
                select(RefreshToken)
                .where(RefreshToken.expires_at < now)
            )
            refresh_tokens = result.scalars().all()
            
            result = await session.execute(
                select(VerificationToken)
                .where(VerificationToken.expires_at < now)
            )
            verification_tokens = result.scalars().all()
            
            deleted_refresh = len(refresh_tokens)
            deleted_verification = len(verification_tokens)
            
            for token in refresh_tokens + verification_tokens:
                await session.delete(token)
            
            await session.commit()
            
        logger.info(
            f"Cleaned up {deleted_refresh} expired refresh tokens "
            f"and {deleted_verification} expired verification tokens"
        )
        return {
            "status": "success",
            "deleted_refresh_tokens": deleted_refresh,
            "deleted_verification_tokens": deleted_verification,
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
        raise self.retry(exc=e, countdown=60 * 5)

def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        schedule=timedelta(hours=24).total_seconds(),
        sig=delete_unverified_users.s(),
        name="Delete unverified users",
    )
    
    sender.add_periodic_task(
        schedule=timedelta(hours=1).total_seconds(),
        sig=cleanup_expired_tokens.s(),
        name="Clean up expired tokens",
    )
