import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Shot(BaseModel):
    shot_id: str = Field(default_factory=lambda: f"shot_{uuid.uuid4().hex[:12]}")
    project_id: str
    scene_id: str
    shot_number: int = 1
    shot_type: str = "MEDIUM"  # WIDE, MEDIUM, CLOSE_UP, EXTREME_CLOSE_UP
    camera_movement: str = "STATIC"  # STATIC, PAN_RIGHT, DOLLY_IN, TRACKING
    visual_description: str
    character_ids: List[str] = Field(default_factory=list)
    dialogue: Optional[str] = None
    dialogue_character_id: Optional[str] = None
    estimated_duration: float = 3.0
    anchor_image_asset_id: Optional[str] = None
    rendered_video_asset_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class Storyboard(BaseModel):
    storyboard_id: str = Field(default_factory=lambda: f"sb_{uuid.uuid4().hex[:12]}")
    project_id: str
    title: str
    shots: List[Shot] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def total_duration(self) -> float:
        return sum(s.estimated_duration for s in self.shots)
