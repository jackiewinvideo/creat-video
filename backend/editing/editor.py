import logging
import os
from pathlib import Path
from typing import Optional

from backend.models.timeline import Timeline
from backend.tool_adapters.ffmpeg_adapter import FFmpegAdapter
from backend.tool_adapters.ffprobe_adapter import FFprobeAdapter
from backend.tool_engine.engine import ToolExecutionEngine
from backend.tool_engine.models import ToolExecutionRequest, ToolExecutionResult
from backend.tool_engine.security import ToolSecurityManager

logger = logging.getLogger(__name__)


class EditingStudio:
    """
    Automated timeline editor. Converts Timeline JSON into automated FFmpeg rendering
    for multi-track video, audio, music mixing, and final master video generation.
    """

    def __init__(
        self,
        storage_root: Optional[str] = None,
        tool_engine: Optional[ToolExecutionEngine] = None
    ):
        self.storage_root = Path(storage_root or "./storage").resolve()
        self.tool_engine = tool_engine or ToolExecutionEngine()

    def render_timeline(
        self,
        timeline: Timeline,
        output_file_path: Optional[str] = None
    ) -> ToolExecutionResult:
        """
        Executes multi-track timeline assembly via FFmpeg.
        """
        if not timeline.video_clips:
            return ToolExecutionResult(
                success=False,
                tool_id="ffmpeg",
                action="render_timeline",
                error_message="Timeline has no video clips."
            )

        if not output_file_path:
            master_dir = self.storage_root / "projects" / timeline.project_id / "master"
            master_dir.mkdir(parents=True, exist_ok=True)
            output_file_path = str(master_dir / f"master_{timeline.timeline_id}.mp4")

        # Step 1: Sequential video concatenation
        video_paths = [clip.file_path for clip in timeline.video_clips]

        # Use ToolExecutionEngine to run concatenation
        req = ToolExecutionRequest(
            task_id=f"render_{timeline.timeline_id}",
            tool_id="ffmpeg",
            action="concat_videos",
            output_path=output_file_path,
            params={
                "input_files": video_paths,
                "reencode": True
            }
        )

        result = self.tool_engine.execute(req)
        if result.success and os.path.exists(output_file_path):
            result.output_files = [output_file_path]
            logger.info(f"Rendered master video successfully: {output_file_path}")
        return result
