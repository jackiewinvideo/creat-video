import time
from typing import Any, Dict, Optional
import httpx
from backend.model_adapters.base import BaseModelAdapter
from backend.model_hub.models import (
    ModelRegistration,
    ModelModality,
    ModelRequest,
    ModelResponse,
    ModelException,
    ModelErrorCategory,
)


class OpenAICompatibleAdapter(BaseModelAdapter):
    """
    Adapter for any provider supporting OpenAI-compatible chat completions
    (OpenAI, OpenRouter, MiniMax, DeepSeek, Ollama, etc.).
    """

    def __init__(
        self,
        registration: ModelRegistration,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1"
    ):
        super().__init__(registration, api_key)
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        if not self.api_key and "localhost" not in self.base_url:
            return False
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                )
                return res.status_code in (200, 401, 403)
        except Exception:
            return False

    def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = time.perf_counter()
        messages = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.append({"role": "user", "content": request.prompt})

        payload: Dict[str, Any] = {
            "model": self.registration.model_id.split("/")[-1],
            "messages": messages,
            "temperature": request.parameters.get("temperature", 0.7),
        }

        if "max_tokens" in request.parameters:
            payload["max_tokens"] = request.parameters["max_tokens"]

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=request.parameters.get("timeout", 60.0)) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    content = choice.get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)

                    cost = self.estimate_cost(prompt_tokens, completion_tokens)

                    return ModelResponse(
                        success=True,
                        task_id=request.task_id,
                        model_id=self.registration.model_id,
                        provider=self.registration.provider,
                        modality=ModelModality.TEXT,
                        content=content,
                        token_usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": usage.get("total_tokens", 0)
                        },
                        cost_estimated=cost,
                        execution_time_ms=elapsed_ms,
                        raw_response=data
                    )

                # Error categorization
                status_code = response.status_code
                error_body = response.text
                if status_code == 401:
                    category = ModelErrorCategory.AUTH_FAILED
                elif status_code == 429:
                    if "quota" in error_body.lower() or "insufficient" in error_body.lower():
                        category = ModelErrorCategory.QUOTA_EXCEEDED
                    else:
                        category = ModelErrorCategory.RATE_LIMIT
                elif status_code in (502, 503, 504):
                    category = ModelErrorCategory.SERVICE_UNAVAILABLE
                else:
                    category = ModelErrorCategory.UNKNOWN

                raise ModelException(
                    message=f"API request failed with HTTP {status_code}: {error_body}",
                    category=category,
                    model_id=self.registration.model_id,
                    retryable=category in (ModelErrorCategory.RATE_LIMIT, ModelErrorCategory.SERVICE_UNAVAILABLE),
                    status_code=status_code
                )

        except httpx.TimeoutException:
            raise ModelException(
                message=f"Request to {self.registration.model_id} timed out.",
                category=ModelErrorCategory.TIMEOUT,
                model_id=self.registration.model_id,
                retryable=True
            )
        except ModelException:
            raise
        except Exception as e:
            raise ModelException(
                message=str(e),
                category=ModelErrorCategory.UNKNOWN,
                model_id=self.registration.model_id,
                retryable=False
            )
