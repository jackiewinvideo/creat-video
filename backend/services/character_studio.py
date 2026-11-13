import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.character import (
    Character,
    CharacterAppearance,
    CharacterCostume,
    CharacterIdentity,
    ConsistencyReviewStatus,
)

logger = logging.getLogger(__name__)


class CharacterStudio:
    """
    Manages multi-character creation, identity-appearance-costume separation,
    character bibles, reference images, and consistency evaluation.
    """

    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = Path(storage_root or "./storage").resolve()
        self._characters_cache: Dict[str, Character] = {}
        self._load_all_characters()

    def _get_project_file(self, project_id: str) -> Path:
        proj_dir = self.storage_root / "projects" / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_dir / "characters.json"

    def _load_all_characters(self) -> None:
        projects_dir = self.storage_root / "projects"
        if not projects_dir.exists():
            return
        for proj_folder in projects_dir.iterdir():
            if proj_folder.is_dir():
                char_file = proj_folder / "characters.json"
                if char_file.exists():
                    try:
                        with open(char_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for item in data:
                            char = Character.model_validate(item)
                            self._characters_cache[char.character_id] = char
                    except Exception as e:
                        logger.warning(f"Failed to load characters from {char_file}: {e}")

    def _save_project_characters(self, project_id: str) -> None:
        file_path = self._get_project_file(project_id)
        chars = [c.model_dump(mode="json") for c in self._characters_cache.values() if c.project_id == project_id]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chars, f, indent=2, ensure_ascii=False)

    def create_character(
        self,
        project_id: str,
        name: str,
        role_description: str,
        identity: CharacterIdentity,
        appearance: CharacterAppearance,
        costumes: Optional[List[CharacterCostume]] = None,
        reference_asset_ids: Optional[List[str]] = None
    ) -> Character:
        char = Character(
            project_id=project_id,
            name=name,
            role_description=role_description,
            identity=identity,
            appearance=appearance,
            costumes=costumes or [],
            reference_asset_ids=reference_asset_ids or []
        )
        self._characters_cache[char.character_id] = char
        self._save_project_characters(project_id)
        logger.info(f"Created character '{name}' (ID: {char.character_id}) for project {project_id}")
        return char

    def get_character(self, character_id: str) -> Optional[Character]:
        return self._characters_cache.get(character_id)

    def list_characters(self, project_id: str) -> List[Character]:
        return [c for c in self._characters_cache.values() if c.project_id == project_id]

    def add_reference_asset(self, character_id: str, asset_id: str) -> Optional[Character]:
        char = self.get_character(character_id)
        if char and asset_id not in char.reference_asset_ids:
            char.reference_asset_ids.append(asset_id)
            self._save_project_characters(char.project_id)
        return char

    def generate_project_character_bible(self, project_id: str) -> Dict[str, Dict[str, str]]:
        chars = self.list_characters(project_id)
        return {c.name: c.to_character_bible() for c in chars}

    def evaluate_consistency(
        self,
        character_id: str,
        detected_features: Dict[str, str]
    ) -> ConsistencyReviewStatus:
        """
        Evaluates detected visual features against character ground truth.
        """
        char = self.get_character(character_id)
        if not char:
            return ConsistencyReviewStatus.FAIL

        # Compare basic appearance attributes
        score = 1.0
        if "hair_color" in detected_features and detected_features["hair_color"].lower() != char.appearance.hair_color.lower():
            score -= 0.3
        if "gender" in detected_features and detected_features["gender"].lower() != char.identity.gender.lower():
            score -= 0.5

        if score >= 0.8:
            return ConsistencyReviewStatus.PASS
        elif score >= 0.5:
            return ConsistencyReviewStatus.WARNING
        elif score >= 0.3:
            return ConsistencyReviewStatus.REVIEW
        return ConsistencyReviewStatus.FAIL
