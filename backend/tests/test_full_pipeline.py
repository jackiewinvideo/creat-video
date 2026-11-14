import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.models.character import ConsistencyReviewStatus
from backend.services.asset_manager import AssetManager
from backend.services.character_studio import CharacterStudio
from backend.editing.editor import EditingStudio
from backend.services.pipeline import FilmProductionPipeline
from backend.services.review_engine import ReviewEngine
from backend.services.scene_studio import SceneStudio
from backend.services.storyboard_studio import StoryboardStudio
from backend.task_manager.manager import TaskManager
from backend.task_manager.models import TaskState
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.security import ToolSecurityManager


@pytest.fixture
def temp_workspace():
    d = tempfile.mkdtemp(prefix="ai_film_pipeline_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_autonomous_film_production_pipeline(temp_workspace):
    sec = ToolSecurityManager(allowed_directories=[temp_workspace, os.getcwd()])
    reg = ToolRegistry()
    ffmpeg = FFmpegAdapter(security_manager=sec)
    ffprobe = FFprobeAdapter(security_manager=sec)
    reg.register_adapter(ffmpeg)
    reg.register_adapter(ffprobe)
    engine = ToolExecutionEngine(registry=reg, security_manager=sec)

    pipeline = FilmProductionPipeline(
        storage_root=temp_workspace,
        tool_engine=engine,
        task_manager=TaskManager(),
        asset_manager=AssetManager(storage_root=temp_workspace, ffprobe_adapter=ffprobe),
        character_studio=CharacterStudio(storage_root=temp_workspace),
        scene_studio=SceneStudio(storage_root=temp_workspace),
        storyboard_studio=StoryboardStudio(storage_root=temp_workspace),
        editing_studio=EditingStudio(storage_root=temp_workspace, tool_engine=engine),
        review_engine=ReviewEngine(ffprobe_adapter=ffprobe)
    )

    result = pipeline.run_production(
        project_id="proj_cyber_rebel",
        story_prompt="A cyber detective discovers a rogue AI in neo-city.",
        character_name="Kaelen",
        num_shots=2
    )

    assert result.success is True
    assert result.master_video_path is not None
    assert os.path.exists(result.master_video_path)
    assert os.path.getsize(result.master_video_path) > 0
    assert result.total_shots == 2
    assert result.checkpoints_count == 5
    assert result.review_report.overall_status in (ConsistencyReviewStatus.PASS, ConsistencyReviewStatus.WARNING)


def test_fastapi_endpoints():
    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Devices check
    res_devices = client.get("/api/devices")
    assert res_devices.status_code == 200
    assert len(res_devices.json()) >= 1

    # 3. Tools check
    res_tools = client.get("/api/tools")
    assert res_tools.status_code == 200
    tool_ids = [t["tool_id"] for t in res_tools.json()]
    assert "ffmpeg" in tool_ids
    assert "ffprobe" in tool_ids

    # 5. Web Terminal Dashboard check
    res_ui = client.get("/")
    assert res_ui.status_code == 200
    assert "AI Film Studio" in res_ui.text
