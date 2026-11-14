import logging
import os
import time
from typing import Any, Dict, Optional
import httpx

from backend.model_adapters.base import BaseModelAdapter
from backend.model_hub.models import (
    ModelErrorCategory,
    ModelException,
    ModelModality,
    ModelRegistration,
    ModelRequest,
    ModelResponse,
)

logger = logging.getLogger(__name__)


class ImageGenerationAdapter(BaseModelAdapter):
    """
    Adapter for AI Text-to-Image models (e.g. OpenAI DALL-E 3, Gemini Imagen).
    """

    def __init__(
        self,
        registration: Optional[ModelRegistration] = None,
        api_key: Optional[str] = None,
        provider: str = "openai"
    ):
        reg = registration or ModelRegistration(
            model_id=f"{provider}/image-model",
            display_name=f"{provider.capitalize()} Image Generator",
            provider=provider,
            modality=ModelModality.IMAGE,
            capabilities=["text_to_image", "photorealistic", "cinematic"],
            cost_per_unit={"per_image": 0.04},
            priority=1
        )
        super().__init__(reg, api_key=api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY"))
        self.provider = provider

    def health_check(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: ModelRequest) -> ModelResponse:
        start_time = time.perf_counter()

        if not self.api_key:
            raise ModelException(
                message="No API Key configured for Image Generation.",
                category=ModelErrorCategory.AUTH_FAILED,
                model_id=self.registration.model_id
            )

        if self.provider == "openai":
            return self._generate_openai(request, start_time)
        elif self.provider == "gemini":
            return self._generate_gemini(request, start_time)
        else:
            raise ModelException(
                message=f"Unsupported image provider: {self.provider}",
                category=ModelErrorCategory.INVALID_REQUEST,
                model_id=self.registration.model_id
            )

    def _generate_openai(self, request: ModelRequest, start_time: float) -> ModelResponse:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "dall-e-3",
            "prompt": f"Cinematic film still, 35mm photography, movie lighting: {request.prompt}",
            "n": 1,
            "size": "1792x1024",
            "quality": "standard"
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, headers=headers, json=payload)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if res.status_code == 200:
                    data = res.json()
                    image_url = data["data"][0]["url"]
                    return ModelResponse(
                        success=True,
                        task_id=request.task_id,
                        model_id=self.registration.model_id,
                        provider=self.registration.provider,
                        modality=ModelModality.IMAGE,
                        media_urls=[image_url],
                        cost_estimated=0.04,
                        execution_time_ms=elapsed_ms
                    )
                elif res.status_code == 429:
                    raise ModelException("OpenAI Image Quota or Rate Limit Exceeded", category=ModelErrorCategory.QUOTA_EXCEEDED, model_id=self.registration.model_id)
                else:
                    raise ModelException(f"OpenAI Error: {res.text}", category=ModelErrorCategory.UNKNOWN, model_id=self.registration.model_id)

        except ModelException:
            raise
        except Exception as e:
            raise ModelException(str(e), category=ModelErrorCategory.UNKNOWN, model_id=self.registration.model_id)

    def _generate_gemini(self, request: ModelRequest, start_time: float) -> ModelResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [{"prompt": request.prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, headers=headers, json=payload)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if res.status_code == 200:
                    data = res.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        b64 = predictions[0]["bytesBase64Encoded"]
                        return ModelResponse(
                            success=True,
                            task_id=request.task_id,
                            model_id=self.registration.model_id,
                            provider="gemini",
                            modality=ModelModality.IMAGE,
                            content=b64,
                            cost_estimated=0.03,
                            execution_time_ms=elapsed_ms
                        )
                raise ModelException(f"Gemini Imagen Error: {res.text}", category=ModelErrorCategory.UNKNOWN, model_id=self.registration.model_id)
        except ModelException:
            raise
        except Exception as e:
            raise ModelException(str(e), category=ModelErrorCategory.UNKNOWN, model_id=self.registration.model_id)
