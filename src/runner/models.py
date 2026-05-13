from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TaskRunResult:
    task_id: str
    status: str
    turns: int
    error: Optional[str] = None


@dataclass(frozen=True)
class PendingTask:
    task_id: str
    initial_message: str


@dataclass
class BenchmarkRunResult:
    status: str
    tasks: List[TaskRunResult] = field(default_factory=list)
