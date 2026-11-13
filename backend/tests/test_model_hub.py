import pytest
from backend.model_hub.models import (
    ModelRegistration,
    ModelModality,
    ModelRequest,
    ModelErrorCategory,
)
from backend.model_hub.registry import ModelRegistry
from backend.model_hub.router import ModelRouter
from backend.model_adapters.mock_adapter import MockModelAdapter


def test_model_registry_registration_and_priority():
    registry = ModelRegistry()

    m1 = ModelRegistration(
        model_id="test/model-low-priority",
        display_name="Low Priority Model",
        provider="test",
        modality=ModelModality.TEXT,
        priority=10
    )
    m2 = ModelRegistration(
        model_id="test/model-high-priority",
        display_name="High Priority Model",
        provider="test",
        modality=ModelModality.TEXT,
        priority=1
    )

    registry.register_adapter(MockModelAdapter(registration=m1))
    registry.register_adapter(MockModelAdapter(registration=m2))

    models = registry.list_models(modality=ModelModality.TEXT)
    assert len(models) == 2
    assert models[0].model_id == "test/model-high-priority"
    assert models[1].model_id == "test/model-low-priority"


def test_model_router_successful_generation():
    registry = ModelRegistry()
    adapter = MockModelAdapter(response_text="Scene 1: Interior of cyberpunk spaceship.")
    registry.register_adapter(adapter)

    router = ModelRouter(registry=registry)
    req = ModelRequest(
        task_id="task_screenplay_01",
        modality=ModelModality.TEXT,
        prompt="Write opening scene for a scifi movie."
    )

    res = router.execute(req)
    assert res.success is True
    assert "cyberpunk spaceship" in res.content
    assert res.cost_estimated >= 0.0
    assert len(res.switch_history) == 0


def test_model_router_fallback_on_quota_exceeded():
    registry = ModelRegistry()

    # Primary model throws QUOTA_EXCEEDED
    m_primary = ModelRegistration(
        model_id="provider/primary-model",
        display_name="Primary Flagship Model",
        provider="primary",
        modality=ModelModality.TEXT,
        priority=1
    )
    primary_adapter = MockModelAdapter(
        registration=m_primary,
        simulate_error=ModelErrorCategory.QUOTA_EXCEEDED
    )

    # Fallback model succeeds
    m_fallback = ModelRegistration(
        model_id="provider/fallback-model",
        display_name="Backup Open Model",
        provider="backup",
        modality=ModelModality.TEXT,
        priority=2
    )
    fallback_adapter = MockModelAdapter(
        registration=m_fallback,
        response_text="Fallback script generated successfully."
    )

    registry.register_adapter(primary_adapter)
    registry.register_adapter(fallback_adapter)

    router = ModelRouter(registry=registry)
    req = ModelRequest(
        task_id="task_quota_switch_01",
        modality=ModelModality.TEXT,
        prompt="Generate screenplay draft",
        preferred_model_id="provider/primary-model",
        fallback_model_ids=["provider/fallback-model"]
    )

    res = router.execute(req)
    # Verification: should succeed with fallback model
    assert res.success is True
    assert res.model_id == "provider/fallback-model"
    assert "Fallback script" in res.content

    # Verification: switch history recorded
    assert len(res.switch_history) == 1
    assert res.switch_history[0].from_model_id == "provider/primary-model"
    assert res.switch_history[0].to_model_id == "provider/fallback-model"
    assert res.switch_history[0].error_category == ModelErrorCategory.QUOTA_EXCEEDED


def test_model_router_all_models_fail():
    registry = ModelRegistry()

    m_fail = ModelRegistration(
        model_id="provider/fail-1",
        display_name="Failing Model",
        provider="fail",
        modality=ModelModality.TEXT
    )
    registry.register_adapter(
        MockModelAdapter(registration=m_fail, simulate_error=ModelErrorCategory.SERVICE_UNAVAILABLE)
    )

    router = ModelRouter(registry=registry)
    req = ModelRequest(
        task_id="task_fail_01",
        modality=ModelModality.TEXT,
        prompt="Test fail",
        preferred_model_id="provider/fail-1"
    )

    res = router.execute(req)
    assert res.success is False
    assert "All models in fallback chain failed" in res.error_message
