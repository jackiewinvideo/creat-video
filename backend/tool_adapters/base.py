from abc import ABC, abstractmethod
from typing import Optional
from backend.tool_engine.models import ToolRegistration, ToolExecutionRequest, ToolExecutionResult


class BaseToolAdapter(ABC):
    """
    Abstract Base Class for all Tool Adapters (CLI, SDK, API, Service).
    Every tool must implement these methods.
    """

    def __init__(self, registration: ToolRegistration):
        self.registration = registration

    @abstractmethod
    def installation_check(self) -> bool:
        """Verify tool is installed and locate binary/module."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Run a lightweight command or ping to ensure responsiveness."""
        pass

    @abstractmethod
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute a specific action using this tool."""
        pass

    def get_registration(self) -> ToolRegistration:
        return self.registration
