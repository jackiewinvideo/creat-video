import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Scene(BaseModel):
    scene_id: str = Field(default_factory=lambda: f"scene_{uuid.uuid4().hex[:12]}")
    project_id: str
    scene_number: int = 1
    name: str
    location_type: str = "EXT"  # INT or EXT
    time_of_day: str = "NIGHT"
    weather: Optional[str] = "Clear"
    lighting: Optional[str] = "Cinematic dramatic lighting"
    description: str
    reference_asset_ids: List[str] = Field(default_factory=list)
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def to_scene_bible(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "setting_prompt": f"{self.location_type}. {self.name}, {self.time_of_day}, {self.weather}",
            "lighting_prompt": f"Lighting: {self.lighting}",
            "description": self.description
        }
