import logging
import os
import time
from typing import Dict, List, Optional
from backend.tool_engine.models import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolStatus,
)
from backend.tool_engine.registry import ToolRegistry
from backend.tool_engine.security import ToolSecurityManager, ToolSecurityException

logger = logging.getLogger(__name__)


class ToolExecutionEngine:
    """
    Central execution engine that manages and executes external tools.
    Implements the 10-step execution pipeline specified in Section 8:
    1. Receive task
    2. Query tool registration
    3. Check installation & health
    4. Validate params & paths
    5. Context setup
    6. Execute & monitor
    7. Capture stdout/stderr
    8. Verify output files
    9. Log execution
    10. Return result
    """

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        security_manager: Optional[ToolSecurityManager] = None
    ):
        self.registry = registry or ToolRegistry()
        self.security_manager = security_manager or ToolSecurityManager()
        self.execution_logs: List[Dict] = []

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        logger.info(f"Received execution request [Task: {request.task_id}, Tool: {request.tool_id}, Action: {request.action}]")

        # Step 2: Query tool registry
        adapter = self.registry.get_adapter(request.tool_id)
        if not adapter:
            return ToolExecutionResult(
                success=False,
                tool_id=request.tool_id,
                action=request.action,
                error_message=f"Tool '{request.tool_id}' is not registered."
            )

        reg = adapter.registration

        # Step 3: Check installation and health
        if reg.status not in (ToolStatus.READY, ToolStatus.BUSY):
            if not adapter.health_check():
                return ToolExecutionResult(
                    success=False,
                    tool_id=request.tool_id,
                    action=request.action,
                    error_message=f"Tool '{request.tool_id}' is unavailable (status: {reg.status.value})."
                )

        # Step 4: Validate parameters & output path
        try:
            if request.output_path:
                self.security_manager.validate_file_path(request.output_path)
        except ToolSecurityException as se:
            return ToolExecutionResult(
                success=False,
                tool_id=request.tool_id,
                action=request.action,
                error_message=f"Security violation: {se}"
            )

        # Step 5 & 6: Execute with retries if configured
        retries = reg.retry_policy.max_retries
        backoff = reg.retry_policy.backoff_seconds
        attempt = 0

        result = None
        while attempt <= retries:
            attempt += 1
            result = adapter.execute(request)
            if result.success:
                break
            if attempt <= retries and (not reg.retry_policy.retryable_exit_codes or result.exit_code in reg.retry_policy.retryable_exit_codes):
                logger.warning(f"Tool {request.tool_id} failed (attempt {attempt}/{retries+1}), retrying in {backoff}s...")
                time.sleep(backoff)

        # Step 8: Verify output files
        if result.success and result.output_files:
            verified_files = []
            for out_file in result.output_files:
                if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                    verified_files.append(out_file)
                else:
                    result.success = False
                    result.error_message = f"Expected output file '{out_file}' was missing or empty."
                    break
            result.output_files = verified_files

        # Step 9: Store execution log
        log_entry = {
            "task_id": request.task_id,
            "tool_id": request.tool_id,
            "action": request.action,
            "success": result.success,
            "exit_code": result.exit_code,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": time.time(),
            "error_message": result.error_message
        }
        self.execution_logs.append(log_entry)

        return result
