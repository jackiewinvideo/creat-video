import time
from typing import Optional
from backend.model_adapters.base import BaseModelAdapter
from backend.model_hub.models import (
    ModelRegistration,
    ModelModality,
    ModelRequest,
    ModelResponse,
    ModelException,
    ModelErrorCategory,
)


class MockModelAdapter(BaseModelAdapter):
    """
    Simulated adapter used for deterministic testing, offline environments,
    and verifying fallback and quota error handling.
    """

    def __init__(
        self,
        registration: Optional[ModelRegistration] = None,
        simulate_error: Optional[ModelErrorCategory] = None,
        response_text: str = "Simulated screenplay and storyboard output."
    ):
        reg = registration or ModelRegistration(
            model_id="mock/text-standard",
            display_name="Mock Text Model",
            provider="mock",
            modality=ModelModality.TEXT,
            capabilities=["storyboard", "script", "prompt_generation"],
            cost_per_unit={"input_1k_tokens": 0.001, "output_1k_tokens": 0.002},
            context_window=32768,
            priority=10
        )
        super().__init__(reg, api_key="mock-key")
        self.simulate_error = simulate_error
        self.response_text = response_text
        self.call_count = 0

    def health_check(self) -> bool:
        return self.simulate_error != ModelErrorCategory.SERVICE_UNAVAILABLE

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.call_count += 1
        start_time = time.perf_counter()

        if self.simulate_error == ModelErrorCategory.QUOTA_EXCEEDED:
            raise ModelException(
                message=f"Insufficient quota or credit balance on {self.registration.model_id}",
                category=ModelErrorCategory.QUOTA_EXCEEDED,
                model_id=self.registration.model_id,
                retryable=False,
                status_code=429
            )
        elif self.simulate_error == ModelErrorCategory.RATE_LIMIT:
            raise ModelException(
                message=f"Rate limit exceeded on {self.registration.model_id}",
                category=ModelErrorCategory.RATE_LIMIT,
                model_id=self.registration.model_id,
                retryable=True,
                status_code=429
            )
        elif self.simulate_error == ModelErrorCategory.SERVICE_UNAVAILABLE:
            raise ModelException(
                message=f"Service {self.registration.model_id} currently unavailable",
                category=ModelErrorCategory.SERVICE_UNAVAILABLE,
                model_id=self.registration.model_id,
                retryable=True,
                status_code=503
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        prompt_tokens = len(request.prompt.split())
        completion_tokens = len(self.response_text.split())

        cost = self.estimate_cost(prompt_tokens, completion_tokens)

        return ModelResponse(
            success=True,
            task_id=request.task_id,
            model_id=self.registration.model_id,
            provider=self.registration.provider,
            modality=self.registration.modality,
            content=self.response_text,
            token_usage={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
            cost_estimated=cost,
            execution_time_ms=elapsed_ms
        )
