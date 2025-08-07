"""
Celery task utilities including base task class and error handling.
"""
import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

from celery import Task, shared_task
from celery.exceptions import MaxRetriesExceededError, Retry, SoftTimeLimitExceeded
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.config import settings
from app.db.deps import get_db
from app.schemas.task import TaskResult, TaskStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = TypeVar('P', bound=BaseModel)

class TaskError(Exception):
    """Base exception for task errors."""
    def __init__(self, message: str, code: str = "task_error", details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class TaskRetryError(TaskError):
    """Exception for task retries."""
    def __init__(self, message: str, retry_in: int = 60, **kwargs):
        super().__init__(message, "task_retry_error", kwargs)
        self.retry_in = retry_in

class TaskValidationError(TaskError):
    """Exception for task validation errors."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "validation_error", details or {})

class BaseTask(Task):
    """Base Celery task with error handling and monitoring."""
    # Default task settings
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # 1 minute
    time_limit = 60 * 10  # 10 minutes
    soft_time_limit = 60 * 9  # 9 minutes
    acks_late = True
    ignore_result = False
    track_started = True
    
    # Custom task properties
    task_type: str = "base"
    task_name: str = "base_task"
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._db_session: Optional[AsyncSession] = None
    
    @property
    def db(self) -> AsyncSession:
        """Get a database session."""
        if self._db_session is None:
            self._db_session = get_db()
        return self._db_session
    
    async def on_success(self, retval, task_id, args, kwargs):
        """Called when the task succeeds."""
        runtime = time.time() - self._start_time if self._start_time else 0
        logger.info(
            f"Task {self.name}[{task_id}] succeeded in {runtime:.2f}s",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "runtime": runtime,
                "status": "success",
            },
        )
        
        # Close the database session if it was opened
        if self._db_session:
            await self._db_session.close()
    
    async def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when the task is retried."""
        retries = self.request.retries
        logger.warning(
            f"Retrying task {self.name}[{task_id}] (attempt {retries + 1}/{self.max_retries})",
            exc_info=exc,
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "retry_count": retries,
                "max_retries": self.max_retries,
                "exception": str(exc),
                "status": "retry",
            },
        )
    
    async def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when the task fails."""
        runtime = time.time() - self._start_time if self._start_time else 0
        logger.error(
            f"Task {self.name}[{task_id}] failed after {runtime:.2f}s: {str(exc)}",
            exc_info=exc,
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "runtime": runtime,
                "exception": str(exc),
                "status": "failure",
            },
        )
        
        # Close the database session if it was opened
        if self._db_session:
            await self._db_session.close()
    
    def run(self, *args, **kwargs):
        """Task entry point."""
        self._start_time = time.time()
        return super().run(*args, **kwargs)

def task(
    *args,
    base: Type[BaseTask] = BaseTask,
    bind: bool = True,
    max_retries: Optional[int] = None,
    default_retry_delay: Optional[int] = None,
    time_limit: Optional[int] = None,
    soft_time_limit: Optional[int] = None,
    **options,
):
    """Decorator to create a Celery task with proper configuration."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Create a task class that inherits from the base class
        task_class = type(
            f"{func.__name__.title()}Task",
            (base,),
            {
                "name": f"app.tasks.{func.__module__.split('.')[-1]}.{func.__name__}",
                "task_type": options.get("task_type", "background"),
                "task_name": func.__name__,
                "max_retries": max_retries or base.max_retries,
                "default_retry_delay": default_retry_delay or base.default_retry_delay,
                "time_limit": time_limit or base.time_limit,
                "soft_time_limit": soft_time_limit or base.soft_time_limit,
                "run": staticmethod(func),
            },
        )
        
        # Register the task with Celery
        task = celery_app.task(
            task_class,
            bind=bind,
            base=task_class,
            **options,
        )
        
        # Add async support
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            def async_wrapper(*args, **kwargs):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(func(*args, **kwargs))
            
            task.original = func
            task.async_run = func
            
            return task
            
        return task
    
    # Handle both @task and @task() syntax
    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator

# Example usage:
# @task(bind=True, max_retries=3)
# async def process_data(self, data: dict) -> dict:
#     # Task implementation here
#     pass

def create_task_result(
    status: TaskStatus,
    message: str = "",
    data: Optional[Any] = None,
    error: Optional[Union[str, Exception]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> TaskResult:
    """Create a standardized task result."""
    error_details = None
    
    if isinstance(error, Exception):
        error_details = {
            "type": error.__class__.__name__,
            "message": str(error),
            "details": getattr(error, "details", None),
        }
    elif error is not None:
        error_details = {"message": str(error)}
    
    return TaskResult(
        status=status,
        message=message,
        data=data,
        error=error_details,
        metadata=metadata or {},
        timestamp=datetime.utcnow(),
    )

def retry_on_exception(
    exc: Exception,
    task: Task,
    max_retries: Optional[int] = None,
    countdown: Optional[int] = None,
    **kwargs,
) -> None:
    """Helper to retry a task on exception with exponential backoff."""
    max_retries = max_retries or task.max_retries
    countdown = countdown or task.default_retry_delay
    
    try:
        retry_count = task.request.retries
        retry_delay = min(countdown * (2 ** retry_count), 3600)  # Cap at 1 hour
        
        if retry_count < max_retries:
            raise task.retry(
                exc=exc,
                countdown=retry_delay,
                max_retries=max_retries,
                **kwargs,
            )
        else:
            logger.error(
                f"Max retries ({max_retries}) exceeded for task {task.name}",
                exc_info=exc,
            )
    except MaxRetriesExceededError:
        logger.error(
            f"Max retries ({max_retries}) exceeded for task {task.name}",
            exc_info=exc,
        )
        raise
    except Exception as e:
        logger.error(
            f"Error while retrying task {task.name}",
            exc_info=e,
        )
        raise exc from e
