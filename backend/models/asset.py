from enum import Enum
import time
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    CHARACTER = "character"
    SCENE = "scene"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"
    SFX = "sfx"
    SUBTITLE = "subtitle"
    GENERATED = "generated"
    FINAL_DELIVERABLE = "final_deliverable"


class AssetSourceType(str, Enum):
    USER_UPLOAD = "user_upload"
    AI_GENERATED = "ai_generated"
    DERIVED = "derived"


class MediaAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: f"asset_{uuid.uuid4().hex[:12]}")
    project_id: str
    asset_type: AssetType
    source_type: AssetSourceType = AssetSourceType.USER_UPLOAD
    file_path: str
    file_name: str
    file_format: str
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    version: int = 1
    source_model_or_tool: Optional[str] = None
    prompt_used: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    associated_character_id: Optional[str] = None
    associated_scene_id: Optional[str] = None
    associated_shot_id: Optional[str] = None
    checksum_sha256: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
