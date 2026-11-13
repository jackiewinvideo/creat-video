import os
import shutil
import tempfile
import pytest
from pathlib import Path

from backend.tool_engine.models import (
    ToolExecutionRequest,
    ToolStatus,
)
from backend.tool_engine.security import ToolSecurityManager, ToolSecurityException
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="ai_film_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_security_manager_path_validation(temp_workspace):
    sec = ToolSecurityManager(allowed_directories=[temp_workspace])

    valid_path = os.path.join(temp_workspace, "output.mp4")
    assert sec.validate_file_path(valid_path) == Path(valid_path).resolve()

    # Outside path should raise ToolSecurityException
    outside_path = os.path.abspath("/windows/system32/cmd.exe") if os.name == "nt" else "/etc/passwd"
    with pytest.raises(ToolSecurityException):
        sec.validate_file_path(outside_path)


def test_security_manager_cli_injection():
    sec = ToolSecurityManager()
    with pytest.raises(ToolSecurityException):
        sec.validate_cli_arguments(["ffmpeg", "-i", "input.mp4; rm -rf /"])


def test_ffmpeg_and_ffprobe_live_execution(temp_workspace):
    sec = ToolSecurityManager(allowed_directories=[temp_workspace, os.getcwd()])
    registry = ToolRegistry()

    ffmpeg_adapter = FFmpegAdapter(security_manager=sec)
    ffprobe_adapter = FFprobeAdapter(security_manager=sec)

    registry.register_adapter(ffmpeg_adapter)
    registry.register_adapter(ffprobe_adapter)

    # 1. Health check
    statuses = registry.check_all_tools()
    assert statuses["ffmpeg"] == ToolStatus.READY
    assert statuses["ffprobe"] == ToolStatus.READY

    engine = ToolExecutionEngine(registry=registry, security_manager=sec)

    # 2. Generate a 2-second test video (blue)
    vid1_path = os.path.join(temp_workspace, "video1.mp4")
    req_gen1 = ToolExecutionRequest(
        task_id="task_test_01",
        tool_id="ffmpeg",
        action="generate_test_pattern",
        output_path=vid1_path,
        params={"duration": 2.0, "color": "blue", "resolution": "640x360", "fps": 24}
    )
    res_gen1 = engine.execute(req_gen1)
    assert res_gen1.success is True
    assert os.path.exists(vid1_path)
    assert os.path.getsize(vid1_path) > 0

    # 3. Generate a 2-second test video (red)
    vid2_path = os.path.join(temp_workspace, "video2.mp4")
    req_gen2 = ToolExecutionRequest(
        task_id="task_test_02",
        tool_id="ffmpeg",
        action="generate_test_pattern",
        output_path=vid2_path,
        params={"duration": 2.0, "color": "red", "resolution": "640x360", "fps": 24}
    )
    res_gen2 = engine.execute(req_gen2)
    assert res_gen2.success is True

    # 4. Probe video1 with ffprobe
    req_probe = ToolExecutionRequest(
        task_id="task_test_03",
        tool_id="ffprobe",
        action="probe",
        params={"file_path": vid1_path}
    )
    res_probe = engine.execute(req_probe)
    assert res_probe.success is True
    video_info = res_probe.metadata.get("video")
    assert video_info is not None
    assert video_info["width"] == 640
    assert video_info["height"] == 360
    assert video_info["fps"] == 24.0

    # 5. Concatenate video1 + video2 into concat.mp4
    concat_path = os.path.join(temp_workspace, "concat.mp4")
    req_concat = ToolExecutionRequest(
        task_id="task_test_04",
        tool_id="ffmpeg",
        action="concat_videos",
        output_path=concat_path,
        params={"input_files": [vid1_path, vid2_path], "reencode": True}
    )
    res_concat = engine.execute(req_concat)
    assert res_concat.success is True
    assert os.path.exists(concat_path)
    assert os.path.getsize(concat_path) > 0

    # 6. Probe concatenated video, verify total duration is ~4.0 seconds
    req_probe_concat = ToolExecutionRequest(
        task_id="task_test_05",
        tool_id="ffprobe",
        action="probe",
        params={"file_path": concat_path}
    )
    res_probe_concat = engine.execute(req_probe_concat)
    assert res_probe_concat.success is True
    concat_video_info = res_probe_concat.metadata.get("video")
    assert concat_video_info is not None
    assert abs(concat_video_info["duration"] - 4.0) < 0.5

    # 7. Extract frame snapshot
    frame_path = os.path.join(temp_workspace, "frame.jpg")
    req_frame = ToolExecutionRequest(
        task_id="task_test_06",
        tool_id="ffmpeg",
        action="extract_frame",
        output_path=frame_path,
        params={"video_file": concat_path, "timestamp": 1.0}
    )
    res_frame = engine.execute(req_frame)
    assert res_frame.success is True
    assert os.path.exists(frame_path)
    assert os.path.getsize(frame_path) > 0

    # 8. Check execution logs
    assert len(engine.execution_logs) >= 6
