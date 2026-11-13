from enum import Enum
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ConsistencyReviewStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class CharacterIdentity(BaseModel):
    facial_features: str = Field(description="Facial features, bone structure, eye shape")
    age: int
    gender: str
    ethnicity: Optional[str] = None
    distinguishing_marks: Optional[str] = None


class CharacterAppearance(BaseModel):
    hair_style: str
    hair_color: str
    skin_tone: str
    body_build: str
    height_cm: Optional[int] = None
    posture: Optional[str] = None


class CharacterCostume(BaseModel):
    costume_id: str = Field(default_factory=lambda: f"costume_{uuid.uuid4().hex[:8]}")
    name: str = "Standard Outfit"
    scene_tags: List[str] = Field(default_factory=list)
    top: str
    bottom: str
    shoes: Optional[str] = None
    accessories: List[str] = Field(default_factory=list)
    color_palette: List[str] = Field(default_factory=list)
    materials: Optional[str] = None


class VoiceSetting(BaseModel):
    provider: str = "elevenlabs"
    voice_id: str
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: Optional[str] = None


class Character(BaseModel):
    character_id: str = Field(default_factory=lambda: f"char_{uuid.uuid4().hex[:12]}")
    project_id: str
    name: str
    role_description: str
    identity: CharacterIdentity
    appearance: CharacterAppearance
    costumes: List[CharacterCostume] = Field(default_factory=list)
    voice: Optional[VoiceSetting] = None
    reference_asset_ids: List[str] = Field(default_factory=list)
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def to_character_bible(self) -> Dict[str, str]:
        """Compiles identity, appearance, and primary costume into a prompt-ready bible."""
        primary_costume = self.costumes[0] if self.costumes else None
        costume_desc = f"{primary_costume.top}, {primary_costume.bottom}" if primary_costume else "Standard casual attire"

        return {
            "name": self.name,
            "identity_prompt": f"{self.identity.age}-year-old {self.identity.gender}, {self.identity.facial_features}",
            "appearance_prompt": f"{self.appearance.hair_style} {self.appearance.hair_color} hair, {self.appearance.skin_tone} skin, {self.appearance.body_build} build",
            "costume_prompt": costume_desc,
            "negative_prompt": "deformed face, inconsistent eyes, extra limbs, bad anatomy"
        }
