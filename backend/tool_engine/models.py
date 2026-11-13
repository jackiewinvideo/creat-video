from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolType(str, Enum):
    CLI = "cli"
    SDK = "sdk"
    API = "api"
    SERVICE = "service"


class ToolStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    UNHEALTHY = "unhealthy"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


class ExecutionLocation(str, Enum):
    LOCAL = "local"
    WORKER = "worker"
    REMOTE = "remote"


class RetryPolicy(BaseModel):
    max_retries: int = Field(default=0, ge=0)
    backoff_seconds: float = Field(default=1.0, ge=0.0)
    retryable_exit_codes: List[int] = Field(default_factory=list)


class ToolRegistration(BaseModel):
    tool_id: str
    tool_name: str
    tool_type: ToolType
    version: str = "unknown"
    provider: str = "system"
    capabilities: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, description="Default timeout in seconds")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    license: str = "Unknown"
    execution_location: ExecutionLocation = ExecutionLocation.LOCAL
    status: ToolStatus = ToolStatus.NOT_INSTALLED
    executable_path: Optional[str] = None
    description: Optional[str] = None


class ToolExecutionRequest(BaseModel):
    task_id: str
    tool_id: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)
    output_path: Optional[str] = None
    timeout: Optional[int] = None


class ToolExecutionResult(BaseModel):
    success: bool
    tool_id: str
    action: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    output_files: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
