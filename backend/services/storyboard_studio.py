import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from backend.models.storyboard import Shot, Storyboard

logger = logging.getLogger(__name__)


class StoryboardStudio:
    """
    Manages storyboards, shots, camera directives, and prompt compilation.
    """

    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = Path(storage_root or "./storage").resolve()
        self._storyboards_cache: Dict[str, Storyboard] = {}
        self._load_all_storyboards()

    def _get_project_file(self, project_id: str) -> Path:
        proj_dir = self.storage_root / "projects" / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_dir / "storyboards.json"

    def _load_all_storyboards(self) -> None:
        projects_dir = self.storage_root / "projects"
        if not projects_dir.exists():
            return
        for proj_folder in projects_dir.iterdir():
            if proj_folder.is_dir():
                sb_file = proj_folder / "storyboards.json"
                if sb_file.exists():
                    try:
                        with open(sb_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for item in data:
                            sb = Storyboard.model_validate(item)
                            self._storyboards_cache[sb.storyboard_id] = sb
                    except Exception as e:
                        logger.warning(f"Failed to load storyboards from {sb_file}: {e}")

    def _save_project_storyboards(self, project_id: str) -> None:
        file_path = self._get_project_file(project_id)
        sbs = [s.model_dump(mode="json") for s in self._storyboards_cache.values() if s.project_id == project_id]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sbs, f, indent=2, ensure_ascii=False)

    def create_storyboard(self, project_id: str, title: str) -> Storyboard:
        sb = Storyboard(project_id=project_id, title=title, shots=[])
        self._storyboards_cache[sb.storyboard_id] = sb
        self._save_project_storyboards(project_id)
        logger.info(f"Created storyboard '{title}' (ID: {sb.storyboard_id}) for project {project_id}")
        return sb

    def add_shot(self, storyboard_id: str, shot: Shot) -> Optional[Storyboard]:
        sb = self._storyboards_cache.get(storyboard_id)
        if sb:
            shot.shot_number = len(sb.shots) + 1
            sb.shots.append(shot)
            self._save_project_storyboards(sb.project_id)
        return sb

    def get_storyboard(self, storyboard_id: str) -> Optional[Storyboard]:
        return self._storyboards_cache.get(storyboard_id)

    def list_storyboards(self, project_id: str) -> List[Storyboard]:
        return [s for s in self._storyboards_cache.values() if s.project_id == project_id]

    @staticmethod
    def compile_shot_prompts(
        shot: Shot,
        character_bibles: Dict[str, Dict[str, str]],
        scene_bible: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Combines shot camera setup, character visual identity, and scene atmosphere
        into a finalized image/video prompt.
        """
        char_prompts = []
        for char_name, bible in character_bibles.items():
            char_prompts.append(
                f"{char_name} ({bible.get('identity_prompt', '')}, wearing {bible.get('costume_prompt', '')})"
            )

        chars_str = "; ".join(char_prompts) if char_prompts else "No characters"
        scene_str = scene_bible.get("setting_prompt", "") if scene_bible else "Cinematic background"
        lighting_str = scene_bible.get("lighting_prompt", "") if scene_bible else "Volumetric lighting"

        image_prompt = (
            f"Cinematic {shot.shot_type} shot, {shot.visual_description}. "
            f"Featuring {chars_str}. Setting: {scene_str}. {lighting_str}, 8k resolution, film grain."
        )

        video_prompt = (
            f"{image_prompt} Camera movement: {shot.camera_movement}. "
            f"Smooth 24fps motion, photorealistic cinematography."
        )

        return {
            "image_prompt": image_prompt,
            "video_prompt": video_prompt,
            "negative_prompt": "cartoon, 3d render, extra fingers, blurry, watermark, low quality"
        }
