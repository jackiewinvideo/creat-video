from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"


class ModelErrorCategory(str, Enum):
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMIT = "rate_limit"
    AUTH_FAILED = "auth_failed"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"


class ModelException(Exception):
    """Exception raised by Model Adapters with structured categorization."""

    def __init__(
        self,
        message: str,
        category: ModelErrorCategory = ModelErrorCategory.UNKNOWN,
        model_id: str = "",
        retryable: bool = False,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.model_id = model_id
        self.retryable = retryable
        self.status_code = status_code


class ModelRegistration(BaseModel):
    model_id: str
    display_name: str
    provider: str
    modality: ModelModality
    capabilities: List[str] = Field(default_factory=list)
    cost_per_unit: Dict[str, float] = Field(default_factory=dict)
    context_window: Optional[int] = None
    is_enabled: bool = True
    priority: int = 1  # 1 is highest priority
    description: Optional[str] = None


class ModelRequest(BaseModel):
    task_id: str
    modality: ModelModality = ModelModality.TEXT
    prompt: str
    system_prompt: Optional[str] = None
    reference_images: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    preferred_model_id: Optional[str] = None
    fallback_model_ids: List[str] = Field(default_factory=list)


class ModelSwitchLog(BaseModel):
    from_model_id: str
    to_model_id: str
    reason: str
    error_category: ModelErrorCategory
    timestamp: float


class ModelResponse(BaseModel):
    success: bool
    task_id: str
    model_id: str
    provider: str
    modality: ModelModality
    content: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    cost_estimated: float = 0.0
    execution_time_ms: float = 0.0
    switch_history: List[ModelSwitchLog] = Field(default_factory=list)
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
