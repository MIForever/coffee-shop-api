"""
Task-related schemas for Celery task results and status tracking.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

T = TypeVar('T')

class TaskStatus(str, Enum):
    """Status of a background task."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    RETRY = "RETRY"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"

class TaskResult(BaseModel):
    """Standardized response for task results."""
    status: TaskStatus = Field(..., description="Current status of the task")
    message: str = Field("", description="Human-readable message about the task status")
    data: Optional[Any] = Field(None, description="Result data from the task")
    error: Optional[Dict[str, Any]] = Field(
        None, 
        description="Error details if the task failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the task"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this result was generated"
    )
    task_id: Optional[str] = Field(
        None,
        description="Celery task ID"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "SUCCESS",
                "message": "Task completed successfully",
                "data": {"processed_items": 42},
                "error": None,
                "metadata": {"elapsed_time": 12.3},
                "timestamp": "2023-01-01T12:00:00Z",
                "task_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class TaskInfo(BaseModel):
    """Information about a Celery task."""
    task_id: str = Field(..., description="Unique task ID")
    name: str = Field(..., description="Name of the task")
    status: str = Field(..., description="Current status")
    args: List[str] = Field(
        default_factory=list,
        description="Positional arguments passed to the task"
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments passed to the task"
    )
    worker: Optional[str] = Field(
        None,
        description="Name of the worker processing the task"
    )
    received: Optional[datetime] = Field(
        None,
        description="When the task was received by the worker"
    )
    started: Optional[datetime] = Field(
        None,
        description="When the task was started by the worker"
    )
    succeeded: Optional[datetime] = Field(
        None,
        description="When the task completed successfully"
    )
    failed: Optional[datetime] = Field(
        None,
        description="When the task failed"
    )
    retries: int = Field(
        0,
        description="Number of times the task has been retried"
    )
    queue: Optional[str] = Field(
        None,
        description="Name of the queue the task was sent to"
    )
    exchange: Optional[str] = Field(
        None,
        description="Name of the exchange the task was sent to"
    )
    routing_key: Optional[str] = Field(
        None,
        description="Routing key used when the task was sent"
    )
    expires: Optional[datetime] = Field(
        None,
        description="When the task will expire"
    )
    eta: Optional[datetime] = Field(
        None,
        description="Earliest time the task will be executed"
    )
    parent_id: Optional[str] = Field(
        None,
        description="Task ID of the parent task"
    )
    root_id: Optional[str] = Field(
        None,
        description="Task ID of the root task in the workflow"
    )
    children: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Child tasks spawned by this task"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "app.tasks.example_task",
                "status": "SUCCESS",
                "args": ["arg1", 42],
                "kwargs": {"key": "value"},
                "worker": "celery@worker1",
                "received": "2023-01-01T12:00:00Z",
                "started": "2023-01-01T12:00:01Z",
                "succeeded": "2023-01-01T12:00:05Z",
                "retries": 0,
                "queue": "default"
            }
        }

class TaskStatusResponse(BaseModel):
    """Response model for task status checks."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Current status of the task")
    result: Optional[Any] = Field(
        None,
        description="Task result if completed successfully"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the task failed"
    )
    traceback: Optional[str] = Field(
        None,
        description="Full traceback if the task failed"
    )
    date_done: Optional[datetime] = Field(
        None,
        description="When the task was completed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "SUCCESS",
                "result": {"processed_items": 42},
                "date_done": "2023-01-01T12:00:05Z"
            }
        }
