import os
import shutil
import tempfile
import pytest

from backend.task_manager.models import TaskPriority, TaskState
from backend.task_manager.storage import TaskStorage
from backend.task_manager.manager import TaskManager


@pytest.fixture
def temp_task_dir():
    d = tempfile.mkdtemp(prefix="ai_film_tasks_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_task_creation_and_state_transition(temp_task_dir):
    storage = TaskStorage(storage_dir=temp_task_dir)
    mgr = TaskManager(storage=storage)

    task = mgr.create_task(
        project_id="proj_cyberpunk_01",
        task_type="full_production",
        inputs={"script_concept": "AI rebel in neo tokyo"},
        total_steps=5,
        priority=TaskPriority.HIGH
    )

    assert task.task_id.startswith("task_")
    assert task.state == TaskState.PENDING

    # Transition to RUNNING
    updated = mgr.update_state(task.task_id, TaskState.RUNNING)
    assert updated.state == TaskState.RUNNING

    # Transition to WAITING_MODEL
    updated = mgr.update_state(task.task_id, TaskState.WAITING_MODEL)
    assert updated.state == TaskState.WAITING_MODEL


def test_checkpoint_recording_and_safe_resumption(temp_task_dir):
    storage = TaskStorage(storage_dir=temp_task_dir)
    mgr = TaskManager(storage=storage)

    task = mgr.create_task(
        project_id="proj_01",
        task_type="render_shots",
        inputs={"scenes": ["scene_1", "scene_2"]},
        total_steps=3
    )

    # Step 1: Script completed
    mgr.record_checkpoint(
        task_id=task.task_id,
        step_name="script_generation",
        step_index=0,
        completed_units=["scene_1_script", "scene_2_script"],
        state_snapshot={"screenplay": "EXT. NEO TOKYO - NIGHT"}
    )

    # Step 2: Create a dummy artifact file for video clip
    clip1_path = os.path.join(temp_task_dir, "shot_01.mp4")
    with open(clip1_path, "w") as f:
        f.write("fake video binary data")

    mgr.record_checkpoint(
        task_id=task.task_id,
        step_name="shot_01_video",
        step_index=1,
        completed_units=["shot_01_render"],
        state_snapshot={"rendered_shots": ["shot_01.mp4"]},
        output_artifacts=[clip1_path]
    )

    # Simulate interruption (e.g. power outage or process termination)
    # Reload from storage with a new TaskManager instance
    new_storage = TaskStorage(storage_dir=temp_task_dir)
    new_mgr = TaskManager(storage=new_storage)

    # Prepare resumption
    resume_ctx = new_mgr.prepare_resumption(task.task_id)
    assert resume_ctx.can_resume is True
    # Should resume from step 2 (0 was script, 1 was shot_01)
    assert resume_ctx.resume_step_index == 2
    assert clip1_path in resume_ctx.verified_artifacts
    assert resume_ctx.state_snapshot.get("rendered_shots") == ["shot_01.mp4"]

    # Now execute resume
    res = new_mgr.resume_task(task.task_id)
    assert res.can_resume is True
    reloaded_task = new_mgr.get_task(task.task_id)
    assert reloaded_task.state == TaskState.RUNNING


def test_resumption_failure_on_missing_artifact(temp_task_dir):
    storage = TaskStorage(storage_dir=temp_task_dir)
    mgr = TaskManager(storage=storage)

    task = mgr.create_task(project_id="p2", task_type="edit", inputs={})

    missing_path = os.path.join(temp_task_dir, "non_existent.mp4")
    mgr.record_checkpoint(
        task_id=task.task_id,
        step_name="render_video",
        step_index=0,
        completed_units=["unit1"],
        state_snapshot={},
        output_artifacts=[missing_path]
    )

    # Should detect missing artifact and reject resuming from corrupted state
    resume_ctx = mgr.resume_task(task.task_id)
    assert resume_ctx.can_resume is False
    assert missing_path in resume_ctx.missing_artifacts
    reloaded = mgr.get_task(task.task_id)
    assert reloaded.state == TaskState.FAILED
