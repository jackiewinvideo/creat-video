from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from backend.model_hub.models import (
    ModelRegistration,
    ModelRequest,
    ModelResponse,
    ModelException,
    ModelErrorCategory,
)


class BaseModelAdapter(ABC):
    """
    Abstract Base Class for all AI Model Adapters.
    Encapsulates provider-specific HTTP calls, token formatting, and error mapping.
    """

    def __init__(self, registration: ModelRegistration, api_key: Optional[str] = None):
        self.registration = registration
        self.api_key = api_key

    def get_registration(self) -> ModelRegistration:
        return self.registration

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity and key validity."""
        pass

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        """Execute the generation request using the underlying AI provider."""
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in USD based on model registration pricing."""
        pricing = self.registration.cost_per_unit
        input_rate = pricing.get("input_1k_tokens", 0.0) / 1000.0
        output_rate = pricing.get("output_1k_tokens", 0.0) / 1000.0
        return round(prompt_tokens * input_rate + completion_tokens * output_rate, 6)
