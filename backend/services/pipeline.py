import logging
import os
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.device_manager.manager import DeviceManager
from backend.editing.editor import EditingStudio
from backend.model_hub.models import ModelModality, ModelRequest
from backend.model_hub.router import ModelRouter
from backend.models.asset import AssetSourceType, AssetType
from backend.models.character import (
    CharacterAppearance,
    CharacterCostume,
    CharacterIdentity,
    ConsistencyReviewStatus,
)
from backend.models.storyboard import Shot
from backend.models.timeline import Timeline, TimelineClip, TimelineTrackType
from backend.services.asset_manager import AssetManager
from backend.services.character_studio import CharacterStudio
from backend.services.review_engine import FilmReviewReport, ReviewEngine
from backend.services.scene_studio import SceneStudio
from backend.services.storyboard_studio import StoryboardStudio
from backend.task_manager.manager import TaskManager
from backend.task_manager.models import TaskState
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_engine.engine import ToolExecutionEngine

logger = logging.getLogger(__name__)


class FilmProductionResult(BaseModel):
    success: bool
    task_id: str
    project_id: str
    master_video_path: Optional[str] = None
    master_asset_id: Optional[str] = None
    review_report: Optional[FilmReviewReport] = None
    total_shots: int = 0
    total_runtime_seconds: float = 0.0
    checkpoints_count: int = 0
    error_message: Optional[str] = None


class FilmProductionPipeline:
    """
    End-to-End Autonomous Film Studio Orchestrator.
    Executes the 6-stage lifecycle specified in Section 4 of the specification:
    Development -> Pre-production -> Production -> Post-production -> Review -> Delivery.
    """

    def __init__(
        self,
        storage_root: Optional[str] = None,
        tool_engine: Optional[ToolExecutionEngine] = None,
        model_router: Optional[ModelRouter] = None,
        task_manager: Optional[TaskManager] = None,
        asset_manager: Optional[AssetManager] = None,
        character_studio: Optional[CharacterStudio] = None,
        scene_studio: Optional[SceneStudio] = None,
        storyboard_studio: Optional[StoryboardStudio] = None,
        editing_studio: Optional[EditingStudio] = None,
        review_engine: Optional[ReviewEngine] = None
    ):
        self.storage_root = storage_root or "./storage"
        self.tool_engine = tool_engine or ToolExecutionEngine()
        self.task_manager = task_manager or TaskManager()
        self.asset_manager = asset_manager or AssetManager(storage_root=self.storage_root)
        self.character_studio = character_studio or CharacterStudio(storage_root=self.storage_root)
        self.scene_studio = scene_studio or SceneStudio(storage_root=self.storage_root)
        self.storyboard_studio = storyboard_studio or StoryboardStudio(storage_root=self.storage_root)
        self.editing_studio = editing_studio or EditingStudio(storage_root=self.storage_root, tool_engine=self.tool_engine)
        self.review_engine = review_engine or ReviewEngine()
        self.model_router = model_router

    def run_production(
        self,
        project_id: str,
        story_prompt: str,
        character_name: str = "Elena",
        num_shots: int = 2
    ) -> FilmProductionResult:
        logger.info(f"Initiating autonomous film production for project: {project_id}")

        # Initialize Master Task
        task = self.task_manager.create_task(
            project_id=project_id,
            task_type="complete_film_production",
            inputs={"story_prompt": story_prompt, "character_name": character_name, "num_shots": num_shots},
            total_steps=5
        )
        self.task_manager.update_state(task.task_id, TaskState.RUNNING)

        try:
            # -------------------------------------------------------------
            # Stage 1: Development (Concept & Script)
            # -------------------------------------------------------------
            script_text = f"Title: Shadows of Code\nPremise: {story_prompt}\nScene 1: Cyber City Dawn."
            if self.model_router:
                req_model = ModelRequest(
                    task_id=task.task_id,
                    modality=ModelModality.TEXT,
                    prompt=f"Write a 2-shot micro-movie screenplay based on: {story_prompt}"
                )
                m_res = self.model_router.execute(req_model)
                if m_res.success and m_res.content:
                    script_text = m_res.content

            self.task_manager.record_checkpoint(
                task_id=task.task_id,
                step_name="stage_1_development",
                step_index=1,
                completed_units=["screenplay"],
                state_snapshot={"screenplay": script_text}
            )

            # -------------------------------------------------------------
            # Stage 2: Pre-production (Character, Scene, Storyboard Bible)
            # -------------------------------------------------------------
            char = self.character_studio.create_character(
                project_id=project_id,
                name=character_name,
                role_description="Lead cybernetic detective",
                identity=CharacterIdentity(facial_features="Sharp jawline, determined eyes", age=28, gender="female"),
                appearance=CharacterAppearance(hair_style="Cyber-bob", hair_color="Silver", skin_tone="Pale", body_build="Athletic"),
                costumes=[CharacterCostume(top="Matte black tactical trench coat", bottom="Combat trousers")]
            )

            scene = self.scene_studio.create_scene(
                project_id=project_id,
                name="Neo-Metropolis Downtown",
                description="Hologram rain and neon reflections",
                time_of_day="NIGHT"
            )

            storyboard = self.storyboard_studio.create_storyboard(project_id, title="Main Storyboard")
            shot1 = Shot(
                project_id=project_id,
                scene_id=scene.scene_id,
                shot_number=1,
                shot_type="WIDE",
                camera_movement="PAN_RIGHT",
                visual_description=f"{character_name} looking over neon city skyline",
                character_ids=[char.character_id],
                estimated_duration=2.0
            )
            shot2 = Shot(
                project_id=project_id,
                scene_id=scene.scene_id,
                shot_number=2,
                shot_type="CLOSE_UP",
                camera_movement="DOLLY_IN",
                visual_description=f"{character_name} turns towards camera with glowing cybernetic eye",
                character_ids=[char.character_id],
                estimated_duration=2.0
            )
            self.storyboard_studio.add_shot(storyboard.storyboard_id, shot1)
            self.storyboard_studio.add_shot(storyboard.storyboard_id, shot2)

            self.task_manager.record_checkpoint(
                task_id=task.task_id,
                step_name="stage_2_preproduction",
                step_index=2,
                completed_units=["character_bible", "scene_bible", "storyboard"],
                state_snapshot={"storyboard_id": storyboard.storyboard_id}
            )

            # -------------------------------------------------------------
            # Stage 3: Production (Asset Generation for each Shot)
            # -------------------------------------------------------------
            ffmpeg_adapter = self.tool_engine.registry.get_adapter("ffmpeg")
            if not isinstance(ffmpeg_adapter, FFmpegAdapter):
                ffmpeg_adapter = FFmpegAdapter()

            rendered_clip_paths = []
            shot_colors = ["blue", "purple"]

            for idx, shot in enumerate([shot1, shot2]):
                clip_path = os.path.join(self.storage_root, "projects", project_id, f"shot_{idx+1}.mp4")
                gen_res = ffmpeg_adapter.generate_test_pattern(
                    output_file=clip_path,
                    duration=shot.estimated_duration,
                    resolution="640x360",
                    fps=24,
                    color=shot_colors[idx % len(shot_colors)]
                )
                if not gen_res.success:
                    raise RuntimeError(f"Failed to generate shot {idx+1}: {gen_res.error_message}")

                # Ingest into AssetManager
                ingested = self.asset_manager.ingest_asset(
                    source_file_path=clip_path,
                    project_id=project_id,
                    asset_type=AssetType.VIDEO,
                    source_type=AssetSourceType.AI_GENERATED,
                    source_model_or_tool="ffmpeg",
                    associated_character_id=char.character_id,
                    associated_scene_id=scene.scene_id,
                    associated_shot_id=shot.shot_id
                )
                rendered_clip_paths.append(ingested.file_path)

            self.task_manager.record_checkpoint(
                task_id=task.task_id,
                step_name="stage_3_production",
                step_index=3,
                completed_units=["shot_1_render", "shot_2_render"],
                state_snapshot={"clip_paths": rendered_clip_paths},
                output_artifacts=rendered_clip_paths
            )

            # -------------------------------------------------------------
            # Stage 4: Post-production (Timeline Assembly & Master Export)
            # -------------------------------------------------------------
            timeline = Timeline(
                project_id=project_id,
                resolution="640x360",
                fps=24,
                video_clips=[
                    TimelineClip(track_type=TimelineTrackType.VIDEO, file_path=rendered_clip_paths[0], duration=2.0),
                    TimelineClip(track_type=TimelineTrackType.VIDEO, file_path=rendered_clip_paths[1], duration=2.0)
                ]
            )

            master_path = os.path.join(self.storage_root, "projects", project_id, "master", "master_film.mp4")
            render_res = self.editing_studio.render_timeline(timeline, output_file_path=master_path)
            if not render_res.success or not os.path.exists(master_path):
                raise RuntimeError(f"Timeline editing failed: {render_res.error_message}")

            master_asset = self.asset_manager.ingest_asset(
                source_file_path=master_path,
                project_id=project_id,
                asset_type=AssetType.FINAL_DELIVERABLE,
                source_type=AssetSourceType.DERIVED,
                source_model_or_tool="editing_studio_ffmpeg"
            )

            self.task_manager.record_checkpoint(
                task_id=task.task_id,
                step_name="stage_4_postproduction",
                step_index=4,
                completed_units=["timeline_assembly", "master_export"],
                state_snapshot={"master_asset_id": master_asset.asset_id},
                output_artifacts=[master_asset.file_path]
            )

            # -------------------------------------------------------------
            # Stage 5 & 6: Review and Exhibition / Delivery
            # -------------------------------------------------------------
            review_report = self.review_engine.review_master_video(
                video_path=master_asset.file_path,
                expected_min_duration=3.5,
                expected_resolution="640x360"
            )

            self.task_manager.record_checkpoint(
                task_id=task.task_id,
                step_name="stage_5_6_review_delivery",
                step_index=5,
                completed_units=["quality_review", "delivery_package"],
                state_snapshot={"review_status": review_report.overall_status.value}
            )

            self.task_manager.update_state(task.task_id, TaskState.COMPLETED)

            return FilmProductionResult(
                success=True,
                task_id=task.task_id,
                project_id=project_id,
                master_video_path=master_asset.file_path,
                master_asset_id=master_asset.asset_id,
                review_report=review_report,
                total_shots=len(rendered_clip_paths),
                total_runtime_seconds=master_asset.duration_seconds or 4.0,
                checkpoints_count=len(self.task_manager.get_task(task.task_id).checkpoints)
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            self.task_manager.update_state(task.task_id, TaskState.FAILED, error_message=str(e))
            return FilmProductionResult(
                success=False,
                task_id=task.task_id,
                project_id=project_id,
                error_message=str(e)
            )
