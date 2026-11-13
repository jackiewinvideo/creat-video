import logging
import os
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from backend.task_manager.models import (
    FilmTask,
    TaskCheckpoint,
    TaskPriority,
    TaskState,
)
from backend.task_manager.storage import TaskStorage

logger = logging.getLogger(__name__)


class TaskResumeContext(BaseModel):
    task_id: str
    can_resume: bool
    resume_step_index: int
    resume_step_name: str
    state_snapshot: Dict[str, Any]
    verified_artifacts: List[str]
    missing_artifacts: List[str]
    message: str


class TaskManager:
    """
    State machine and checkpoint coordinator for film production tasks.
    Enforces checkpoint verification and seamless resumption from interruptions.
    """

    def __init__(self, storage: Optional[TaskStorage] = None):
        self.storage = storage or TaskStorage()

    def create_task(
        self,
        project_id: str,
        task_type: str,
        inputs: Dict[str, Any],
        total_steps: int = 1,
        priority: TaskPriority = TaskPriority.NORMAL,
        assigned_device_id: Optional[str] = None
    ) -> FilmTask:
        task = FilmTask(
            project_id=project_id,
            task_type=task_type,
            inputs=inputs,
            total_steps=total_steps,
            priority=priority,
            assigned_device_id=assigned_device_id,
            state=TaskState.PENDING
        )
        self.storage.save_task(task)
        logger.info(f"Created task '{task.task_id}' (Type: {task_type}, Project: {project_id})")
        return task

    def update_state(
        self,
        task_id: str,
        new_state: TaskState,
        error_message: Optional[str] = None,
        assigned_device_id: Optional[str] = None
    ) -> Optional[FilmTask]:
        task = self.storage.get_task(task_id)
        if not task:
            return None

        task.state = new_state
        task.updated_at = time.time()
        if error_message:
            task.error_message = error_message
        if assigned_device_id:
            task.assigned_device_id = assigned_device_id

        self.storage.save_task(task)
        logger.info(f"Task '{task_id}' transitioned to state: {new_state.value}")
        return task

    def record_checkpoint(
        self,
        task_id: str,
        step_name: str,
        step_index: int,
        completed_units: List[str],
        state_snapshot: Dict[str, Any],
        output_artifacts: Optional[List[str]] = None,
        model_id: Optional[str] = None,
        tool_id: Optional[str] = None
    ) -> Optional[TaskCheckpoint]:
        task = self.storage.get_task(task_id)
        if not task:
            return None

        cp = TaskCheckpoint(
            task_id=task_id,
            step_name=step_name,
            step_index=step_index,
            completed_units=completed_units,
            state_snapshot=state_snapshot,
            output_artifacts=output_artifacts or [],
            model_id=model_id,
            tool_id=tool_id
        )

        task.checkpoints.append(cp)
        task.current_step_index = step_index
        task.updated_at = time.time()

        # Update outputs with new state snapshot
        task.outputs.update(state_snapshot)

        self.storage.save_task(task)
        logger.info(f"Recorded checkpoint for Task '{task_id}' [Step {step_index}: {step_name}]")
        return cp

    def prepare_resumption(self, task_id: str) -> TaskResumeContext:
        """
        Inspects last checkpoint and verifies output artifacts on disk.
        Determines exactly from which step and unit the task can safely resume.
        """
        task = self.storage.get_task(task_id)
        if not task:
            return TaskResumeContext(
                task_id=task_id,
                can_resume=False,
                resume_step_index=0,
                resume_step_name="start",
                state_snapshot={},
                verified_artifacts=[],
                missing_artifacts=[],
                message="Task not found."
            )

        if not task.checkpoints:
            # Start from beginning
            return TaskResumeContext(
                task_id=task_id,
                can_resume=True,
                resume_step_index=0,
                resume_step_name="initial",
                state_snapshot=task.inputs,
                verified_artifacts=[],
                missing_artifacts=[],
                message="No previous checkpoints; resuming from step 0."
            )

        # Inspect latest checkpoint
        last_cp = task.checkpoints[-1]
        verified_artifacts = []
        missing_artifacts = []

        for artifact in last_cp.output_artifacts:
            if os.path.exists(artifact) and os.path.getsize(artifact) > 0:
                verified_artifacts.append(artifact)
            else:
                missing_artifacts.append(artifact)

        if missing_artifacts:
            return TaskResumeContext(
                task_id=task_id,
                can_resume=False,
                resume_step_index=last_cp.step_index,
                resume_step_name=last_cp.step_name,
                state_snapshot=last_cp.state_snapshot,
                verified_artifacts=verified_artifacts,
                missing_artifacts=missing_artifacts,
                message=f"Missing required artifact files: {missing_artifacts}. Checkpoint invalidated."
            )

        # Resume from next step
        next_step_index = last_cp.step_index + 1
        return TaskResumeContext(
            task_id=task_id,
            can_resume=True,
            resume_step_index=next_step_index,
            resume_step_name=f"resume_after_{last_cp.step_name}",
            state_snapshot=last_cp.state_snapshot,
            verified_artifacts=verified_artifacts,
            missing_artifacts=[],
            message=f"Resuming safely from step {next_step_index} after verified checkpoint '{last_cp.step_name}'."
        )

    def resume_task(self, task_id: str) -> TaskResumeContext:
        context = self.prepare_resumption(task_id)
        if context.can_resume:
            self.update_state(task_id, TaskState.RUNNING)
        else:
            self.update_state(task_id, TaskState.FAILED, error_message=context.message)
        return context

    def get_task(self, task_id: str) -> Optional[FilmTask]:
        return self.storage.get_task(task_id)

    def list_tasks(self, project_id: Optional[str] = None) -> List[FilmTask]:
        return self.storage.list_tasks(project_id)
