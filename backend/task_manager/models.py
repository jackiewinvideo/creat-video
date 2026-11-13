from enum import Enum
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING_USER = "WAITING_USER"
    WAITING_MODEL = "WAITING_MODEL"
    WAITING_TOOL = "WAITING_TOOL"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCheckpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    step_name: str
    step_index: int
    completed_units: List[str] = Field(default_factory=list)
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    output_artifacts: List[str] = Field(default_factory=list)
    model_id: Optional[str] = None
    tool_id: Optional[str] = None
    version: str = "1.0"
    created_at: float = Field(default_factory=time.time)


class FilmTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    project_id: str
    task_type: str
    state: TaskState = TaskState.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    total_steps: int = 1
    current_step_index: int = 0
    assigned_device_id: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: List[TaskCheckpoint] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
