from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskOverallGroup:
    task_id: str
    group_task_ids: list[str]

    @property
    def group_size(self) -> int:
        return len(self.group_task_ids)

    @property
    def weight(self) -> int:
        return self.group_size


def load_depends_on_by_task_id(
    *,
    user_id: str,
    episode_tasks: Any,
    ordered_task_ids: list[str],
) -> dict[str, list[str]]:
    if not isinstance(episode_tasks, list):
        return {task_id: [] for task_id in ordered_task_ids}
    known_task_ids = set(ordered_task_ids)
    depends_on_by_task_id: dict[str, list[str]] = {}
    for item in episode_tasks:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("task_id", "")).strip()
        if not task_id or task_id not in known_task_ids:
            continue
        raw_depends_on = item.get("depends_on")
        if raw_depends_on is None:
            raw_depends_on = []
        if not isinstance(raw_depends_on, list):
            raise ValueError(
                f"invalid depends_on in episode.yaml for user_id={user_id} task_id={task_id}: expected list"
            )
        depends_on_task_ids: list[str] = []
        for dep in raw_depends_on:
            dep_task_id = str(dep).strip()
            if not dep_task_id:
                raise ValueError(
                    f"invalid depends_on entry in episode.yaml for user_id={user_id} task_id={task_id}: empty task_id"
                )
            depends_on_task_ids.append(dep_task_id)
        depends_on_by_task_id[task_id] = depends_on_task_ids
    return {
        task_id: list(depends_on_by_task_id.get(task_id, []))
        for task_id in ordered_task_ids
    }


def build_task_overall_groups(
    *,
    ordered_task_ids: list[str],
    depends_on_by_task_id: dict[str, list[str]],
) -> dict[str, TaskOverallGroup]:
    task_order_indexes = {
        task_id: idx
        for idx, task_id in enumerate(ordered_task_ids)
    }
    resolved_group_ids_by_task: dict[str, list[str]] = {}
    visiting: set[str] = set()

    def resolve_group_ids(task_id: str) -> list[str]:
        cached = resolved_group_ids_by_task.get(task_id)
        if cached is not None:
            return list(cached)
        if task_id in visiting:
            raise ValueError(f"cyclic depends_on detected while resolving overall group for task_id={task_id}")
        visiting.add(task_id)
        group_ids = {task_id}
        for dep_task_id in depends_on_by_task_id.get(task_id, []):
            if dep_task_id not in task_order_indexes:
                raise ValueError(
                    f"invalid depends_on contract for overall aggregation task_id={task_id}: unknown dependency {dep_task_id}"
                )
            group_ids.update(resolve_group_ids(dep_task_id))
        visiting.remove(task_id)
        ordered_group_ids = sorted(group_ids, key=lambda item: task_order_indexes[item])
        resolved_group_ids_by_task[task_id] = ordered_group_ids
        return list(ordered_group_ids)

    return {
        task_id: TaskOverallGroup(
            task_id=task_id,
            group_task_ids=resolve_group_ids(task_id),
        )
        for task_id in ordered_task_ids
    }


def compute_weighted_overall_average(
    task_scores: list[tuple[float, TaskOverallGroup]],
) -> tuple[float | None, dict[str, Any]]:
    if not task_scores:
        return None, {
            "mode": "dependency_group_size_weighted",
            "scored_task_count": 0,
            "total_weight": 0,
        }
    total_weight = sum(group.weight for _, group in task_scores)
    if total_weight < 1:
        return None, {
            "mode": "dependency_group_size_weighted",
            "scored_task_count": len(task_scores),
            "total_weight": 0,
        }
    weighted_score_sum = sum(score * group.weight for score, group in task_scores)
    return weighted_score_sum / total_weight, {
        "mode": "dependency_group_size_weighted",
        "scored_task_count": len(task_scores),
        "total_weight": total_weight,
    }
