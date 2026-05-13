from __future__ import annotations

import asyncio
import importlib.util
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from time import perf_counter
from types import ModuleType
from typing import Any, Callable

from src.data import UserDataRepository, format_hidden_intents_xml
from src.data.models import ToolTraceSpec
from src.llm import LLMClient
from src.utils import activate_task_logging, complete_task_logging, get_logger

from .overall_aggregation import (
    TaskOverallGroup,
    build_task_overall_groups,
    compute_weighted_overall_average,
    load_depends_on_by_task_id,
)
from .prompts import build_criterion_scorer_prompt
from .trace_history import (
    FollowupTurnStyle,
    collect_tool_history,
)

logger = get_logger("Bench.Evaluation.Checklist").profile("eval")
stage_logger = logger.profile("eval_stage")
DEFAULT_PARSE_RETRIES = 5
TRACE_TURN_FILENAME_PATTERN = re.compile(r"^trace_(\d+)\.txt$")
CRITERION_BLOCK_PATTERN = re.compile(
    r"<c(?P<idx>\d+)>\s*<criterion>\s*(?P<criterion>.*?)\s*</criterion>\s*<score>\s*(?P<score>YES|NO)\s*</score>\s*</c(?P=idx)>",
    flags=re.IGNORECASE | re.DOTALL,
)


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _normalize_xml_text(value: str) -> str:
    return _normalize_whitespace(unescape(value or ""))


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return repr(value)


def _to_binary_score(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        if value in {0, 1}:
            return int(value)
        raise ValueError(f"score must be 0 or 1, got {value!r}")
    raise ValueError(f"score must be 0 or 1, got {value!r}")


def _normalize_initial_scores(
    *,
    payload: Any,
    script_path: Path,
) -> tuple[list[str], dict[str, int]]:
    if not isinstance(payload, dict):
        raise ValueError(
            f"tools evaluation script must return dict in score([]): {script_path}"
        )
    checklist_keys: list[str] = []
    parsed: dict[str, int] = {}
    for raw_key, raw_value in payload.items():
        key = str(raw_key).strip()
        if not key:
            raise ValueError(
                f"tools evaluation script returned empty checklist key in score([]): {script_path}"
            )
        if key in parsed:
            continue
        parsed[key] = _to_binary_score(raw_value)
        checklist_keys.append(key)
    if not checklist_keys:
        raise ValueError(
            f"tools evaluation script score([]) must return non-empty checklist dict: {script_path}"
        )
    return checklist_keys, parsed


def _normalize_turn_scores(
    *,
    payload: Any,
    checklist_keys: list[str],
    script_path: Path,
    user_id: str,
    task_id: str,
    turn_index: int,
) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError(f"score() return must be dict, got {type(payload).__name__}")
    known_keys = set(checklist_keys)
    parsed: dict[str, int] = {}
    for raw_key, raw_value in payload.items():
        key = str(raw_key).strip()
        if not key or key not in known_keys:
            if key:
                logger.warning(
                    "Ignoring unknown tools checklist key user={} task={} turn={} key={} script={}",
                    user_id,
                    task_id,
                    turn_index,
                    key,
                    script_path,
                    data={
                        "user_id": user_id,
                        "task_id": task_id,
                        "turn_index": turn_index,
                        "tools_script_path": str(script_path),
                        "unknown_tools_checklist_key": key,
                    },
                )
            continue
        parsed[key] = _to_binary_score(raw_value)
    return {key: int(parsed.get(key, 0)) for key in checklist_keys}


@dataclass(frozen=True)
class CriterionScore:
    index: int
    criterion: str
    weight: float
    score: str
    value: int

    @property
    def weighted_value(self) -> float:
        return self.value * self.weight


@dataclass(frozen=True)
class ParsedScoreAttempt:
    parsed_scores_by_index: dict[int, CriterionScore]
    mismatch_indexes: tuple[int, ...]


@dataclass(frozen=True)
class TurnEvaluationScore:
    turn_index: int
    history_path: Path
    evaluation_prompt: str
    llm_raw_responses: list[str]
    criterion_scores: list[CriterionScore]
    average_score: float
    tools_evaluation: dict[str, Any] | None = None

    @property
    def yes_count(self) -> int:
        return sum(item.value for item in self.criterion_scores)

    @property
    def criterion_count(self) -> int:
        return len(self.criterion_scores)

    @property
    def total_weight(self) -> float:
        return sum(item.weight for item in self.criterion_scores)

    @property
    def weighted_yes_score(self) -> float:
        return sum(item.weighted_value for item in self.criterion_scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "history_path": str(self.history_path),
            "criterion_count": self.criterion_count,
            "yes_count": self.yes_count,
            "total_weight": self.total_weight,
            "weighted_yes_score": self.weighted_yes_score,
            "average_score": self.average_score,
            "llm_evaluation": {
                "prompt": self.evaluation_prompt,
                "raw_responses": list(self.llm_raw_responses),
            },
            "tools_evaluation": (
                dict(self.tools_evaluation)
                if isinstance(self.tools_evaluation, dict)
                else {}
            ),
            "criterion_scores": [
                {
                    "index": item.index,
                    "criterion": item.criterion,
                    "weight": item.weight,
                    "score": item.score,
                    "value": item.value,
                    "weighted_value": item.weighted_value,
                }
                for item in self.criterion_scores
            ],
        }


@dataclass(frozen=True)
class TaskEvaluationScore:
    task_id: str
    title: str
    history_dir: Path
    criterion_scores: list[CriterionScore]
    average_score: float
    turn_evaluations: list[TurnEvaluationScore]
    overall_group_task_ids: list[str]
    overall_group_size: int
    overall_weight: int

    @property
    def yes_count(self) -> int:
        return sum(item.value for item in self.criterion_scores)

    @property
    def criterion_count(self) -> int:
        return len(self.criterion_scores)

    @property
    def total_weight(self) -> float:
        return sum(item.weight for item in self.criterion_scores)

    @property
    def weighted_yes_score(self) -> float:
        return sum(item.weighted_value for item in self.criterion_scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "history_dir": str(self.history_dir),
            "criterion_count": self.criterion_count,
            "yes_count": self.yes_count,
            "total_weight": self.total_weight,
            "weighted_yes_score": self.weighted_yes_score,
            "average_score": self.average_score,
            "overall_group_task_ids": list(self.overall_group_task_ids),
            "overall_group_size": self.overall_group_size,
            "overall_weight": self.overall_weight,
            "criterion_scores": [
                {
                    "index": item.index,
                    "criterion": item.criterion,
                    "weight": item.weight,
                    "score": item.score,
                    "value": item.value,
                    "weighted_value": item.weighted_value,
                }
                for item in self.criterion_scores
            ],
            "turn_evaluations": [item.to_dict() for item in self.turn_evaluations],
        }


@dataclass(frozen=True)
class UserEvaluationScore:
    user_id: str
    agent_id: str
    generated_at: str
    overall_average_score: float | None
    overall_aggregation: dict[str, Any]
    tasks: list[TaskEvaluationScore]

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "generated_at": self.generated_at,
            "overall_average_score": self.overall_average_score,
            "overall_aggregation": dict(self.overall_aggregation),
            "task_count": len(self.tasks),
            "tasks": [item.to_dict() for item in self.tasks],
        }


@dataclass(frozen=True)
class TaskEvaluationInput:
    task_id: str
    title: str
    history_dir: Path
    hidden_intents_xml: str
    criteria: list["TaskCriterion"]
    followup_turn_styles: list[FollowupTurnStyle]
    tool_trace_specs: list[ToolTraceSpec]
    tools_evaluation_path: Path | None
    overall_group: TaskOverallGroup


@dataclass(frozen=True)
class TaskCriterion:
    criterion: str
    weight: float
    evaluation: str  # llm | tool_script
    tool_key: str | None = None


@dataclass(frozen=True)
class ToolScriptRuntime:
    module_name: str
    script_path: Path
    script_code: str
    score_fn: Callable[[list[dict[str, Any]]], Any]
    checklist_keys: list[str]

    def score_turn(
        self,
        *,
        tools_history: list[dict[str, Any]],
        user_id: str,
        task_id: str,
        turn_index: int,
    ) -> tuple[dict[str, int], dict[str, Any]]:
        raw_payload: Any = None
        try:
            raw_payload = self.score_fn(tools_history)
            normalized = _normalize_turn_scores(
                payload=raw_payload,
                checklist_keys=self.checklist_keys,
                script_path=self.script_path,
                user_id=user_id,
                task_id=task_id,
                turn_index=turn_index,
            )
            return normalized, {
                "script_path": str(self.script_path),
                "script_code": self.script_code,
                "raw_output": _to_json_safe(raw_payload),
                "error": None,
            }
        except Exception as exc:
            logger.warning(
                "tools evaluation failed user={} task={} turn={} script={} reason={}",
                user_id,
                task_id,
                turn_index,
                self.script_path,
                str(exc),
                data={
                    "user_id": user_id,
                    "task_id": task_id,
                    "turn_index": turn_index,
                    "tools_script_path": str(self.script_path),
                },
            )
            return {key: 0 for key in self.checklist_keys}, {
                "script_path": str(self.script_path),
                "script_code": self.script_code,
                "raw_output": _to_json_safe(raw_payload),
                "error": str(exc),
            }


class ChecklistEvaluator:
    def __init__(
        self,
        *,
        llm_client: LLMClient,
        repository: UserDataRepository | None = None,
        data_root: Path = Path("data"),
        parse_retries: int = DEFAULT_PARSE_RETRIES,
        results_root: Path = Path("outputs"),
    ) -> None:
        self.llm = llm_client
        self.repository = repository or UserDataRepository(data_root=str(data_root))
        self.parse_retries = int(parse_retries)
        if self.parse_retries < 1:
            raise ValueError("parse_retries must be >= 1")
        self.results_root = Path(results_root)

    async def evaluate_user(
        self,
        *,
        user_id: str,
        agent_id: str,
        trace_dir_by_task_id: dict[str, Path],
        task_ids: list[str] | None = None,
        followup_turn_styles_by_task_id: dict[str, list[FollowupTurnStyle]] | None = None,
        timestamp: datetime | None = None,
        eval_log_timestamp: str | None = None,
        write_results: bool = True,
    ) -> tuple[UserEvaluationScore, list[Path]]:
        user_role, task_inputs = self._load_task_inputs(
            user_id,
            trace_dir_by_task_id,
            task_ids=task_ids,
            followup_turn_styles_by_task_id=followup_turn_styles_by_task_id,
        )
        task_results = await asyncio.gather(
            *(
                self._evaluate_task(
                    user_id=user_id,
                    user_role=user_role,
                    task_input=task_input,
                    eval_log_timestamp=eval_log_timestamp,
                )
                for task_input in task_inputs
            )
        )
        succeeded_tasks = [item for item in task_results if item is not None]
        overall_average, overall_aggregation = compute_weighted_overall_average(
            [
                (
                    item.average_score,
                    next(task_input.overall_group for task_input in task_inputs if task_input.task_id == item.task_id),
                )
                for item in succeeded_tasks
            ]
        )
        average_text = f"{overall_average:.3f}" if overall_average is not None else "n/a"
        stage_logger.info(
            "user_eval done user={} agent={} ok={} skip={} avg={}",
            user_id,
            agent_id,
            len(succeeded_tasks),
            len(task_inputs) - len(succeeded_tasks),
            average_text,
            data={
                "user_id": user_id,
                "agent_id": agent_id,
                "ok": len(succeeded_tasks),
                "skip": len(task_inputs) - len(succeeded_tasks),
                "average_score": overall_average,
            },
        )

        now = timestamp or datetime.now()
        summary = UserEvaluationScore(
            user_id=user_id,
            agent_id=agent_id,
            generated_at=now.isoformat(timespec="seconds"),
            overall_average_score=overall_average,
            overall_aggregation=overall_aggregation,
            tasks=succeeded_tasks,
        )
        if not write_results:
            return summary, []
        return summary, self._write_results(summary, now)

    def _load_task_inputs(
        self,
        user_id: str,
        trace_dir_by_task_id: dict[str, Path],
        *,
        task_ids: list[str] | None = None,
        followup_turn_styles_by_task_id: dict[str, list[FollowupTurnStyle]] | None = None,
    ) -> tuple[str, list[TaskEvaluationInput]]:
        profile, episode, tasks = self.repository.load_user(user_id)
        selected_task_ids = [str(task_id).strip() for task_id in (task_ids or []) if str(task_id).strip()]
        if selected_task_ids:
            selected_set = set(selected_task_ids)
            missing = [task_id for task_id in selected_task_ids if task_id not in tasks]
            if missing:
                raise KeyError(f"Unknown task_id: {missing}")
            ordered_task_ids = [task_id for task_id in episode.task_order if task_id in tasks and task_id in selected_set]
            ordered_task_ids.extend(
                task_id for task_id in selected_task_ids if task_id in tasks and task_id not in ordered_task_ids
            )
        else:
            ordered_task_ids = [task_id for task_id in episode.task_order if task_id in tasks] or sorted(tasks.keys())
        for task_id in sorted(task_id for task_id in trace_dir_by_task_id if task_id not in tasks):
            logger.warning("Ignoring history with unknown task_id user_id={} task_id={}", user_id, task_id)
        depends_on_by_task_id = load_depends_on_by_task_id(
            user_id=user_id,
            episode_tasks=episode.raw.get("tasks"),
            ordered_task_ids=ordered_task_ids,
        )
        if selected_task_ids:
            ordered_task_id_set = set(ordered_task_ids)
            depends_on_by_task_id = {
                task_id: [
                    depends_on_task_id
                    for depends_on_task_id in depends_on_task_ids
                    if depends_on_task_id in ordered_task_id_set
                ]
                for task_id, depends_on_task_ids in depends_on_by_task_id.items()
            }
        overall_groups_by_task_id = build_task_overall_groups(
            ordered_task_ids=ordered_task_ids,
            depends_on_by_task_id=depends_on_by_task_id,
        )

        task_inputs: list[TaskEvaluationInput] = []
        for task_id in ordered_task_ids:
            history_dir = trace_dir_by_task_id.get(task_id)
            if history_dir is None:
                raise FileNotFoundError(
                    f"trace directory missing for user_id={user_id} task_id={task_id} (expected exact task_id match)"
                )
            criteria: list[TaskCriterion] = []
            for item in tasks[task_id].objectives:
                criterion_text = str(item.get("criterion", "")).strip()
                if not criterion_text:
                    continue
                evaluation = str(item.get("evaluation", "llm")).strip() or "llm"
                if evaluation != "llm":
                    raise ValueError(
                        f"Unsupported objective evaluation mode user_id={user_id} task_id={task_id}: {evaluation!r}"
                    )
                criteria.append(
                    TaskCriterion(
                        criterion=criterion_text,
                        weight=float(item.get("weight", 1)),
                        evaluation=evaluation,
                    )
                )
            tools_evaluation_path = tasks[task_id].tools_evaluation_path
            if not criteria and tools_evaluation_path is None:
                logger.warning(
                    "Skipping evaluation task with empty criteria user_id={} task_id={}",
                    user_id,
                    task_id,
                )
                continue
            task_inputs.append(
                TaskEvaluationInput(
                    task_id=task_id,
                    title=tasks[task_id].title,
                    history_dir=history_dir,
                    hidden_intents_xml=format_hidden_intents_xml(tasks[task_id].hidden_intents),
                    criteria=criteria,
                    followup_turn_styles=list((followup_turn_styles_by_task_id or {}).get(task_id, [])),
                    tool_trace_specs=list(tasks[task_id].tool_trace_specs),
                    tools_evaluation_path=tools_evaluation_path,
                    overall_group=overall_groups_by_task_id[task_id],
                )
            )
        return profile.role_text, task_inputs

    async def _evaluate_task(
        self,
        *,
        user_id: str,
        user_role: str,
        task_input: TaskEvaluationInput,
        eval_log_timestamp: str | None,
    ) -> TaskEvaluationScore | None:
        started_at = perf_counter()
        activate_task_logging(task_input.task_id, session_timestamp=eval_log_timestamp)
        try:
            criteria = list(task_input.criteria)
            tools_runtime: ToolScriptRuntime | None = None
            if task_input.tools_evaluation_path is not None:
                tools_runtime = self._load_tools_runtime(
                    task_id=task_input.task_id,
                    script_path=task_input.tools_evaluation_path,
                )
                criteria.extend(
                    TaskCriterion(
                        criterion=f"[tools] {key}",
                        weight=1.0,
                        evaluation="tool_script",
                        tool_key=key,
                    )
                    for key in tools_runtime.checklist_keys
                )
            if not criteria:
                logger.warning(
                    "Skipping evaluation task with empty criteria user_id={} task_id={}",
                    user_id,
                    task_input.task_id,
                )
                return None
            turn_paths = self._load_turn_histories(task_input.history_dir)
            turn_evaluations = await asyncio.gather(
                *(
                    self._evaluate_turn(
                        user_id=user_id,
                        user_role=user_role,
                        hidden_intents_xml=task_input.hidden_intents_xml,
                        criteria=criteria,
                        tools_runtime=tools_runtime,
                        allowed_tool_names=(
                            {spec.tool_name for spec in task_input.tool_trace_specs}
                            if task_input.tool_trace_specs
                            else None
                        ),
                        eval_log_timestamp=eval_log_timestamp,
                        history_dir=task_input.history_dir,
                        task_id=task_input.task_id,
                        turn_index=turn_index,
                        history_path=history_path,
                    )
                    for turn_index, history_path in turn_paths
                )
            )
            turn_evaluations = sorted(turn_evaluations, key=lambda item: item.turn_index)
            criterion_scores = self._merge_turn_scores(criteria, turn_evaluations)
            total_weight = sum(item.weight for item in criterion_scores)
            average_score = (
                sum(item.weighted_value for item in criterion_scores) / total_weight
                if total_weight > 0
                else 0.0
            )
            yes_count = sum(item.value for item in criterion_scores)
            logger.info(
                "Checklist evaluation finished user={} task={} avg={:.3f} yes={} no={} t={:.2f}s",
                user_id,
                task_input.task_id,
                average_score,
                yes_count,
                len(criterion_scores) - yes_count,
                perf_counter() - started_at,
                data={
                    "user_id": user_id,
                    "task_id": task_input.task_id,
                    "turn_count": len(turn_evaluations),
                    "average_score": average_score,
                    "yes_count": yes_count,
                    "no_count": len(criterion_scores) - yes_count,
                },
            )
            return TaskEvaluationScore(
                task_id=task_input.task_id,
                title=task_input.title,
                history_dir=task_input.history_dir,
                criterion_scores=criterion_scores,
                average_score=average_score,
                turn_evaluations=turn_evaluations,
                overall_group_task_ids=list(task_input.overall_group.group_task_ids),
                overall_group_size=task_input.overall_group.group_size,
                overall_weight=task_input.overall_group.weight,
            )
        except (ValueError, FileNotFoundError) as exc:
            logger.error(
                "Checklist evaluation failed user={} task={} attempts={} reason={}",
                user_id,
                task_input.task_id,
                self.parse_retries,
                str(exc),
                data={"user_id": user_id, "task_id": task_input.task_id, "attempts": self.parse_retries},
            )
            return None
        finally:
            complete_task_logging(task_input.task_id)

    async def _evaluate_turn(
        self,
        *,
        user_id: str,
        user_role: str,
        hidden_intents_xml: str,
        criteria: list[TaskCriterion],
        tools_runtime: ToolScriptRuntime | None,
        allowed_tool_names: set[str],
        eval_log_timestamp: str | None,
        history_dir: Path,
        task_id: str,
        turn_index: int,
        history_path: Path,
    ) -> TurnEvaluationScore:
        history = history_path.read_text(encoding="utf-8")
        requires_tool_scoring = any(item.evaluation == "tool_script" for item in criteria)
        turn_data = (
            self._load_turn_data_for_index(
                history_dir,
                turn_index,
                eval_log_timestamp=eval_log_timestamp,
            )
            if requires_tool_scoring
            else {}
        )
        criterion_scores, evaluation_prompt, raw_responses, tools_evaluation = await self._score_turn_criteria(
            user_role=user_role,
            hidden_intents_xml=hidden_intents_xml,
            history=history,
            criteria=criteria,
            tools_runtime=tools_runtime,
            allowed_tool_names=allowed_tool_names,
            turn_data=turn_data,
            user_id=user_id,
            task_id=task_id,
            turn_index=turn_index,
        )
        total_weight = sum(item.weight for item in criterion_scores)
        average_score = (
            sum(item.weighted_value for item in criterion_scores) / total_weight
            if total_weight > 0
            else 0.0
        )
        return TurnEvaluationScore(
            turn_index=turn_index,
            history_path=history_path,
            evaluation_prompt=evaluation_prompt,
            llm_raw_responses=raw_responses,
            criterion_scores=criterion_scores,
            average_score=average_score,
            tools_evaluation=tools_evaluation,
        )

    async def _score_turn_criteria(
        self,
        *,
        user_role: str,
        hidden_intents_xml: str,
        history: str,
        criteria: list[TaskCriterion],
        tools_runtime: ToolScriptRuntime | None,
        allowed_tool_names: set[str],
        turn_data: dict[str, Any],
        user_id: str,
        task_id: str,
        turn_index: int,
    ) -> tuple[list[CriterionScore], str, list[str], dict[str, Any]]:
        text_criteria = [
            (idx, item)
            for idx, item in enumerate(criteria, start=1)
            if item.evaluation == "llm"
        ]
        text_scores: list[CriterionScore] = []
        evaluation_prompt = ""
        raw_responses: list[str] = []
        if text_criteria:
            text_scores, evaluation_prompt, raw_responses = await self._score_task_criteria(
                user_role=user_role,
                hidden_intents_xml=hidden_intents_xml,
                history=history,
                criteria=[(item.criterion, item.weight) for _, item in text_criteria],
                user_id=user_id,
                task_id=task_id,
                turn_index=turn_index,
                retry_limit=self.parse_retries,
            )

        text_iter = iter(text_scores)
        tool_scores_by_key: dict[str, int] = {}
        tools_evaluation: dict[str, Any] = {}
        if tools_runtime is not None and any(item.evaluation == "tool_script" for item in criteria):
            tool_scores_by_key, tools_evaluation = tools_runtime.score_turn(
                tools_history=collect_tool_history(turn_data, allowed_tool_names=allowed_tool_names),
                user_id=user_id,
                task_id=task_id,
                turn_index=turn_index,
            )
        turn_scores: list[CriterionScore] = []
        for index, criterion in enumerate(criteria, start=1):
            if criterion.evaluation == "llm":
                parsed = next(text_iter)
                turn_scores.append(
                    CriterionScore(
                        index=index,
                        criterion=criterion.criterion,
                        weight=criterion.weight,
                        score=parsed.score,
                        value=parsed.value,
                    )
                )
                continue

            if criterion.evaluation != "tool_script":
                raise ValueError(f"unsupported criterion evaluation mode: {criterion.evaluation}")
            score = "YES" if tool_scores_by_key.get(str(criterion.tool_key), 0) == 1 else "NO"
            turn_scores.append(
                CriterionScore(
                    index=index,
                    criterion=criterion.criterion,
                    weight=criterion.weight,
                    score=score,
                    value=1 if score == "YES" else 0,
                )
            )
        return turn_scores, evaluation_prompt, raw_responses, tools_evaluation

    async def _score_task_criteria(
        self,
        *,
        user_role: str,
        hidden_intents_xml: str,
        history: str,
        criteria: list[tuple[str, float]],
        user_id: str,
        task_id: str,
        turn_index: int | None = None,
        retry_limit: int | None = None,
    ) -> tuple[list[CriterionScore], str, list[str]]:
        prompt = build_criterion_scorer_prompt(
            role=user_role,
            hidden_intents_xml=hidden_intents_xml,
            history=history,
            criteria=[item[0] for item in criteria],
        )
        raw_responses: list[str] = []
        resolved_scores_by_index: dict[int, CriterionScore] = {}
        last_error: ValueError | None = None
        last_attempt_was_parseable = False
        retry_limit = DEFAULT_PARSE_RETRIES if retry_limit is None else int(retry_limit)
        for attempt in range(1, retry_limit + 1):
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            logger.llm_call(prompt=prompt, response=response.content)
            raw_responses.append(response.content)
            try:
                parsed_attempt = self._parse_scores_attempt(response.content, criteria)
            except ValueError as exc:
                last_error = exc
                last_attempt_was_parseable = False
                if attempt < retry_limit:
                    logger.warning(
                        "Checklist evaluation retry user={} task={} turn={} attempt={}/{} reason={}",
                        user_id,
                        task_id,
                        turn_index if turn_index is not None else "-",
                        attempt,
                        retry_limit,
                        str(exc),
                        data={
                            "user_id": user_id,
                            "task_id": task_id,
                            "turn_index": turn_index,
                            "attempt": attempt,
                            "retry_limit": retry_limit,
                        },
                    )
                continue

            last_attempt_was_parseable = True
            for index, score in parsed_attempt.parsed_scores_by_index.items():
                resolved_scores_by_index.setdefault(index, score)

            unresolved_indexes = [
                index for index in range(1, len(criteria) + 1) if index not in resolved_scores_by_index
            ]
            if not unresolved_indexes:
                return [resolved_scores_by_index[index] for index in range(1, len(criteria) + 1)], prompt, raw_responses

            if attempt < retry_limit:
                logger.warning(
                    "Checklist evaluation retry user={} task={} turn={} attempt={}/{} reason={}",
                    user_id,
                    task_id,
                    turn_index if turn_index is not None else "-",
                    attempt,
                    retry_limit,
                    f"criterion mismatch unresolved_indexes={unresolved_indexes}",
                    data={
                        "user_id": user_id,
                        "task_id": task_id,
                        "turn_index": turn_index,
                        "attempt": attempt,
                        "retry_limit": retry_limit,
                        "unresolved_indexes": list(unresolved_indexes),
                    },
                )

        if last_attempt_was_parseable:
            unresolved_indexes = [
                index for index in range(1, len(criteria) + 1) if index not in resolved_scores_by_index
            ]
            if unresolved_indexes:
                logger.warning(
                    "Checklist evaluation defaulting unresolved mismatched criteria to NO user={} task={} turn={} indexes={}",
                    user_id,
                    task_id,
                    turn_index if turn_index is not None else "-",
                    unresolved_indexes,
                    data={
                        "user_id": user_id,
                        "task_id": task_id,
                        "turn_index": turn_index,
                        "unresolved_indexes": list(unresolved_indexes),
                    },
                )
                for index in unresolved_indexes:
                    criterion, weight = criteria[index - 1]
                    resolved_scores_by_index[index] = CriterionScore(
                        index=index,
                        criterion=criterion,
                        weight=weight,
                        score="NO",
                        value=0,
                    )
            return [resolved_scores_by_index[index] for index in range(1, len(criteria) + 1)], prompt, raw_responses

        raise ValueError(
            f"failed to parse criterion scores after {retry_limit} attempts "
            f"user_id={user_id} task_id={task_id} turn_index={turn_index}: {last_error}"
        )

    def _load_turn_histories(self, history_dir: Path) -> list[tuple[int, Path]]:
        if not history_dir.is_dir():
            raise FileNotFoundError(f"trace history directory not found: {history_dir}")
        indexed: list[tuple[int, Path]] = []
        for path in history_dir.iterdir():
            if not path.is_file():
                continue
            match = TRACE_TURN_FILENAME_PATTERN.match(path.name)
            if match is None:
                continue
            indexed.append((int(match.group(1)), path))
        indexed.sort(key=lambda item: item[0])
        if not indexed:
            raise FileNotFoundError(f"trace turn files not found under: {history_dir}")
        return indexed

    def _load_turn_data_for_index(
        self,
        history_dir: Path,
        turn_index: int,
        *,
        eval_log_timestamp: str | None,
    ) -> dict[str, Any]:
        trace_logs_dir = history_dir / "trace_logs"
        if not trace_logs_dir.is_dir():
            raise FileNotFoundError(f"trace logs directory not found: {trace_logs_dir}")
        if not eval_log_timestamp:
            raise FileNotFoundError(
                f"eval trace snapshot timestamp required to load turn data under {trace_logs_dir}"
            )
        latest_session = trace_logs_dir / eval_log_timestamp
        if not latest_session.is_dir():
            raise FileNotFoundError(
                f"trace session directory not found for eval timestamp={eval_log_timestamp} under {trace_logs_dir}"
            )
        turn_paths = sorted(
            [
                path
                for path in latest_session.iterdir()
                if path.is_file() and path.name.startswith("turn_") and path.suffix == ".json"
            ],
            key=lambda item: self._normalize_turn_log_sort_key(item.name),
        )
        if turn_index < 1 or turn_index > len(turn_paths):
            raise FileNotFoundError(
                f"turn log not found for turn_index={turn_index} under {latest_session}"
            )
        turn_path = turn_paths[turn_index - 1]
        with turn_path.open("r", encoding="utf-8") as handle:
            parsed = json.load(handle)
        if not isinstance(parsed, dict):
            raise ValueError(f"invalid turn log payload in {turn_path}: expected object")
        return parsed

    @staticmethod
    def _normalize_turn_log_sort_key(filename: str) -> tuple[int, str]:
        if not filename.startswith("turn_") or not filename.endswith(".json"):
            return 10**18, filename
        stem = filename[5:-5]
        if stem.isdigit():
            return int(stem), filename
        compact = stem.replace("_", "")
        if compact.isdigit():
            return int(compact), filename
        return 10**18, filename

    @staticmethod
    def _merge_turn_scores(
        criteria: list[TaskCriterion],
        turn_evaluations: list[TurnEvaluationScore],
    ) -> list[CriterionScore]:
        aggregated: list[CriterionScore] = []
        for index, criterion in enumerate(criteria, start=1):
            is_yes = any(
                turn_eval.criterion_scores[index - 1].value == 1
                for turn_eval in turn_evaluations
                if len(turn_eval.criterion_scores) >= index
            )
            score = "YES" if is_yes else "NO"
            aggregated.append(
                CriterionScore(
                    index=index,
                    criterion=criterion.criterion,
                    weight=criterion.weight,
                    score=score,
                    value=1 if is_yes else 0,
                )
            )
        return aggregated

    def _load_tools_runtime(
        self,
        *,
        task_id: str,
        script_path: Path,
    ) -> ToolScriptRuntime:
        module_name = self._build_tools_module_name(task_id=task_id, script_path=script_path)
        module = self._load_tools_module(module_name=module_name, script_path=script_path)
        score_fn = getattr(module, "score", None)
        if not callable(score_fn):
            raise ValueError(
                f"tools evaluation script must define callable score(tools_history): {script_path}"
            )
        checklist_keys, _ = _normalize_initial_scores(
            payload=score_fn([]),
            script_path=script_path,
        )
        script_code = script_path.read_text(encoding="utf-8")
        return ToolScriptRuntime(
            module_name=module_name,
            script_path=script_path,
            script_code=script_code,
            score_fn=score_fn,
            checklist_keys=checklist_keys,
        )

    @staticmethod
    def _build_tools_module_name(*, task_id: str, script_path: Path) -> str:
        stem = re.sub(r"[^a-zA-Z0-9_]", "_", script_path.stem)
        return f"bench_tools_eval_{task_id}_{stem}_{abs(hash(str(script_path))) % (10**10)}"

    @staticmethod
    def _load_tools_module(*, module_name: str, script_path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"unable to load tools evaluation module: {script_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _parse_scores_attempt(
        self,
        output: str,
        criteria: list[tuple[str, float]],
    ) -> ParsedScoreAttempt:
        matches = list(CRITERION_BLOCK_PATTERN.finditer(output or ""))
        if len(matches) != len(criteria):
            raise ValueError(f"invalid block count expected={len(criteria)} got={len(matches)}")

        parsed: dict[int, CriterionScore] = {}
        mismatch_indexes: list[int] = []
        for match in matches:
            index = int(match.group("idx"))
            if index < 1 or index > len(criteria):
                raise ValueError(f"criterion index out of range: {index}")
            if index in parsed:
                raise ValueError(f"duplicate criterion index: {index}")

            expected_criterion, weight = criteria[index - 1]
            parsed_criterion = (match.group("criterion") or "").strip()
            if _normalize_xml_text(parsed_criterion) != _normalize_xml_text(expected_criterion):
                mismatch_indexes.append(index)
                continue

            score = (match.group("score") or "").strip().upper()
            if score not in {"YES", "NO"}:
                raise ValueError(f"invalid score at index {index}: {score!r}")

            parsed[index] = CriterionScore(
                index=index,
                criterion=expected_criterion,
                weight=weight,
                score=score,
                value=1 if score == "YES" else 0,
            )
        return ParsedScoreAttempt(
            parsed_scores_by_index=parsed,
            mismatch_indexes=tuple(sorted(mismatch_indexes)),
        )

    def _parse_scores(self, output: str, criteria: list[tuple[str, float]]) -> list[CriterionScore]:
        parsed_attempt = self._parse_scores_attempt(output, criteria)
        if parsed_attempt.mismatch_indexes:
            raise ValueError(f"criterion mismatch at index {parsed_attempt.mismatch_indexes[0]}")

        missing = [
            index for index in range(1, len(criteria) + 1) if index not in parsed_attempt.parsed_scores_by_index
        ]
        if missing:
            raise ValueError(f"missing criterion indexes: {missing}")
        return [parsed_attempt.parsed_scores_by_index[index] for index in range(1, len(criteria) + 1)]

    def _write_results(self, summary: UserEvaluationScore, timestamp: datetime) -> list[Path]:
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        output_paths: list[Path] = []
        for task_score in summary.tasks:
            payload = json.dumps(
                {
                    "user_id": summary.user_id,
                    "agent_id": summary.agent_id,
                    "generated_at": summary.generated_at,
                    "overall_average_score": summary.overall_average_score,
                    "overall_aggregation": summary.overall_aggregation,
                    "task_count": len(summary.tasks),
                    "task": task_score.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
            output_dir = self.results_root / summary.agent_id / summary.user_id / task_score.task_id / "eval" / "results"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{timestamp_str}_result.json"
            output_path.write_text(payload, encoding="utf-8")
            output_paths.append(output_path)
        return output_paths
