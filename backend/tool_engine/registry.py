import logging
from typing import Dict, List, Optional
from backend.tool_adapters.base import BaseToolAdapter
from backend.tool_engine.models import ToolRegistration, ToolStatus

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for all available tools in AI Film Studio.
    Tracks adapters, capabilities, health, and installation status.
    """

    def __init__(self):
        self._adapters: Dict[str, BaseToolAdapter] = {}

    def register_adapter(self, adapter: BaseToolAdapter) -> None:
        tool_id = adapter.registration.tool_id
        self._adapters[tool_id] = adapter
        logger.info(f"Registered tool adapter: {tool_id} ({adapter.registration.tool_name})")

    def get_adapter(self, tool_id: str) -> Optional[BaseToolAdapter]:
        return self._adapters.get(tool_id)

    def get_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        adapter = self._adapters.get(tool_id)
        return adapter.registration if adapter else None

    def list_tools(self) -> List[ToolRegistration]:
        return [adapter.registration for adapter in self._adapters.values()]

    def check_tool_health(self, tool_id: str) -> bool:
        adapter = self._adapters.get(tool_id)
        if not adapter:
            return False
        return adapter.health_check()

    def check_all_tools(self) -> Dict[str, ToolStatus]:
        """Perform installation and health checks on all registered tools."""
        statuses = {}
        for tool_id, adapter in self._adapters.items():
            is_healthy = adapter.health_check()
            statuses[tool_id] = adapter.registration.status
            logger.info(f"Tool check '{tool_id}': status={adapter.registration.status.value}")
        return statuses
