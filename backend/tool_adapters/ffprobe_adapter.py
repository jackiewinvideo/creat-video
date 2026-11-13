import json
from typing import Any, Dict, Optional
from backend.tool_adapters.cli_adapter import CLIToolAdapter
from backend.tool_engine.models import (
    ToolRegistration,
    ToolType,
    ExecutionLocation,
    ToolExecutionRequest,
    ToolExecutionResult,
)
from backend.tool_engine.security import ToolSecurityManager


class FFprobeAdapter(CLIToolAdapter):
    """
    Adapter for FFprobe: extracts structured media metadata (codecs, resolution, fps, duration).
    """

    def __init__(
        self,
        security_manager: Optional[ToolSecurityManager] = None,
        custom_executable_path: Optional[str] = None
    ):
        registration = ToolRegistration(
            tool_id="ffprobe",
            tool_name="FFprobe Media Inspector",
            tool_type=ToolType.CLI,
            version="auto",
            provider="FFmpeg Project",
            capabilities=[
                "media_probe",
                "format_detection",
                "stream_analysis",
                "codec_check",
                "resolution_detection",
                "duration_detection"
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to media file"}
                },
                "required": ["file_path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "format": {"type": "object"},
                    "streams": {"type": "array"},
                    "video_info": {"type": "object"},
                    "audio_info": {"type": "object"}
                }
            },
            timeout=30,
            license="LGPL/GPL",
            execution_location=ExecutionLocation.LOCAL,
            description="Analyzes multimedia streams and formats to produce machine-readable JSON metadata."
        )
        super().__init__(registration, security_manager, custom_executable_path)

    def probe(self, file_path: str) -> Dict[str, Any]:
        """
        Runs ffprobe and returns parsed metadata.
        """
        validated_path = self.security_manager.validate_file_path(file_path, must_exist=True)

        args = [
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            str(validated_path)
        ]

        result = self.run_command(args)
        if not result.success:
            raise RuntimeError(f"FFprobe failed: {result.stderr or result.error_message}")

        try:
            raw_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse FFprobe JSON output: {e}\nRaw output: {result.stdout}")

        # Extract structured summary
        summary = {
            "format": raw_data.get("format", {}),
            "streams": raw_data.get("streams", []),
            "video": None,
            "audio": None
        }

        for stream in summary["streams"]:
            codec_type = stream.get("codec_type")
            if codec_type == "video" and summary["video"] is None:
                # Calculate FPS
                r_frame_rate = stream.get("r_frame_rate", "0/0")
                fps = 0.0
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    if float(den) > 0:
                        fps = round(float(num) / float(den), 3)

                summary["video"] = {
                    "codec_name": stream.get("codec_name"),
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "fps": fps,
                    "duration": float(stream.get("duration", summary["format"].get("duration", 0))),
                    "bit_rate": stream.get("bit_rate"),
                    "pix_fmt": stream.get("pix_fmt")
                }
            elif codec_type == "audio" and summary["audio"] is None:
                summary["audio"] = {
                    "codec_name": stream.get("codec_name"),
                    "sample_rate": stream.get("sample_rate"),
                    "channels": stream.get("channels"),
                    "bit_rate": stream.get("bit_rate"),
                    "duration": float(stream.get("duration", summary["format"].get("duration", 0)))
                }

        return summary

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        if request.action == "probe":
            file_path = request.params.get("file_path")
            if not file_path:
                return ToolExecutionResult(
                    success=False,
                    tool_id=self.registration.tool_id,
                    action=request.action,
                    error_message="Missing 'file_path' in parameters."
                )

            try:
                metadata = self.probe(file_path)
                return ToolExecutionResult(
                    success=True,
                    tool_id=self.registration.tool_id,
                    action=request.action,
                    exit_code=0,
                    metadata=metadata
                )
            except Exception as e:
                return ToolExecutionResult(
                    success=False,
                    tool_id=self.registration.tool_id,
                    action=request.action,
                    exit_code=-1,
                    error_message=str(e)
                )

        return ToolExecutionResult(
            success=False,
            tool_id=self.registration.tool_id,
            action=request.action,
            error_message=f"Unsupported action '{request.action}' for ffprobe."
        )
