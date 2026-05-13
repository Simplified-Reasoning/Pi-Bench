from __future__ import annotations

import asyncio
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from src.data import UserDataRepository
from src.utils import activate_task_logging, complete_task_logging, get_logger
from .overall_aggregation import (
    TaskOverallGroup,
    build_task_overall_groups,
    compute_weighted_overall_average,
    load_depends_on_by_task_id,
)
from .trace_history import FollowupTurnStyle, IntentJudgeTurn

logger = get_logger("Bench.Evaluation.Proactiveness").profile("eval")
stage_logger = logger.profile("eval_stage")

TURN_SCALE = 5.0
TURN_DECAY_SHAPE = 0.5

MESSAGE_LENGTH_BASE = 20
MESSAGE_LENGTH_SCALE = 150.0
MESSAGE_LENGTH_DECAY_SHAPE = 2.0


@dataclass(frozen=True)
class ProactivenessTaskScore:
    task_id: str
    title: str
    final_turn_path: Path
    user_turn_count: int
    user_message_lengths: list[int]
    turn_score: float
    message_length_scores: list[float]
    average_message_length_score: float
    intent_judge_turns: list["ProactivenessIntentJudgeTurn"]
    inferred_intent_indexes: list[int]
    matched_intent_indexes: list[int]
    covered_intent_indexes: list[int]
    covered_intent_count: int
    total_hidden_intent_count: int
    independent_average_score: float
    average_score: float
    include_in_overall: bool
    overall_group_task_ids: list[str]
    overall_group_size: int
    overall_weight: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "final_turn_path": str(self.final_turn_path),
            "user_turn_count": self.user_turn_count,
            "user_message_lengths": list(self.user_message_lengths),
            "turn_score": self.turn_score,
            "message_length_scores": list(self.message_length_scores),
            "average_message_length_score": self.average_message_length_score,
            "intent_judge_turns": [item.to_dict() for item in self.intent_judge_turns],
            "inferred_intent_indexes": list(self.inferred_intent_indexes),
            "matched_intent_indexes": list(self.matched_intent_indexes),
            "covered_intent_indexes": list(self.covered_intent_indexes),
            "covered_intent_count": self.covered_intent_count,
            "total_hidden_intent_count": self.total_hidden_intent_count,
            "independent_average_score": self.independent_average_score,
            "average_score": self.average_score,
            "include_in_overall": self.include_in_overall,
            "overall_group_task_ids": list(self.overall_group_task_ids),
            "overall_group_size": self.overall_group_size,
            "overall_weight": self.overall_weight,
        }


@dataclass(frozen=True)
class ProactivenessUserScore:
    user_id: str
    agent_id: str
    generated_at: str
    overall_average_score: float | None
    overall_aggregation: dict[str, Any]
    tasks: list[ProactivenessTaskScore]

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
class ProactivenessTaskInput:
    task_id: str
    title: str
    turn_paths: list[Path]
    followup_turn_styles: list[FollowupTurnStyle]
    intent_judge_turns: list[IntentJudgeTurn]
    total_hidden_intent_count: int
    depends_on_task_inputs: list["ProactivenessDependencyInput"]
    include_in_overall: bool
    overall_group: TaskOverallGroup


@dataclass(frozen=True)
class ProactivenessDependencyInput:
    task_id: str
    intent_judge_turns: list[IntentJudgeTurn]
    total_hidden_intent_count: int


@dataclass(frozen=True)
class FollowupUserTurn:
    assistant_turn_index: int
    message_length: int


@dataclass(frozen=True)
class ProactivenessIntentJudgeTurn:
    assistant_turn_index: int
    inferred_indexes: list[int]
    matched_indexes: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "assistant_turn_index": self.assistant_turn_index,
            "inferred_indexes": list(self.inferred_indexes),
            "matched_indexes": list(self.matched_indexes),
        }


class ProactivenessEvaluator:
    def __init__(
        self,
        *,
        repository: UserDataRepository | None = None,
        data_root: Path = Path("data"),
    ) -> None:
        self.repository = repository or UserDataRepository(data_root=str(data_root))

    async def evaluate_user(
        self,
        *,
        user_id: str,
        agent_id: str,
        turn_paths_by_task_id: dict[str, list[Path]],
        task_ids: list[str] | None = None,
        followup_turn_styles_by_task_id: dict[str, list[FollowupTurnStyle]] | None = None,
        intent_judge_turns_by_task_id: dict[str, list[IntentJudgeTurn]] | None = None,
        timestamp: datetime | None = None,
        eval_log_timestamp: str | None = None,
    ) -> ProactivenessUserScore:
        task_inputs = self._load_task_inputs(
            user_id,
            turn_paths_by_task_id,
            task_ids=task_ids,
            followup_turn_styles_by_task_id=followup_turn_styles_by_task_id,
            intent_judge_turns_by_task_id=intent_judge_turns_by_task_id,
        )
        task_results = await asyncio.gather(
            *(
                asyncio.to_thread(
                    self._evaluate_task,
                    user_id=user_id,
                    task_input=task_input,
                    eval_log_timestamp=eval_log_timestamp,
                )
                for task_input in task_inputs
            )
        )
        succeeded_tasks = [item for item in task_results if item is not None]
        tasks_in_overall = [item for item in succeeded_tasks if item.include_in_overall]
        overall_average, overall_aggregation = compute_weighted_overall_average(
            [
                (
                    item.average_score,
                    next(task_input.overall_group for task_input in task_inputs if task_input.task_id == item.task_id),
                )
                for item in tasks_in_overall
            ]
        )
        average_text = f"{overall_average:.3f}" if overall_average is not None else "n/a"
        stage_logger.info(
            "user_proactiveness done user={} agent={} ok={} skip={} avg={}",
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
        return ProactivenessUserScore(
            user_id=user_id,
            agent_id=agent_id,
            generated_at=now.isoformat(timespec="seconds"),
            overall_average_score=overall_average,
            overall_aggregation=overall_aggregation,
            tasks=succeeded_tasks,
        )

    def _load_task_inputs(
        self,
        user_id: str,
        turn_paths_by_task_id: dict[str, list[Path]],
        *,
        task_ids: list[str] | None = None,
        followup_turn_styles_by_task_id: dict[str, list[FollowupTurnStyle]] | None = None,
        intent_judge_turns_by_task_id: dict[str, list[IntentJudgeTurn]] | None = None,
    ) -> list[ProactivenessTaskInput]:
        _, episode, tasks = self.repository.load_user(user_id)
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
        for task_id in sorted(task_id for task_id in turn_paths_by_task_id if task_id not in tasks):
            logger.warning("Ignoring turns with unknown task_id user_id={} task_id={}", user_id, task_id)
        task_order_indexes = {
            task_id: idx
            for idx, task_id in enumerate(ordered_task_ids)
        }
        criteria_by_task_id = {
            task_id: (
                [
                    str(item.get("criterion", "")).strip()
                    for item in tasks[task_id].objectives
                    if str(item.get("criterion", "")).strip()
                ]
                + (
                    ["[tools] from tools_evaluation_path"]
                    if tasks[task_id].tools_evaluation_path is not None
                    else []
                )
            )
            for task_id in ordered_task_ids
        }
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
        for task_id in ordered_task_ids:
            self._validate_dependency_contract(
                user_id=user_id,
                task_id=task_id,
                depends_on_task_ids=depends_on_by_task_id.get(task_id, []),
                criteria_by_task_id=criteria_by_task_id,
                task_order_indexes=task_order_indexes,
            )
        overall_groups_by_task_id = build_task_overall_groups(
            ordered_task_ids=ordered_task_ids,
            depends_on_by_task_id=depends_on_by_task_id,
        )

        task_inputs: list[ProactivenessTaskInput] = []
        for task_id in ordered_task_ids:
            turn_paths = turn_paths_by_task_id.get(task_id)
            if not turn_paths:
                raise FileNotFoundError(
                    f"turn history missing for user_id={user_id} task_id={task_id} (expected exact task_id match)"
                )
            criteria = criteria_by_task_id[task_id]
            depends_on_task_ids = depends_on_by_task_id.get(task_id, [])
            task_inputs.append(
                ProactivenessTaskInput(
                    task_id=task_id,
                    title=tasks[task_id].title,
                    turn_paths=turn_paths,
                    followup_turn_styles=list((followup_turn_styles_by_task_id or {}).get(task_id, [])),
                    intent_judge_turns=list((intent_judge_turns_by_task_id or {}).get(task_id, [])),
                    total_hidden_intent_count=len(tasks[task_id].hidden_intents),
                    depends_on_task_inputs=[
                        ProactivenessDependencyInput(
                            task_id=depends_on_task_id,
                            intent_judge_turns=list(
                                (intent_judge_turns_by_task_id or {}).get(depends_on_task_id, [])
                            ),
                            total_hidden_intent_count=len(tasks[depends_on_task_id].hidden_intents),
                        )
                        for depends_on_task_id in depends_on_task_ids
                    ],
                    include_in_overall=bool(criteria),
                    overall_group=overall_groups_by_task_id[task_id],
                )
            )
        return task_inputs

    def _validate_dependency_contract(
        self,
        *,
        user_id: str,
        task_id: str,
        depends_on_task_ids: list[str],
        criteria_by_task_id: dict[str, list[str]],
        task_order_indexes: dict[str, int],
    ) -> None:
        if depends_on_task_ids and not criteria_by_task_id.get(task_id):
            raise ValueError(
                f"invalid depends_on contract user_id={user_id} task_id={task_id}: task with depends_on must have non-empty criteria"
            )
        if not depends_on_task_ids:
            return
        seen_depends_on: set[str] = set()
        task_index = task_order_indexes[task_id]
        for dep_task_id in depends_on_task_ids:
            if dep_task_id in seen_depends_on:
                raise ValueError(
                    f"invalid depends_on contract user_id={user_id} task_id={task_id}: duplicate dependency {dep_task_id}"
                )
            seen_depends_on.add(dep_task_id)
            if dep_task_id == task_id:
                raise ValueError(
                    f"invalid depends_on contract user_id={user_id} task_id={task_id}: self dependency is not allowed"
                )
            dep_task_index = task_order_indexes.get(dep_task_id)
            if dep_task_index is None:
                raise ValueError(
                    f"invalid depends_on contract user_id={user_id} task_id={task_id}: unknown dependency {dep_task_id}"
                )
            if dep_task_index >= task_index:
                raise ValueError(
                    f"invalid depends_on contract user_id={user_id} task_id={task_id}: dependency {dep_task_id} must be earlier in episode order"
                )
            if criteria_by_task_id.get(dep_task_id):
                raise ValueError(
                    f"invalid depends_on contract user_id={user_id} task_id={task_id}: dependency {dep_task_id} must have empty criteria"
                )

    def _evaluate_task(
        self,
        *,
        user_id: str,
        task_input: ProactivenessTaskInput,
        eval_log_timestamp: str | None,
    ) -> ProactivenessTaskScore | None:
        started_at = perf_counter()
        activate_task_logging(task_input.task_id, session_timestamp=eval_log_timestamp)
        try:
            # logger.info(
            #     "Proactiveness evaluation started user={} task={}",
            #     user_id,
            #     task_input.task_id,
            #     data={"user_id": user_id, "task_id": task_input.task_id},
            # )
            final_turn_path = task_input.turn_paths[-1]
            messages = self._load_messages(final_turn_path)
            followup_turns = self._extract_followup_user_turns(messages)
            matched_turn_indexes: set[int] = set()
            try:
                matched_turn_indexes = self._resolve_matched_turn_indexes(
                    followup_turns=followup_turns,
                    followup_turn_styles=task_input.followup_turn_styles,
                    final_turn_path=final_turn_path,
                )
            except ValueError as exc:
                logger.warning(
                    "Legacy proactiveness alignment failed user={} task={} reason={}",
                    user_id,
                    task_input.task_id,
                    str(exc),
                    data={"user_id": user_id, "task_id": task_input.task_id},
                )
            user_lengths = [item.message_length for item in followup_turns]
            turn_count = len(followup_turns)
            turn_score, length_scores, average_length_score, _legacy_average_score = self._calculate_legacy_score(
                followup_turns=followup_turns,
                matched_turn_indexes=matched_turn_indexes,
            )
            coverage = self._build_intent_coverage(
                turns=task_input.intent_judge_turns,
                total_hidden_intent_count=task_input.total_hidden_intent_count,
                task_id=task_input.task_id,
            )
            independent_average_score = float(coverage["average_score"])
            average_score = self._calculate_average_score_with_dependencies(
                primary_coverage=coverage,
                depends_on_task_inputs=task_input.depends_on_task_inputs,
            )
            # Legacy formula kept for reference only; currently not used as final score:
            # legacy_average_score = average_length_score * turn_score if turn_count else 1.0

            logger.info(
                "Proactiveness evaluation finished user={} task={} avg={:.3f} turns={} len_avg={:.1f} t={:.2f}s",
                user_id,
                task_input.task_id,
                average_score,
                turn_count,
                (sum(user_lengths) / turn_count) if turn_count else 0.0,
                perf_counter() - started_at,
                data={
                    "user_id": user_id,
                    "task_id": task_input.task_id,
                    "average_score": average_score,
                    "turn_count": turn_count,
                },
            )
            return ProactivenessTaskScore(
                task_id=task_input.task_id,
                title=task_input.title,
                final_turn_path=final_turn_path,
                user_turn_count=turn_count,
                user_message_lengths=user_lengths,
                turn_score=turn_score,
                message_length_scores=length_scores,
                average_message_length_score=average_length_score,
                intent_judge_turns=coverage["turn_records"],
                inferred_intent_indexes=coverage["inferred_indexes"],
                matched_intent_indexes=coverage["matched_indexes"],
                covered_intent_indexes=coverage["covered_indexes"],
                covered_intent_count=coverage["covered_count"],
                total_hidden_intent_count=coverage["total_hidden_intent_count"],
                independent_average_score=independent_average_score,
                average_score=average_score,
                include_in_overall=task_input.include_in_overall,
                overall_group_task_ids=list(task_input.overall_group.group_task_ids),
                overall_group_size=task_input.overall_group.group_size,
                overall_weight=task_input.overall_group.weight,
            )
        except ValueError as exc:
            logger.error(
                "Proactiveness evaluation failed user={} task={} reason={}",
                user_id,
                task_input.task_id,
                str(exc),
                data={"user_id": user_id, "task_id": task_input.task_id},
            )
            return None
        finally:
            complete_task_logging(task_input.task_id)

    def _load_messages(self, final_turn_path: Path) -> list[dict[str, Any]]:
        with final_turn_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"turn file must contain a JSON object: {final_turn_path}")
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError(f"turn file messages must be a list: {final_turn_path}")
        return [message for message in messages if isinstance(message, dict)]

    def _extract_followup_user_turns(self, messages: list[dict[str, Any]]) -> list[FollowupUserTurn]:
        followup_turns: list[FollowupUserTurn] = []
        assistant_turn_index = 0
        seen_initial_user = False
        for message in messages:
            role = str(message.get("role") or "")
            if role == "assistant":
                if not self._is_assistant_tool_call_message(message):
                    assistant_turn_index += 1
                continue
            if role != "user":
                continue

            normalized = self._normalize_user_message(message.get("content"))
            if not seen_initial_user:
                seen_initial_user = True
                continue
            followup_turns.append(
                FollowupUserTurn(
                    assistant_turn_index=assistant_turn_index,
                    message_length=len(normalized),
                )
            )
        return followup_turns

    @staticmethod
    def _is_assistant_tool_call_message(message: dict[str, Any]) -> bool:
        tool_calls = message.get("tool_calls")
        return isinstance(tool_calls, list) and len(tool_calls) > 0

    def _resolve_matched_turn_indexes(
        self,
        *,
        followup_turns: list[FollowupUserTurn],
        followup_turn_styles: list[FollowupTurnStyle],
        final_turn_path: Path,
    ) -> set[int]:
        matched_turn_indexes = {
            item.assistant_turn_index
            for item in followup_turn_styles
            if item.matched_hidden_intents
        }
        if not matched_turn_indexes:
            return set()

        available_turn_indexes = {item.assistant_turn_index for item in followup_turns}
        missing_turn_indexes = sorted(matched_turn_indexes - available_turn_indexes)
        if missing_turn_indexes:
            raise ValueError(
                "followup turn styles reference missing assistant_turn_index(s) "
                f"in final turn messages {final_turn_path}: {missing_turn_indexes}"
            )
        return matched_turn_indexes

    def _calculate_legacy_score(
        self,
        *,
        followup_turns: list[FollowupUserTurn],
        matched_turn_indexes: set[int],
    ) -> tuple[float, list[float], float, float]:
        turn_count = len(followup_turns)
        turn_score = self._stretched_exponential(turn_count, scale=TURN_SCALE, shape=TURN_DECAY_SHAPE)
        length_scores = [
            1.0
            if turn.assistant_turn_index in matched_turn_indexes
            else (
                1.0
                if turn.message_length <= MESSAGE_LENGTH_BASE
                else self._stretched_exponential(
                    turn.message_length - MESSAGE_LENGTH_BASE,
                    scale=MESSAGE_LENGTH_SCALE,
                    shape=MESSAGE_LENGTH_DECAY_SHAPE,
                )
            )
            for turn in followup_turns
        ]
        average_length_score = sum(length_scores) / turn_count if turn_count else 1.0
        legacy_average_score = average_length_score * turn_score if turn_count else 1.0
        return turn_score, length_scores, average_length_score, legacy_average_score

    def _build_intent_coverage(
        self,
        *,
        turns: list[IntentJudgeTurn],
        total_hidden_intent_count: int,
        task_id: str,
    ) -> dict[str, Any]:
        if total_hidden_intent_count < 1:
            raise ValueError(f"task has no hidden intents for proactiveness scoring: {task_id}")

        inferred_indexes: list[int] = []
        matched_indexes: list[int] = []
        covered_indexes: list[int] = []
        seen_inferred: set[int] = set()
        seen_matched: set[int] = set()
        seen_covered: set[int] = set()
        turn_records: list[ProactivenessIntentJudgeTurn] = []

        for turn in turns:
            self._validate_intent_indexes(
                turn.inferred_indexes,
                total_hidden_intent_count=total_hidden_intent_count,
                field_name="inferred_indexes",
                task_id=task_id,
                assistant_turn_index=turn.assistant_turn_index,
            )
            self._validate_intent_indexes(
                turn.matched_indexes,
                total_hidden_intent_count=total_hidden_intent_count,
                field_name="matched_indexes",
                task_id=task_id,
                assistant_turn_index=turn.assistant_turn_index,
            )
            turn_records.append(
                ProactivenessIntentJudgeTurn(
                    assistant_turn_index=turn.assistant_turn_index,
                    inferred_indexes=list(turn.inferred_indexes),
                    matched_indexes=list(turn.matched_indexes),
                )
            )
            for idx in turn.inferred_indexes:
                if idx not in seen_inferred:
                    seen_inferred.add(idx)
                    inferred_indexes.append(idx)
                if idx not in seen_covered:
                    seen_covered.add(idx)
                    covered_indexes.append(idx)
            for idx in turn.matched_indexes:
                if idx not in seen_matched:
                    seen_matched.add(idx)
                    matched_indexes.append(idx)
                if idx not in seen_covered:
                    seen_covered.add(idx)
                    covered_indexes.append(idx)

        covered_count = len(covered_indexes)
        return {
            "turn_records": turn_records,
            "inferred_indexes": inferred_indexes,
            "matched_indexes": matched_indexes,
            "covered_indexes": covered_indexes,
            "covered_count": covered_count,
            "total_hidden_intent_count": total_hidden_intent_count,
            "average_score": covered_count / total_hidden_intent_count,
        }

    def _validate_intent_indexes(
        self,
        indexes: list[int],
        *,
        total_hidden_intent_count: int,
        field_name: str,
        task_id: str,
        assistant_turn_index: int,
    ) -> None:
        for idx in indexes:
            if idx < 1 or idx > total_hidden_intent_count:
                raise ValueError(
                    f"invalid {field_name} index in task={task_id} assistant_turn_index={assistant_turn_index}: {idx}"
                )

    def _calculate_average_score_with_dependencies(
        self,
        *,
        primary_coverage: dict[str, Any],
        depends_on_task_inputs: list[ProactivenessDependencyInput],
    ) -> float:
        covered_count = int(primary_coverage["covered_count"])
        total_hidden_intent_count = int(primary_coverage["total_hidden_intent_count"])
        for depends_on_input in depends_on_task_inputs:
            dependency_coverage = self._build_intent_coverage(
                turns=depends_on_input.intent_judge_turns,
                total_hidden_intent_count=depends_on_input.total_hidden_intent_count,
                task_id=depends_on_input.task_id,
            )
            covered_count += int(dependency_coverage["covered_count"])
            total_hidden_intent_count += int(dependency_coverage["total_hidden_intent_count"])
        return covered_count / total_hidden_intent_count

    def _normalize_user_message(self, content: Any) -> str:
        if content is None:
            text = ""
        elif isinstance(content, str):
            text = content
        else:
            text = json.dumps(content, ensure_ascii=False, sort_keys=True)

        if not text.startswith("[Runtime Context"):
            return text.strip()
        parts = text.split("\n\n", maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()
        return text.strip()

    @staticmethod
    def _stretched_exponential(value: float, *, scale: float, shape: float) -> float:
        if value <= 0:
            return 1.0
        return math.exp(-((value / scale) ** shape))
