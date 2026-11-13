import logging
import time
from typing import List, Optional
from backend.model_hub.models import (
    ModelRequest,
    ModelResponse,
    ModelSwitchLog,
    ModelException,
    ModelErrorCategory,
)
from backend.model_hub.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Intelligent Router for AI Models.
    Coordinates primary model execution, error detection (quota, rate limit, service down),
    and automatic fallback switching as specified in Section 7 of the specification.
    """

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.switch_history: List[ModelSwitchLog] = []

    def execute(self, request: ModelRequest) -> ModelResponse:
        """
        Execute request with automatic fallback chain traversal.
        """
        candidate_model_ids = self._resolve_model_chain(request)
        if not candidate_model_ids:
            return ModelResponse(
                success=False,
                task_id=request.task_id,
                model_id="none",
                provider="none",
                modality=request.modality,
                error_message="No enabled models available for the requested modality."
            )

        switch_logs: List[ModelSwitchLog] = []
        last_error_message: Optional[str] = None

        for idx, model_id in enumerate(candidate_model_ids):
            adapter = self.registry.get_adapter(model_id)
            if not adapter or not adapter.registration.is_enabled:
                continue

            try:
                logger.info(f"Task {request.task_id}: invoking model '{model_id}' (attempt {idx + 1}/{len(candidate_model_ids)})")
                response = adapter.generate(request)

                if response.success:
                    response.switch_history = switch_logs
                    return response

            except ModelException as me:
                logger.warning(
                    f"Model '{model_id}' failed with {me.category.value}: {me.message}"
                )
                last_error_message = me.message

                # Determine if we should fallback to next model
                fallback_categories = (
                    ModelErrorCategory.QUOTA_EXCEEDED,
                    ModelErrorCategory.RATE_LIMIT,
                    ModelErrorCategory.SERVICE_UNAVAILABLE,
                    ModelErrorCategory.TIMEOUT,
                    ModelErrorCategory.AUTH_FAILED
                )

                if me.category in fallback_categories and (idx + 1) < len(candidate_model_ids):
                    next_model_id = candidate_model_ids[idx + 1]
                    switch_log = ModelSwitchLog(
                        from_model_id=model_id,
                        to_model_id=next_model_id,
                        reason=me.message,
                        error_category=me.category,
                        timestamp=time.time()
                    )
                    switch_logs.append(switch_log)
                    self.switch_history.append(switch_log)
                    logger.info(f"Switching from '{model_id}' to fallback '{next_model_id}' due to {me.category.value}.")
                    continue
                else:
                    # Non-fallback error or end of chain
                    break

            except Exception as ex:
                logger.error(f"Unexpected error with model '{model_id}': {ex}")
                last_error_message = str(ex)
                break

        return ModelResponse(
            success=False,
            task_id=request.task_id,
            model_id=candidate_model_ids[0] if candidate_model_ids else "unknown",
            provider="unknown",
            modality=request.modality,
            switch_history=switch_logs,
            error_message=f"All models in fallback chain failed. Last error: {last_error_message}"
        )

    def _resolve_model_chain(self, request: ModelRequest) -> List[str]:
        chain: List[str] = []

        # 1. Explicit preferred model
        if request.preferred_model_id:
            chain.append(request.preferred_model_id)

        # 2. Explicit fallbacks in request
        for fid in request.fallback_model_ids:
            if fid not in chain:
                chain.append(fid)

        # 3. If empty, populate from registry by modality ordered by priority
        if not chain:
            models = self.registry.list_models(modality=request.modality, enabled_only=True)
            chain = [m.model_id for m in models]

        return chain
