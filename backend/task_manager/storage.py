import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from backend.task_manager.models import FilmTask


class TaskStorage:
    """
    File-backed persistent storage for FilmTasks and their Checkpoints.
    Guarantees state persistence across process and machine restarts.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or "./storage/tasks").resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _task_path(self, task_id: str) -> Path:
        return self.storage_dir / f"{task_id}.json"

    def save_task(self, task: FilmTask) -> None:
        """Atomic write to prevent corrupted task state."""
        target_path = self._task_path(task.task_id)
        data = task.model_dump(mode="json")

        temp_fd, temp_path = tempfile.mkstemp(dir=self.storage_dir, prefix=f"{task.task_id}_tmp_")
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic replace
        os.replace(temp_path, target_path)

    def get_task(self, task_id: str) -> Optional[FilmTask]:
        path = self._task_path(task_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return FilmTask.model_validate(data)
        except Exception:
            return None

    def list_tasks(self, project_id: Optional[str] = None) -> List[FilmTask]:
        tasks = []
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                task = FilmTask.model_validate(data)
                if project_id is None or task.project_id == project_id:
                    tasks.append(task)
            except Exception:
                continue
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def delete_task(self, task_id: str) -> bool:
        path = self._task_path(task_id)
        if path.exists():
            path.unlink()
            return True
        return False
