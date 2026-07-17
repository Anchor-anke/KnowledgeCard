"""In-memory asynchronous summary jobs for local testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4


TASK_UPLOADING = "UPLOADING"
TASK_EXTRACTED = "EXTRACTED"
TASK_GENERATING = "GENERATING"
TASK_DRAFT_READY = "DRAFT_READY"
TASK_FAILED = "FAILED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SummaryTask:
    id: str
    title: str
    source_type: str
    source_name: Optional[str]
    status: str = TASK_UPLOADING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def public(self) -> Dict[str, Any]:
        return {
            "task_id": self.id,
            "title": self.title,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SummaryJobService:
    """Coordinates task state and delegates generation to an AI client."""

    def __init__(self, ai_client):
        self.ai_client = ai_client
        self._tasks: Dict[str, SummaryTask] = {}
        self._lock = Lock()

    def create_task(
        self,
        title: str,
        source_type: str,
        source_name: Optional[str],
        text: str,
        background_tasks,
    ) -> SummaryTask:
        task = SummaryTask(
            id=f"summary_{uuid4().hex}",
            title=title.strip() or "未命名资料",
            source_type=source_type,
            source_name=source_name,
        )
        with self._lock:
            self._tasks[task.id] = task
        self._update(task.id, status=TASK_EXTRACTED)
        background_tasks.add_task(self.process_task, task.id, text)
        return self.get_task(task.id)

    def process_task(self, task_id: str, text: str) -> None:
        task = self.get_task(task_id)
        if task is None:
            return
        self._update(task_id, status=TASK_GENERATING, error=None)
        try:
            result = self.ai_client.summarize(
                title=task.title,
                text=text,
                source_type=task.source_type,
            )
        except Exception as exc:
            self._update(task_id, status=TASK_FAILED, error=str(exc))
            return
        self._update(task_id, status=TASK_DRAFT_READY, result=result, error=None)

    def get_task(self, task_id: str) -> Optional[SummaryTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def _update(self, task_id: str, **changes) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            for key, value in changes.items():
                setattr(task, key, value)
            task.updated_at = utc_now()
