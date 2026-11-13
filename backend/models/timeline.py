from enum import Enum
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TimelineTrackType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    MUSIC = "music"
    SFX = "sfx"
    SUBTITLE = "subtitle"


class TimelineClip(BaseModel):
    clip_id: str = Field(default_factory=lambda: f"clip_{uuid.uuid4().hex[:8]}")
    track_type: TimelineTrackType
    asset_id: Optional[str] = None
    file_path: str
    timeline_start: float = 0.0
    source_start: float = 0.0
    duration: float = 3.0
    volume: float = 1.0


class Timeline(BaseModel):
    timeline_id: str = Field(default_factory=lambda: f"tl_{uuid.uuid4().hex[:12]}")
    project_id: str
    resolution: str = "1280x720"
    fps: int = 24
    video_clips: List[TimelineClip] = Field(default_factory=list)
    audio_clips: List[TimelineClip] = Field(default_factory=list)
    music_clips: List[TimelineClip] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

    def total_duration(self) -> float:
        all_clips = self.video_clips + self.audio_clips + self.music_clips
        if not all_clips:
            return 0.0
        return max(c.timeline_start + c.duration for c in all_clips)
