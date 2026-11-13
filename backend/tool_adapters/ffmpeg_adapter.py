import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.tool_adapters.cli_adapter import CLIToolAdapter
from backend.tool_engine.models import (
    ToolRegistration,
    ToolType,
    ExecutionLocation,
    ToolExecutionRequest,
    ToolExecutionResult,
)
from backend.tool_engine.security import ToolSecurityManager


class FFmpegAdapter(CLIToolAdapter):
    """
    Adapter for FFmpeg: performs automated video editing, concatenation,
    rescaling, audio mixing, trimming, and frame extraction.
    """

    def __init__(
        self,
        security_manager: Optional[ToolSecurityManager] = None,
        custom_executable_path: Optional[str] = None
    ):
        registration = ToolRegistration(
            tool_id="ffmpeg",
            tool_name="FFmpeg Media Processing Engine",
            tool_type=ToolType.CLI,
            version="auto",
            provider="FFmpeg Project",
            capabilities=[
                "video_concat",
                "video_trim",
                "audio_mix",
                "extract_frame",
                "convert_format",
                "scale_video",
                "generate_test_pattern"
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "inputs": {"type": "array", "items": {"type": "string"}},
                    "output": {"type": "string"}
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "output_file": {"type": "string"}
                }
            },
            timeout=1800,  # 30 minutes default for video processing
            license="LGPL/GPL",
            execution_location=ExecutionLocation.LOCAL,
            description="High-performance multimedia transcoding and automated editing engine."
        )
        super().__init__(registration, security_manager, custom_executable_path)

    def generate_test_pattern(
        self,
        output_file: str,
        duration: float = 3.0,
        resolution: str = "1280x720",
        fps: int = 30,
        color: str = "blue"
    ) -> ToolExecutionResult:
        """
        Generates a synthetic color video with silence/tone for pipeline verification.
        """
        validated_output = self.security_manager.validate_file_path(output_file)
        os.makedirs(validated_output.parent, exist_ok=True)

        args = [
            "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={resolution}:r={fps}:d={duration}",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-t", str(duration),
            str(validated_output)
        ]

        result = self.run_command(args)
        if result.success and validated_output.exists():
            result.output_files = [str(validated_output)]
        return result

    def extract_frame(
        self,
        video_file: str,
        output_image: str,
        timestamp: float = 0.0
    ) -> ToolExecutionResult:
        """Extract a single snapshot frame at the given timestamp."""
        validated_input = self.security_manager.validate_file_path(video_file, must_exist=True)
        validated_output = self.security_manager.validate_file_path(output_image)
        os.makedirs(validated_output.parent, exist_ok=True)

        args = [
            "-y",
            "-ss", str(timestamp),
            "-i", str(validated_input),
            "-vframes", "1",
            "-q:v", "2",
            str(validated_output)
        ]

        result = self.run_command(args)
        if result.success and validated_output.exists():
            result.output_files = [str(validated_output)]
        return result

    def trim(
        self,
        input_file: str,
        output_file: str,
        start_time: float = 0.0,
        duration: Optional[float] = None
    ) -> ToolExecutionResult:
        """Trim/cut a section of a video."""
        validated_input = self.security_manager.validate_file_path(input_file, must_exist=True)
        validated_output = self.security_manager.validate_file_path(output_file)
        os.makedirs(validated_output.parent, exist_ok=True)

        args = ["-y", "-ss", str(start_time), "-i", str(validated_input)]
        if duration is not None:
            args.extend(["-t", str(duration)])
        args.extend(["-c", "copy", str(validated_output)])

        result = self.run_command(args)
        if result.success and validated_output.exists():
            result.output_files = [str(validated_output)]
        return result

    def concat_videos(
        self,
        input_files: List[str],
        output_file: str,
        reencode: bool = True
    ) -> ToolExecutionResult:
        """
        Concatenate multiple video files sequentially.
        If reencode is True, normalizes resolution and frame rate to avoid sync issues.
        """
        if not input_files:
            return ToolExecutionResult(
                success=False,
                tool_id=self.registration.tool_id,
                action="concat_videos",
                error_message="No input files provided for concatenation."
            )

        validated_inputs = [
            self.security_manager.validate_file_path(f, must_exist=True)
            for f in input_files
        ]
        validated_output = self.security_manager.validate_file_path(output_file)
        os.makedirs(validated_output.parent, exist_ok=True)

        if not reencode:
            # Demuxer concat
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as concat_list:
                for path in validated_inputs:
                    concat_list.write(f"file '{path.as_posix()}'\n")
                list_file_path = concat_list.name

            try:
                args = [
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file_path,
                    "-c", "copy",
                    str(validated_output)
                ]
                result = self.run_command(args)
            finally:
                if os.path.exists(list_file_path):
                    os.remove(list_file_path)
        else:
            # Complex filter concat (robust against different codecs/resolutions)
            args = ["-y"]
            for path in validated_inputs:
                args.extend(["-i", str(path)])

            n = len(validated_inputs)
            filter_spec = "".join([f"[{i}:v:0][{i}:a:0]" for i in range(n)]) + f"concat=n={n}:v=1:a=1[outv][outa]"

            args.extend([
                "-filter_complex", filter_spec,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                str(validated_output)
            ])
            result = self.run_command(args)

        if result.success and validated_output.exists():
            result.output_files = [str(validated_output)]
        return result

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        action = request.action
        params = request.params

        if action == "generate_test_pattern":
            return self.generate_test_pattern(
                output_file=request.output_path or params.get("output_file", "test.mp4"),
                duration=float(params.get("duration", 3.0)),
                resolution=params.get("resolution", "1280x720"),
                fps=int(params.get("fps", 30)),
                color=params.get("color", "blue")
            )
        elif action == "concat_videos":
            return self.concat_videos(
                input_files=params.get("input_files", []),
                output_file=request.output_path or params.get("output_file", "concat.mp4"),
                reencode=bool(params.get("reencode", True))
            )
        elif action == "extract_frame":
            return self.extract_frame(
                video_file=params.get("video_file", ""),
                output_image=request.output_path or params.get("output_image", "frame.jpg"),
                timestamp=float(params.get("timestamp", 0.0))
            )
        elif action == "trim":
            return self.trim(
                input_file=params.get("input_file", ""),
                output_file=request.output_path or params.get("output_file", "trimmed.mp4"),
                start_time=float(params.get("start_time", 0.0)),
                duration=params.get("duration")
            )
        elif action == "custom_cli":
            args = params.get("args", [])
            return self.run_command(args, timeout=request.timeout)

        return ToolExecutionResult(
            success=False,
            tool_id=self.registration.tool_id,
            action=action,
            error_message=f"Unsupported FFmpeg action '{action}'."
        )
