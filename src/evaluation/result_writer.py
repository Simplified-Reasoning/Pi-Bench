from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.utils import safe_model_id

from .checklist_evaluator import TaskEvaluationScore, UserEvaluationScore
from .proactiveness_evaluator import ProactivenessTaskScore, ProactivenessUserScore


def write_combined_task_results(
    *,
    checklist_summary: UserEvaluationScore | None,
    proactiveness_summary: ProactivenessUserScore | None,
    results_root: Path,
    timestamp: datetime,
    explicit_none_tasks: list[tuple[str, str]] | None = None,
) -> list[Path]:
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    if checklist_summary is None and proactiveness_summary is None:
        raise ValueError("at least one evaluation summary is required")

    checklist_by_task_id = {task.task_id: task for task in checklist_summary.tasks} if checklist_summary else {}
    proactiveness_by_task_id = (
        {task.task_id: task for task in proactiveness_summary.tasks} if proactiveness_summary else {}
    )

    ordered_tasks: list[tuple[str, str]] = []
    seen_task_ids: set[str] = set()
    if checklist_summary is not None:
        for task in checklist_summary.tasks:
            if task.task_id in seen_task_ids:
                continue
            ordered_tasks.append((task.task_id, task.title))
            seen_task_ids.add(task.task_id)
    if proactiveness_summary is not None:
        for task in proactiveness_summary.tasks:
            if task.task_id in seen_task_ids:
                continue
            ordered_tasks.append((task.task_id, task.title))
            seen_task_ids.add(task.task_id)
    for task_id, title in explicit_none_tasks or []:
        if task_id in seen_task_ids:
            continue
        ordered_tasks.append((task_id, title))
        seen_task_ids.add(task_id)

    base_summary = checklist_summary or proactiveness_summary
    checklist_overall_score = checklist_summary.overall_average_score if checklist_summary is not None else None
    proactiveness_overall_score = (
        proactiveness_summary.overall_average_score if proactiveness_summary is not None else None
    )
    overall_average_score = (
        checklist_overall_score if checklist_overall_score is not None else proactiveness_overall_score
    )
    overall_aggregation = {
        "checklist": (
            dict(checklist_summary.overall_aggregation)
            if checklist_summary is not None
            else {
                "mode": "dependency_group_size_weighted",
                "scored_task_count": 0,
                "total_weight": 0,
            }
        ),
        "proactiveness": (
            dict(proactiveness_summary.overall_aggregation)
            if proactiveness_summary is not None
            else {
                "mode": "dependency_group_size_weighted",
                "scored_task_count": 0,
                "total_weight": 0,
            }
        ),
    }

    output_paths: list[Path] = []
    for task_id, task_title in ordered_tasks:
        checklist_task = checklist_by_task_id.get(task_id)
        proactiveness_task = proactiveness_by_task_id.get(task_id)
        task_payload = _build_task_payload(
            checklist_task,
            proactiveness_task,
            task_id=task_id,
            title=task_title,
        )
        output_dir = (
            results_root / safe_model_id(base_summary.agent_id) / base_summary.user_id / task_id / "eval" / "results"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp_str}_result.json"
        output_path.write_text(
            json.dumps(
                {
                    "user_id": base_summary.user_id,
                    "agent_id": base_summary.agent_id,
                    "generated_at": base_summary.generated_at,
                    "overall_average_score": overall_average_score,
                    "overall_checklist_average_score": checklist_overall_score,
                    "overall_proactiveness_average_score": proactiveness_overall_score,
                    "overall_aggregation": overall_aggregation,
                    "task_count": len(ordered_tasks),
                    "checklist_task_count": len(checklist_summary.tasks) if checklist_summary is not None else 0,
                    "proactiveness_task_count": (
                        _count_proactiveness_overall_tasks(proactiveness_summary)
                        if proactiveness_summary is not None
                        else 0
                    ),
                    "task": task_payload,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        output_paths.append(output_path)
    return output_paths


def _count_proactiveness_overall_tasks(summary: ProactivenessUserScore) -> int:
    return sum(1 for task in summary.tasks if task.include_in_overall)


def _build_task_payload(
    checklist_task: TaskEvaluationScore | None,
    proactiveness_task: ProactivenessTaskScore | None,
    *,
    task_id: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    if checklist_task is not None:
        task_id = checklist_task.task_id
        title = checklist_task.title
    elif proactiveness_task is not None:
        task_id = proactiveness_task.task_id
        title = proactiveness_task.title
    elif task_id is None:
        raise ValueError("at least one task payload is required")

    return {
        "task_id": task_id,
        "title": title or "",
        "checklist": checklist_task.to_dict() if checklist_task is not None else None,
        "proactiveness": proactiveness_task.to_dict() if proactiveness_task is not None else None,
    }
