import logging
from typing import Dict, List, Optional
from backend.model_adapters.base import BaseModelAdapter
from backend.model_hub.models import ModelRegistration, ModelModality

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for all AI Models in AI Film Studio.
    Provides model discovery, modality filtering, priority ordering, and fallback configurations.
    """

    def __init__(self):
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._stage_fallbacks: Dict[str, List[str]] = {}

    def register_adapter(self, adapter: BaseModelAdapter) -> None:
        model_id = adapter.registration.model_id
        self._adapters[model_id] = adapter
        logger.info(f"Registered model: {model_id} ({adapter.registration.display_name})")

    def unregister(self, model_id: str) -> None:
        self._adapters.pop(model_id, None)

    def get_adapter(self, model_id: str) -> Optional[BaseModelAdapter]:
        return self._adapters.get(model_id)

    def get_model(self, model_id: str) -> Optional[ModelRegistration]:
        adapter = self._adapters.get(model_id)
        return adapter.registration if adapter else None

    def list_models(
        self,
        modality: Optional[ModelModality] = None,
        enabled_only: bool = True
    ) -> List[ModelRegistration]:
        models = [adapter.registration for adapter in self._adapters.values()]
        if enabled_only:
            models = [m for m in models if m.is_enabled]
        if modality:
            models = [m for m in models if m.modality == modality]

        # Sort by priority (1 is highest)
        return sorted(models, key=lambda m: m.priority)

    def set_stage_fallback_chain(self, stage_name: str, model_ids: List[str]) -> None:
        """Configure fallback hierarchy for a specific production stage."""
        self._stage_fallbacks[stage_name] = model_ids

    def get_stage_fallback_chain(self, stage_name: str) -> List[str]:
        return self._stage_fallbacks.get(stage_name, [])
