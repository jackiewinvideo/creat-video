import os
import shutil
import tempfile
import pytest

from backend.editing.editor import EditingStudio
from backend.models.character import ConsistencyReviewStatus
from backend.models.timeline import Timeline, TimelineClip, TimelineTrackType
from backend.services.review_engine import ReviewEngine
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.security import ToolSecurityManager


@pytest.fixture
def temp_workspace():
    d = tempfile.mkdtemp(prefix="ai_film_edit_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_editing_and_quality_review_engine(temp_workspace):
    sec = ToolSecurityManager(allowed_directories=[temp_workspace, os.getcwd()])
    reg = ToolRegistry()
    ffmpeg = FFmpegAdapter(security_manager=sec)
    ffprobe = FFprobeAdapter(security_manager=sec)
    reg.register_adapter(ffmpeg)
    reg.register_adapter(ffprobe)
    engine = ToolExecutionEngine(registry=reg, security_manager=sec)

    # 1. Generate two 1.5s video clips
    clip1 = os.path.join(temp_workspace, "clip1.mp4")
    clip2 = os.path.join(temp_workspace, "clip2.mp4")
    ffmpeg.generate_test_pattern(output_file=clip1, duration=1.5, resolution="640x360", fps=24, color="blue")
    ffmpeg.generate_test_pattern(output_file=clip2, duration=1.5, resolution="640x360", fps=24, color="yellow")

    # 2. Build Timeline
    tl = Timeline(
        project_id="proj_edit_01",
        resolution="640x360",
        fps=24,
        video_clips=[
            TimelineClip(track_type=TimelineTrackType.VIDEO, file_path=clip1, duration=1.5),
            TimelineClip(track_type=TimelineTrackType.VIDEO, file_path=clip2, duration=1.5)
        ]
    )

    # 3. Render Master Video
    editor = EditingStudio(storage_root=temp_workspace, tool_engine=engine)
    master_path = os.path.join(temp_workspace, "master.mp4")
    res_render = editor.render_timeline(tl, output_file_path=master_path)

    assert res_render.success is True
    assert os.path.exists(master_path)
    assert os.path.getsize(master_path) > 0

    # 4. Review Master Video
    reviewer = ReviewEngine(ffprobe_adapter=ffprobe)
    report = reviewer.review_master_video(master_path, expected_min_duration=2.5, expected_resolution="640x360")

    assert report.overall_status in (ConsistencyReviewStatus.PASS, ConsistencyReviewStatus.WARNING)
    assert report.score >= 0.8
    assert report.media_summary is not None
