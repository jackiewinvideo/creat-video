import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from backend.models.scene import Scene

logger = logging.getLogger(__name__)


class SceneStudio:
    """
    Manages scene environments, lighting bibles, location settings, and reference assets.
    """

    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = Path(storage_root or "./storage").resolve()
        self._scenes_cache: Dict[str, Scene] = {}
        self._load_all_scenes()

    def _get_project_file(self, project_id: str) -> Path:
        proj_dir = self.storage_root / "projects" / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_dir / "scenes.json"

    def _load_all_scenes(self) -> None:
        projects_dir = self.storage_root / "projects"
        if not projects_dir.exists():
            return
        for proj_folder in projects_dir.iterdir():
            if proj_folder.is_dir():
                scene_file = proj_folder / "scenes.json"
                if scene_file.exists():
                    try:
                        with open(scene_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for item in data:
                            scene = Scene.model_validate(item)
                            self._scenes_cache[scene.scene_id] = scene
                    except Exception as e:
                        logger.warning(f"Failed to load scenes from {scene_file}: {e}")

    def _save_project_scenes(self, project_id: str) -> None:
        file_path = self._get_project_file(project_id)
        scenes = [s.model_dump(mode="json") for s in self._scenes_cache.values() if s.project_id == project_id]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2, ensure_ascii=False)

    def create_scene(
        self,
        project_id: str,
        name: str,
        description: str,
        scene_number: int = 1,
        location_type: str = "EXT",
        time_of_day: str = "NIGHT",
        weather: str = "Clear",
        lighting: str = "Cinematic lighting",
        reference_asset_ids: Optional[List[str]] = None
    ) -> Scene:
        scene = Scene(
            project_id=project_id,
            scene_number=scene_number,
            name=name,
            description=description,
            location_type=location_type,
            time_of_day=time_of_day,
            weather=weather,
            lighting=lighting,
            reference_asset_ids=reference_asset_ids or []
        )
        self._scenes_cache[scene.scene_id] = scene
        self._save_project_scenes(project_id)
        logger.info(f"Created scene '{name}' (ID: {scene.scene_id}) for project {project_id}")
        return scene

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        return self._scenes_cache.get(scene_id)

    def list_scenes(self, project_id: str) -> List[Scene]:
        scenes = [s for s in self._scenes_cache.values() if s.project_id == project_id]
        return sorted(scenes, key=lambda s: s.scene_number)

    def generate_project_scene_bible(self, project_id: str) -> Dict[str, Dict[str, str]]:
        scenes = self.list_scenes(project_id)
        return {s.name: s.to_scene_bible() for s in scenes}
