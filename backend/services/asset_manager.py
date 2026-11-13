import hashlib
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.asset import AssetSourceType, AssetType, MediaAsset
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Manages physical asset files, metadata extraction, hashing, categorization,
    and versioning for AI Film Studio projects.
    """

    def __init__(self, storage_root: Optional[str] = None, ffprobe_adapter: Optional[FFprobeAdapter] = None):
        self.storage_root = Path(storage_root or "./storage").resolve()
        self.ffprobe = ffprobe_adapter or FFprobeAdapter()
        self._assets_cache: Dict[str, MediaAsset] = {}
        self._load_all_project_indices()

    def _get_project_asset_dir(self, project_id: str, asset_type: AssetType) -> Path:
        p = self.storage_root / "projects" / project_id / "assets" / asset_type.value
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _get_project_index_path(self, project_id: str) -> Path:
        p = self.storage_root / "projects" / project_id / "assets"
        p.mkdir(parents=True, exist_ok=True)
        return p / "index.json"

    def _load_all_project_indices(self) -> None:
        projects_dir = self.storage_root / "projects"
        if not projects_dir.exists():
            return
        for proj_folder in projects_dir.iterdir():
            if proj_folder.is_dir():
                index_file = proj_folder / "assets" / "index.json"
                if index_file.exists():
                    try:
                        with open(index_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for item in data:
                            asset = MediaAsset.model_validate(item)
                            self._assets_cache[asset.asset_id] = asset
                    except Exception as e:
                        logger.warning(f"Failed to load asset index from {index_file}: {e}")

    def _save_project_index(self, project_id: str) -> None:
        index_file = self._get_project_index_path(project_id)
        proj_assets = [a.model_dump(mode="json") for a in self._assets_cache.values() if a.project_id == project_id]
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(proj_assets, f, indent=2, ensure_ascii=False)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192 * 1024):
                sha.update(chunk)
        return sha.hexdigest()

    def ingest_asset(
        self,
        source_file_path: str,
        project_id: str,
        asset_type: AssetType,
        source_type: AssetSourceType = AssetSourceType.USER_UPLOAD,
        source_model_or_tool: Optional[str] = None,
        prompt_used: Optional[str] = None,
        tags: Optional[List[str]] = None,
        associated_character_id: Optional[str] = None,
        associated_scene_id: Optional[str] = None,
        associated_shot_id: Optional[str] = None,
        copy_file: bool = True
    ) -> MediaAsset:
        src = Path(source_file_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {source_file_path}")

        file_name = src.name
        file_ext = src.suffix.lower().lstrip(".")
        file_size = src.stat().st_size
        checksum = self.compute_sha256(src)

        # Target destination in storage
        dest_dir = self._get_project_asset_dir(project_id, asset_type)
        asset_id = f"asset_{hashlib.md5(f'{project_id}_{file_name}_{time.time()}'.encode()).hexdigest()[:12]}"
        dest_file_name = f"{asset_id}_v1_{file_name}"
        dest_path = dest_dir / dest_file_name

        if copy_file:
            shutil.copy2(src, dest_path)
        else:
            shutil.move(str(src), str(dest_path))

        # Media probing via FFprobe for video/audio
        duration = None
        resolution = None
        fps = None

        if file_ext in ("mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "aac", "flac", "ogg"):
            try:
                probe_res = self.ffprobe.probe(str(dest_path))
                if probe_res.get("video"):
                    v = probe_res["video"]
                    resolution = f"{v.get('width')}x{v.get('height')}"
                    fps = v.get("fps")
                    duration = v.get("duration")
                elif probe_res.get("audio"):
                    duration = probe_res["audio"].get("duration")
            except Exception as pe:
                logger.debug(f"Media probe skipped or failed for {dest_file_name}: {pe}")

        asset = MediaAsset(
            asset_id=asset_id,
            project_id=project_id,
            asset_type=asset_type,
            source_type=source_type,
            file_path=str(dest_path),
            file_name=file_name,
            file_format=file_ext,
            file_size_bytes=file_size,
            duration_seconds=duration,
            resolution=resolution,
            fps=fps,
            version=1,
            source_model_or_tool=source_model_or_tool,
            prompt_used=prompt_used,
            tags=tags or [],
            associated_character_id=associated_character_id,
            associated_scene_id=associated_scene_id,
            associated_shot_id=associated_shot_id,
            checksum_sha256=checksum
        )

        self._assets_cache[asset_id] = asset
        self._save_project_index(project_id)
        logger.info(f"Ingested asset {asset_id} ({asset_type.value}) for project {project_id}")
        return asset

    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        return self._assets_cache.get(asset_id)

    def list_assets(
        self,
        project_id: str,
        asset_type: Optional[AssetType] = None,
        character_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[MediaAsset]:
        results = [a for a in self._assets_cache.values() if a.project_id == project_id]
        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]
        if character_id:
            results = [a for a in results if a.associated_character_id == character_id]
        if scene_id:
            results = [a for a in results if a.associated_scene_id == scene_id]
        if tag:
            results = [a for a in results if tag in a.tags]
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    def create_new_version(
        self,
        asset_id: str,
        new_source_path: str,
        source_model_or_tool: Optional[str] = None,
        prompt_used: Optional[str] = None
    ) -> MediaAsset:
        existing = self.get_asset(asset_id)
        if not existing:
            raise ValueError(f"Asset '{asset_id}' not found.")

        src = Path(new_source_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"New version file not found: {new_source_path}")

        new_version = existing.version + 1
        dest_dir = self._get_project_asset_dir(existing.project_id, existing.asset_type)
        dest_file_name = f"{asset_id}_v{new_version}_{src.name}"
        dest_path = dest_dir / dest_file_name

        shutil.copy2(src, dest_path)

        existing.version = new_version
        existing.file_path = str(dest_path)
        existing.file_name = src.name
        existing.file_size_bytes = dest_path.stat().st_size
        existing.checksum_sha256 = self.compute_sha256(dest_path)
        existing.updated_at = time.time()
        if source_model_or_tool:
            existing.source_model_or_tool = source_model_or_tool
        if prompt_used:
            existing.prompt_used = prompt_used

        self._save_project_index(existing.project_id)
        logger.info(f"Updated asset {asset_id} to version {new_version}")
        return existing
