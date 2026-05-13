from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.data import UserDataRepository
from src.utils import get_logger, safe_model_id

from .checklist_evaluator import CriterionScore, TaskEvaluationScore, TurnEvaluationScore, UserEvaluationScore
from .overall_aggregation import build_task_overall_groups, compute_weighted_overall_average, load_depends_on_by_task_id
from .trace_history import (
    HISTORY_LOG_FILENAME_PATTERN,
    IntentJudgeTurn,
    MESSAGES_HISTORY_FILENAME_PATTERN,
    TRACE_SESSION_DIR_PATTERN,
    FollowupTurnStyle,
    load_task_followup_turn_styles,
    load_task_intent_judge_turns,
)

RESULT_FILENAME_PATTERN = re.compile(r"^(\d{8}_\d{6})_result\.json$")
ANSI_RESET = "\033[0m"
ANSI_BOLD_YELLOW = "\033[1;33m"
ANSI_CYAN = "\033[36m"

logger = get_logger("Bench.Evaluation.Reevaluation").profile("eval")
stage_logger = logger.profile("eval_stage")
aux_logger = logger.profile("eval_aux")


@dataclass(frozen=True)
class ReevaluationSourceRecord:
    task_id: str
    timestamp: str
    result_path: Path


@dataclass(frozen=True)
class OutputsTaskTurnSession:
    task_id: str
    session_timestamp: str
    session_dir: Path
    turn_paths: list[Path]


@dataclass(frozen=True)
class OutputEvalSnapshot:
    task_id: str
    timestamp: str
    result_path: Path
    trace_session_dir: Path
    turn_paths: list[Path]


def collect_output_task_turn_sessions(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    source_eval_timestamp: str | None = None,
) -> dict[str, OutputsTaskTurnSession]:
    user_root = output_dir / safe_model_id(model_id) / user_id
    if not user_root.is_dir():
        raise FileNotFoundError(f"user output dir not found: {user_root}")

    selected: dict[str, OutputsTaskTurnSession] = {}
    for task_dir in sorted(path for path in user_root.iterdir() if path.is_dir()):
        snapshot = _select_output_eval_snapshot(
            output_dir=output_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_dir.name,
            source_eval_timestamp=source_eval_timestamp,
        )
        if snapshot is None:
            continue
        selected[task_dir.name] = OutputsTaskTurnSession(
            task_id=task_dir.name,
            session_timestamp=snapshot.timestamp,
            session_dir=snapshot.trace_session_dir,
            turn_paths=list(snapshot.turn_paths),
        )
    return selected


def load_reevaluation_inputs(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    source_eval_timestamp: str | None,
    data_root: Path = Path("data"),
) -> tuple[
    UserEvaluationScore,
    list[ReevaluationSourceRecord],
    dict[str, list[Path]],
    dict[str, list[FollowupTurnStyle]],
    dict[str, list[IntentJudgeTurn]],
    list[tuple[str, str]],
]:
    repository = UserDataRepository(data_root=str(data_root))
    episode, tasks = _load_episode_and_tasks_for_reeval(repository=repository, user_id=user_id)
    ordered_task_ids = [task_id for task_id in episode.task_order if task_id in tasks] or sorted(tasks.keys())
    depends_on_by_task_id = load_depends_on_by_task_id(
        user_id=user_id,
        episode_tasks=episode.raw.get("tasks"),
        ordered_task_ids=ordered_task_ids,
    )
    overall_groups_by_task_id = build_task_overall_groups(
        ordered_task_ids=ordered_task_ids,
        depends_on_by_task_id=depends_on_by_task_id,
    )

    checklist_tasks: list[TaskEvaluationScore] = []
    source_records: list[ReevaluationSourceRecord] = []
    explicit_none_tasks: list[tuple[str, str]] = []
    missing_checklist_tasks: list[str] = []

    for task_id in ordered_task_ids:
        task = tasks[task_id]
        has_checklist = bool(task.objectives or task.tools_evaluation_path is not None)
        if not has_checklist:
            explicit_none_tasks.append((task_id, task.title))
            continue

        snapshot = _select_output_eval_snapshot(
            output_dir=output_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_id,
            source_eval_timestamp=source_eval_timestamp,
        )
        if snapshot is None:
            missing_checklist_tasks.append(task_id)
            continue
        checklist_task = _load_checklist_task_from_result(
            result_path=snapshot.result_path,
            task_id=task_id,
            task_title=task.title,
            expected_checklist_criteria=list(task.objectives),
            expected_tools_evaluation_path=task.tools_evaluation_path,
            history_dir=output_dir / safe_model_id(model_id) / user_id / task_id / "eval",
            overall_group_task_ids=list(overall_groups_by_task_id[task_id].group_task_ids),
            overall_group_size=overall_groups_by_task_id[task_id].group_size,
            overall_weight=overall_groups_by_task_id[task_id].weight,
        )
        checklist_tasks.append(checklist_task)
        source_records.append(
            ReevaluationSourceRecord(
                task_id=task_id,
                timestamp=snapshot.timestamp,
                result_path=snapshot.result_path,
            )
        )

    if missing_checklist_tasks:
        raise FileNotFoundError(
            "missing reusable checklist result for task(s): " + ", ".join(sorted(missing_checklist_tasks))
        )

    task_scores = [
        (task.average_score, overall_groups_by_task_id[task.task_id])
        for task in checklist_tasks
    ]
    overall_average, overall_aggregation = compute_weighted_overall_average(task_scores)
    checklist_summary = UserEvaluationScore(
        user_id=user_id,
        agent_id=model_id,
        generated_at="",
        overall_average_score=overall_average,
        overall_aggregation=overall_aggregation,
        tasks=checklist_tasks,
    )

    turn_sessions = collect_output_task_turn_sessions(
        output_dir=output_dir,
        model_id=model_id,
        user_id=user_id,
        source_eval_timestamp=source_eval_timestamp,
    )
    turn_paths_by_task_id = {task_id: session.turn_paths for task_id, session in turn_sessions.items()}
    followup_turn_styles_by_task_id = {
        task_id: load_task_followup_turn_styles(
            output_dir=output_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_id,
        )
        for task_id in turn_paths_by_task_id
    }
    intent_judge_turns_by_task_id = {
        task_id: load_task_intent_judge_turns(
            output_dir=output_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_id,
        )
        for task_id in turn_paths_by_task_id
    }
    return (
        checklist_summary,
        source_records,
        turn_paths_by_task_id,
        followup_turn_styles_by_task_id,
        intent_judge_turns_by_task_id,
        explicit_none_tasks,
    )


def _load_episode_and_tasks_for_reeval(
    *,
    repository: UserDataRepository,
    user_id: str,
):
    user_root = repository.data_root / user_id
    episode = repository._load_episode(user_root / "episode.yaml")
    tasks_dir = user_root / "tasks"
    tasks = {}
    if tasks_dir.exists():
        for task_path in tasks_dir.glob("*/task.yaml"):
            task = repository._load_task(task_path)
            tasks[task.task_id] = task
    if not tasks:
        raise FileNotFoundError(f"no task specs found for reeval under: {tasks_dir}")
    return episode, tasks


def log_reused_checklist_sources(source_records: list[ReevaluationSourceRecord]) -> None:
    if not source_records:
        return
    lines = ["Reusing checklist results"]
    for record in source_records:
        lines.append(
            f"task_id={record.task_id} source_eval_timestamp="
            f"{_format_highlight(record.timestamp, ANSI_BOLD_YELLOW)} result_path="
            f"{_format_highlight(str(record.result_path), ANSI_CYAN)}"
        )
        aux_logger.info(
            "Reused checklist result task_id={} source_eval_timestamp={} result_path={}",
            record.task_id,
            record.timestamp,
            record.result_path,
            data={
                "task_id": record.task_id,
                "source_eval_timestamp": record.timestamp,
                "result_path": str(record.result_path),
            },
        )
    stage_logger.info("\n".join(lines), persist=False)


def _format_highlight(text: str, color: str) -> str:
    return f"{color}{text}{ANSI_RESET}"


def _select_output_eval_snapshot(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
    source_eval_timestamp: str | None,
) -> OutputEvalSnapshot | None:
    result_dir = output_dir / safe_model_id(model_id) / user_id / task_id / "eval" / "results"
    trace_logs_dir = output_dir / safe_model_id(model_id) / user_id / task_id / "eval" / "trace_logs"
    if not result_dir.is_dir() and not trace_logs_dir.is_dir():
        return None
    if source_eval_timestamp is not None:
        result_path = result_dir / f"{source_eval_timestamp}_result.json"
        trace_session_dir = trace_logs_dir / source_eval_timestamp
        if not result_path.is_file() or not trace_session_dir.is_dir():
            return None
        turn_paths = sorted(trace_session_dir.glob("turn_*.json"), key=_normalize_turn_sort_key)
        if not turn_paths:
            return None
        return OutputEvalSnapshot(
            task_id=task_id,
            timestamp=source_eval_timestamp,
            result_path=result_path,
            trace_session_dir=trace_session_dir,
            turn_paths=turn_paths,
        )

    latest: OutputEvalSnapshot | None = None
    for file_path in result_dir.iterdir():
        if not file_path.is_file():
            continue
        match = RESULT_FILENAME_PATTERN.match(file_path.name)
        if match is None:
            continue
        timestamp = match.group(1)
        trace_session_dir = trace_logs_dir / timestamp
        if not trace_session_dir.is_dir():
            continue
        turn_paths = sorted(trace_session_dir.glob("turn_*.json"), key=_normalize_turn_sort_key)
        if not turn_paths:
            continue
        snapshot = OutputEvalSnapshot(
            task_id=task_id,
            timestamp=timestamp,
            result_path=file_path,
            trace_session_dir=trace_session_dir,
            turn_paths=turn_paths,
        )
        if latest is None or snapshot.timestamp > latest.timestamp:
            latest = snapshot
    return latest


def _load_checklist_task_from_result(
    *,
    result_path: Path,
    task_id: str,
    task_title: str,
    expected_checklist_criteria: list[dict[str, Any]],
    expected_tools_evaluation_path: Path | None,
    history_dir: Path,
    overall_group_task_ids: list[str],
    overall_group_size: int,
    overall_weight: int,
) -> TaskEvaluationScore:
    with result_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"result payload must be an object: {result_path}")
    task_payload = payload.get("task")
    if not isinstance(task_payload, dict):
        raise ValueError(f"result payload missing task object: {result_path}")
    result_task_id = str(task_payload.get("task_id") or "").strip()
    if result_task_id != task_id:
        raise ValueError(f"result task_id mismatch in {result_path}: expected {task_id}, got {result_task_id}")
    result_title = str(task_payload.get("title") or "").strip()
    if result_title != task_title:
        raise ValueError(
            f"result title mismatch for task_id={task_id} in {result_path}: expected {task_title!r}, got {result_title!r}"
        )
    checklist_payload = task_payload.get("checklist")
    expected_has_checklist = bool(expected_checklist_criteria or expected_tools_evaluation_path is not None)
    if not expected_has_checklist:
        raise ValueError(
            f"internal reeval contract violation for task_id={task_id}: task should not require checklist reuse"
        )
    if not isinstance(checklist_payload, dict):
        raise ValueError(
            f"result checklist mismatch for task_id={task_id}: "
            f"current data requires checklist scoring but result has task.checklist={checklist_payload!r} in {result_path}"
        )

    criterion_scores = _parse_criterion_scores(
        checklist_payload.get("criterion_scores"),
        source_path=result_path,
        field_name="task.checklist.criterion_scores",
    )
    expected_data_criteria = _build_expected_data_criteria(expected_checklist_criteria)
    _validate_checklist_against_task_spec(
        task_id=task_id,
        result_path=result_path,
        criterion_scores=criterion_scores,
        expected_checklist_criteria=expected_data_criteria,
        expected_tools_evaluation_path=expected_tools_evaluation_path,
    )
    turn_evaluations = _parse_turn_evaluations(
        checklist_payload.get("turn_evaluations"),
        source_path=result_path,
    )
    criterion_scores = _rebuild_reused_criterion_scores(
        criterion_scores=criterion_scores,
        expected_checklist_criteria=expected_data_criteria,
        expected_tools_evaluation_path=expected_tools_evaluation_path,
        source_path=result_path,
        field_name="task.checklist.criterion_scores",
    )
    turn_evaluations = _rebuild_reused_turn_evaluations(
        turn_evaluations=turn_evaluations,
        expected_checklist_criteria=expected_data_criteria,
        expected_tools_evaluation_path=expected_tools_evaluation_path,
        source_path=result_path,
    )
    total_weight = sum(item.weight for item in criterion_scores)
    weighted_yes_score = sum(item.weighted_value for item in criterion_scores)
    average_score = weighted_yes_score / total_weight if total_weight > 0 else 0.0

    return TaskEvaluationScore(
        task_id=task_id,
        title=task_title,
        history_dir=history_dir,
        criterion_scores=criterion_scores,
        average_score=average_score,
        turn_evaluations=turn_evaluations,
        overall_group_task_ids=overall_group_task_ids,
        overall_group_size=overall_group_size,
        overall_weight=overall_weight,
    )


def _parse_criterion_scores(raw_scores: Any, *, source_path: Path, field_name: str) -> list[CriterionScore]:
    if not isinstance(raw_scores, list):
        raise ValueError(f"{field_name} must be a list in {source_path}")
    parsed: list[CriterionScore] = []
    for index, item in enumerate(raw_scores, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{field_name}[{index}] must be an object in {source_path}")
        parsed.append(
            CriterionScore(
                index=int(item.get("index")),
                criterion=str(item.get("criterion") or "").strip(),
                weight=float(item.get("weight")),
                score=str(item.get("score") or "").strip(),
                value=int(item.get("value")),
            )
        )
    return parsed


def _build_expected_data_criteria(expected_checklist_criteria: list[dict[str, Any]]) -> list[tuple[str, float]]:
    return [
        (str(item.get("criterion") or "").strip(), float(item.get("weight", 1.0)))
        for item in expected_checklist_criteria
        if str(item.get("criterion") or "").strip()
    ]


def _rebuild_reused_criterion_scores(
    *,
    criterion_scores: list[CriterionScore],
    expected_checklist_criteria: list[tuple[str, float]],
    expected_tools_evaluation_path: Path | None,
    source_path: Path,
    field_name: str,
) -> list[CriterionScore]:
    rebuilt: list[CriterionScore] = []
    expected_count_min = len(expected_checklist_criteria)
    if expected_tools_evaluation_path is None and len(criterion_scores) != expected_count_min:
        raise ValueError(
            f"{field_name} count mismatch in {source_path}: expected {expected_count_min}, got {len(criterion_scores)}"
        )
    if expected_tools_evaluation_path is not None and len(criterion_scores) < expected_count_min:
        raise ValueError(
            f"{field_name} count mismatch in {source_path}: expected at least {expected_count_min}, got {len(criterion_scores)}"
        )

    for index, item in enumerate(criterion_scores, start=1):
        if index <= expected_count_min:
            expected_text, expected_weight = expected_checklist_criteria[index - 1]
            if item.index != index:
                raise ValueError(
                    f"{field_name}[{index}] index mismatch in {source_path}: expected {index}, got {item.index}"
                )
            if item.criterion != expected_text:
                raise ValueError(
                    f"{field_name}[{index}] text mismatch in {source_path}: expected {expected_text!r}, got {item.criterion!r}"
                )
            rebuilt.append(
                CriterionScore(
                    index=item.index,
                    criterion=item.criterion,
                    weight=expected_weight,
                    score=item.score,
                    value=item.value,
                )
            )
            continue

        if expected_tools_evaluation_path is None:
            raise ValueError(
                f"{field_name}[{index}] unexpected extra criterion in {source_path}: {item.criterion!r}"
            )
        rebuilt.append(
            CriterionScore(
                index=item.index,
                criterion=item.criterion,
                weight=1.0,
                score=item.score,
                value=item.value,
            )
        )
    return rebuilt


def _parse_turn_evaluations(raw_turns: Any, *, source_path: Path) -> list[TurnEvaluationScore]:
    if not isinstance(raw_turns, list):
        raise ValueError(f"task.checklist.turn_evaluations must be a list in {source_path}")
    parsed: list[TurnEvaluationScore] = []
    for index, item in enumerate(raw_turns, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"task.checklist.turn_evaluations[{index}] must be an object in {source_path}")
        llm_evaluation = item.get("llm_evaluation")
        if not isinstance(llm_evaluation, dict):
            raise ValueError(f"turn_evaluations[{index}].llm_evaluation must be an object in {source_path}")
        parsed.append(
            TurnEvaluationScore(
                turn_index=int(item.get("turn_index")),
                history_path=Path(str(item.get("history_path") or "")),
                evaluation_prompt=str(llm_evaluation.get("prompt") or ""),
                llm_raw_responses=[
                    str(raw_response)
                    for raw_response in list(llm_evaluation.get("raw_responses") or [])
                ],
                criterion_scores=_parse_criterion_scores(
                    item.get("criterion_scores"),
                    source_path=source_path,
                    field_name=f"task.checklist.turn_evaluations[{index}].criterion_scores",
                ),
                average_score=float(item.get("average_score")),
                tools_evaluation=(
                    dict(item.get("tools_evaluation"))
                    if isinstance(item.get("tools_evaluation"), dict)
                    else {}
                ),
            )
        )
    return parsed


def _rebuild_reused_turn_evaluations(
    *,
    turn_evaluations: list[TurnEvaluationScore],
    expected_checklist_criteria: list[tuple[str, float]],
    expected_tools_evaluation_path: Path | None,
    source_path: Path,
) -> list[TurnEvaluationScore]:
    rebuilt: list[TurnEvaluationScore] = []
    for index, item in enumerate(turn_evaluations, start=1):
        rebuilt_scores = _rebuild_reused_criterion_scores(
            criterion_scores=item.criterion_scores,
            expected_checklist_criteria=expected_checklist_criteria,
            expected_tools_evaluation_path=expected_tools_evaluation_path,
            source_path=source_path,
            field_name=f"task.checklist.turn_evaluations[{index}].criterion_scores",
        )
        total_weight = sum(score.weight for score in rebuilt_scores)
        average_score = sum(score.weighted_value for score in rebuilt_scores) / total_weight if total_weight > 0 else 0.0
        rebuilt.append(
            TurnEvaluationScore(
                turn_index=item.turn_index,
                history_path=item.history_path,
                evaluation_prompt=item.evaluation_prompt,
                llm_raw_responses=list(item.llm_raw_responses),
                criterion_scores=rebuilt_scores,
                average_score=average_score,
                tools_evaluation=dict(item.tools_evaluation) if isinstance(item.tools_evaluation, dict) else {},
            )
        )
    return rebuilt


def _validate_checklist_against_task_spec(
    *,
    task_id: str,
    result_path: Path,
    criterion_scores: list[CriterionScore],
    expected_checklist_criteria: list[tuple[str, float]],
    expected_tools_evaluation_path: Path | None,
) -> None:
    expected_count_min = len(expected_checklist_criteria)
    actual_count = len(criterion_scores)
    if expected_tools_evaluation_path is None and actual_count != expected_count_min:
        raise ValueError(
            f"result checklist criterion count mismatch for task_id={task_id} in {result_path}: "
            f"expected {expected_count_min}, got {actual_count}"
        )
    if expected_tools_evaluation_path is not None and actual_count < expected_count_min:
        raise ValueError(
            f"result checklist criterion count mismatch for task_id={task_id} in {result_path}: "
            f"expected at least {expected_count_min}, got {actual_count}"
        )

    for index, (expected_text, _) in enumerate(expected_checklist_criteria, start=1):
        actual = criterion_scores[index - 1]
        if actual.index != index:
            raise ValueError(
                f"result checklist criterion index mismatch for task_id={task_id} in {result_path}: "
                f"expected index {index}, got {actual.index}"
            )
        if actual.criterion != expected_text:
            raise ValueError(
                f"result checklist criterion text mismatch for task_id={task_id} criterion_index={index} "
                f"in {result_path}: expected {expected_text!r}, got {actual.criterion!r}"
            )

def _normalize_turn_sort_key(path: Path) -> tuple[int, str]:
    name = path.name
    match = re.match(r"^turn_(\d+)\.json$", name)
    if match is not None:
        return int(match.group(1)), name
    match = re.match(r"^turn_(\d{8})_(\d{6})\.json$", name)
    if match is not None:
        return int(match.group(1) + match.group(2)), name
    return (10**18, name)
