import os
import shutil
import subprocess
import time
from typing import List, Optional
from backend.tool_adapters.base import BaseToolAdapter
from backend.tool_engine.models import ToolRegistration, ToolExecutionRequest, ToolExecutionResult, ToolStatus
from backend.tool_engine.security import ToolSecurityManager, ToolSecurityException


class CLIToolAdapter(BaseToolAdapter):
    """
    Adapter for command-line tools (e.g. FFmpeg, FFprobe, Blender, Whisper CLI).
    Never uses shell=True; uses argument vectors for security.
    """

    def __init__(
        self,
        registration: ToolRegistration,
        security_manager: Optional[ToolSecurityManager] = None,
        custom_executable_path: Optional[str] = None
    ):
        super().__init__(registration)
        self.security_manager = security_manager or ToolSecurityManager()
        self.executable_path = custom_executable_path or registration.executable_path or shutil.which(registration.tool_id)

    def installation_check(self) -> bool:
        if not self.executable_path:
            self.executable_path = shutil.which(self.registration.tool_id)

        if self.executable_path and os.path.exists(self.executable_path):
            self.registration.executable_path = self.executable_path
            self.registration.status = ToolStatus.READY
            return True
        
        # Check if findable via PATH
        found = shutil.which(self.registration.tool_id)
        if found:
            self.executable_path = found
            self.registration.executable_path = found
            self.registration.status = ToolStatus.READY
            return True

        self.registration.status = ToolStatus.NOT_INSTALLED
        return False

    def health_check(self) -> bool:
        if not self.installation_check():
            return False
        try:
            # Default health check runs `--version` or `-version`
            result = subprocess.run(
                [self.executable_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False
            )
            is_healthy = result.returncode == 0
            self.registration.status = ToolStatus.READY if is_healthy else ToolStatus.UNHEALTHY
            return is_healthy
        except Exception:
            self.registration.status = ToolStatus.UNHEALTHY
            return False

    def run_command(
        self,
        args: List[str],
        timeout: Optional[int] = None
    ) -> ToolExecutionResult:
        if not self.executable_path:
            return ToolExecutionResult(
                success=False,
                tool_id=self.registration.tool_id,
                action="cli_execution",
                exit_code=-1,
                error_message=f"Tool '{self.registration.tool_id}' is not installed or executable not found."
            )

        cmd = [self.executable_path] + args
        self.security_manager.validate_cli_arguments(cmd)
        effective_timeout = self.security_manager.validate_timeout(timeout, self.registration.timeout)

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                shell=False
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            success = proc.returncode == 0
            return ToolExecutionResult(
                success=success,
                tool_id=self.registration.tool_id,
                action="cli_execution",
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                execution_time_ms=elapsed_ms,
                error_message=None if success else f"Process exited with code {proc.returncode}"
            )
        except subprocess.TimeoutExpired as te:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                tool_id=self.registration.tool_id,
                action="cli_execution",
                exit_code=-2,
                stdout=te.stdout or "" if isinstance(te.stdout, str) else "",
                stderr=te.stderr or "" if isinstance(te.stderr, str) else "",
                execution_time_ms=elapsed_ms,
                error_message=f"Command timed out after {effective_timeout} seconds."
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                tool_id=self.registration.tool_id,
                action="cli_execution",
                exit_code=-3,
                execution_time_ms=elapsed_ms,
                error_message=str(e)
            )

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Subclasses override this to translate high-level actions into CLI arguments."""
        raise NotImplementedError("Subclasses must implement action-specific execution.")
