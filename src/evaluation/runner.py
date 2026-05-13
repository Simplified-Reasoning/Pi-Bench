from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.data import UserDataRepository
from src.llm import LLMClient
from src.utils import safe_model_id

from .checklist_evaluator import ChecklistEvaluator, UserEvaluationScore
from .proactiveness_evaluator import ProactivenessEvaluator
from .reevaluation import load_reevaluation_inputs, log_reused_checklist_sources
from .result_writer import write_combined_task_results
from .trace_history import (
    TraceHistoryBuilder,
    collect_model_task_turn_sessions,
    generate_trace_viewer_html,
    load_task_intent_judge_turns,
    load_task_followup_turn_styles,
)
from ..utils import get_logger

logger = get_logger("Bench.Evaluation").profile("eval")
stage_logger = logger.profile("eval_stage")
result_logger = logger.profile("eval_result")


@dataclass
class TraceEvaluationResult:
    model_id: str
    user_id: str
    scoring: str
    output_dir: Path
    tasks_built: int
    users_covered: int
    checklist_evaluated_tasks: int
    proactiveness_evaluated_tasks: int
    overall_average_score: float | None
    overall_proactiveness_average_score: float | None
    score_paths: list[Path]


@dataclass
class OutputsReevaluationResult:
    model_id: str
    user_id: str
    scoring: str
    output_dir: Path
    checklist_reused_tasks: int
    proactiveness_evaluated_tasks: int
    overall_average_score: float | None
    overall_proactiveness_average_score: float | None
    score_paths: list[Path]


class TraceEvaluationRunner:
    """Build task histories and evaluate checklist criteria for one user."""

    def __init__(
        self,
        *,
        model_id: str,
        user_id: str,
        logs_dir: Path,
        workspace_dir: Path,
        config_path: Path,
        output_dir: Path,
        scoring: str,
        llm_client: LLMClient | None,
        task_ids: list[str] | None = None,
        data_root: Path = Path("data"),
    ) -> None:
        self.model_id = model_id
        self.user_id = user_id
        self.scoring = scoring
        self.logs_dir = logs_dir
        self.workspace_dir = workspace_dir
        self.config_path = config_path
        self.output_dir = output_dir
        self.data_root = data_root
        self.llm = llm_client
        self.task_ids = [str(task_id).strip() for task_id in (task_ids or []) if str(task_id).strip()]

    async def run(self) -> TraceEvaluationResult:
        stage_logger.info(
            "Trace evaluation started model_id={} user_id={}",
            self.model_id,
            self.user_id,
            data={"model_id": self.model_id, "user_id": self.user_id, "scoring": self.scoring},
        )
        now = datetime.now()
        eval_run_ts = now.strftime("%Y%m%d_%H%M%S")
        written = TraceHistoryBuilder(
            model_id=self.model_id,
            user_id=self.user_id,
            logs_dir=self.logs_dir,
            config_path=self.config_path,
            output_dir=self.output_dir,
            workspace_dir=self.workspace_dir,
            data_root=self.data_root,
        ).build(eval_timestamp=eval_run_ts)
        users = {item[0] for item in written}
        stage_logger.info(
            "Trace histories built model_id={} tasks={} users={}",
            self.model_id,
            len(written),
            len(users),
            data={"tasks_built": len(written), "users_covered": len(users)},
        )

        trace_dir_by_task_id = {
            task_id: trace_dir
            for user_id, task_id, trace_dir in written
            if user_id == self.user_id
        }
        turn_sessions_by_task_id = {
            task_id: session
            for (user_id, task_id), session in collect_model_task_turn_sessions(
                model_id=self.model_id,
                logs_dir=self.logs_dir,
                user_id=self.user_id,
            ).items()
            if user_id == self.user_id
        }
        turn_paths_by_task_id = {
            task_id: session.turn_paths for task_id, session in turn_sessions_by_task_id.items()
        }
        selected_task_ids = set(self.task_ids)
        if selected_task_ids:
            trace_dir_by_task_id = {
                task_id: trace_dir
                for task_id, trace_dir in trace_dir_by_task_id.items()
                if task_id in selected_task_ids
            }
            turn_paths_by_task_id = {
                task_id: turn_paths
                for task_id, turn_paths in turn_paths_by_task_id.items()
                if task_id in selected_task_ids
            }
        followup_turn_styles_by_task_id = {
            task_id: load_task_followup_turn_styles(
                output_dir=self.output_dir,
                model_id=self.model_id,
                user_id=self.user_id,
                task_id=task_id,
            )
            for task_id in turn_sessions_by_task_id
        }
        intent_judge_turns_by_task_id = {
            task_id: load_task_intent_judge_turns(
                output_dir=self.output_dir,
                model_id=self.model_id,
                user_id=self.user_id,
                task_id=task_id,
            )
            for task_id in turn_sessions_by_task_id
        }
        if not trace_dir_by_task_id:
            raise FileNotFoundError(
                f"no history generated for user_id={self.user_id} under model_id={self.model_id}"
            )
        explicit_none_tasks = _load_explicit_none_tasks(
            user_id=self.user_id,
            data_root=self.data_root,
            task_ids=set(trace_dir_by_task_id).union(turn_paths_by_task_id)
        )
        checklist_summary = None
        proactiveness_summary = None
        tasks: list[asyncio.Future] = []
        kinds: list[str] = []
        if self.scoring in {"checklist", "both"}:
            if self.llm is None:
                raise ValueError("evaluation llm is required when scoring includes checklist")
            tasks.append(
                ChecklistEvaluator(
                    llm_client=self.llm,
                    data_root=self.data_root,
                ).evaluate_user(
                    user_id=self.user_id,
                    agent_id=self.model_id,
                    trace_dir_by_task_id=trace_dir_by_task_id,
                    task_ids=self.task_ids or None,
                    followup_turn_styles_by_task_id=followup_turn_styles_by_task_id,
                    timestamp=now,
                    eval_log_timestamp=eval_run_ts,
                    write_results=False,
                )
            )
            kinds.append("checklist")
        if self.scoring in {"proactiveness", "both"}:
            tasks.append(
                ProactivenessEvaluator(data_root=self.data_root).evaluate_user(
                    user_id=self.user_id,
                    agent_id=self.model_id,
                    turn_paths_by_task_id=turn_paths_by_task_id,
                    task_ids=self.task_ids or None,
                    followup_turn_styles_by_task_id=followup_turn_styles_by_task_id,
                    intent_judge_turns_by_task_id=intent_judge_turns_by_task_id,
                    timestamp=now,
                    eval_log_timestamp=eval_run_ts,
                )
            )
            kinds.append("proactiveness")

        for kind, evaluation_result in zip(kinds, await asyncio.gather(*tasks)):
            if kind == "checklist":
                checklist_summary, _ = evaluation_result
            else:
                proactiveness_summary = evaluation_result

        score_paths = write_combined_task_results(
            checklist_summary=checklist_summary,
            proactiveness_summary=proactiveness_summary,
            results_root=self.output_dir,
            timestamp=now,
            explicit_none_tasks=explicit_none_tasks,
        )
        user_root_dir = self.output_dir / safe_model_id(self.model_id) / self.user_id
        html_path = generate_trace_viewer_html(
            model_id=self.model_id,
            user_id=self.user_id,
            user_root_dir=user_root_dir,
        )
        stage_logger.info(
            "Trace viewer html generated model_id={} user_id={} html_path={}",
            self.model_id,
            self.user_id,
            html_path,
            data={
                "model_id": self.model_id,
                "user_id": self.user_id,
                "html_path": str(html_path),
            },
        )

        result = TraceEvaluationResult(
            model_id=self.model_id,
            user_id=self.user_id,
            scoring=self.scoring,
            output_dir=self.output_dir / safe_model_id(self.model_id) / self.user_id,
            tasks_built=len(written),
            users_covered=len(users),
            checklist_evaluated_tasks=len(checklist_summary.tasks) if checklist_summary is not None else 0,
            proactiveness_evaluated_tasks=len(proactiveness_summary.tasks) if proactiveness_summary is not None else 0,
            overall_average_score=(
                checklist_summary.overall_average_score
                if checklist_summary is not None and checklist_summary.overall_average_score is not None
                else (
                    proactiveness_summary.overall_average_score
                    if proactiveness_summary is not None
                    else None
                )
            ),
            overall_proactiveness_average_score=(
                proactiveness_summary.overall_average_score if proactiveness_summary is not None else None
            ),
            score_paths=score_paths,
        )
        result_logger.block(
            "Trace evaluation finished",
            f"model_id={result.model_id} user_id={result.user_id} scoring={result.scoring}",
            f"tasks_built={result.tasks_built} users_covered={result.users_covered}",
            f"overall_avg={_format_optional_score(result.overall_average_score)}",
            (
                f"checklist_tasks={result.checklist_evaluated_tasks} "
                f"checklist_avg={_format_optional_score(checklist_summary.overall_average_score)}"
                if checklist_summary is not None
                else f"checklist_tasks={result.checklist_evaluated_tasks} checklist_avg=n/a"
            ),
            (
                "proactiveness_tasks="
                f"{result.proactiveness_evaluated_tasks} "
                f"proactiveness_avg={_format_optional_score(result.overall_proactiveness_average_score)}"
                if result.overall_proactiveness_average_score is not None
                else f"proactiveness_tasks={result.proactiveness_evaluated_tasks} proactiveness_avg=n/a"
            ),
            f"score_files={len(result.score_paths)} output_dir={result.output_dir}",
            *[f"score_path={path}" for path in result.score_paths],
            data={
                "output_dir": str(result.output_dir),
                "trace_logs_dir": str(self.logs_dir),
                "workspace_dir": str(self.workspace_dir),
                "tasks_built": result.tasks_built,
                "users_covered": result.users_covered,
                "checklist_evaluated_tasks": result.checklist_evaluated_tasks,
                "proactiveness_evaluated_tasks": result.proactiveness_evaluated_tasks,
                "overall_average_score": result.overall_average_score,
                "overall_proactiveness_average_score": result.overall_proactiveness_average_score,
                "score_paths": [str(path) for path in result.score_paths],
                "html_path": str(html_path),
            },
        )
        return result


class OutputsReevaluationRunner:
    def __init__(
        self,
        *,
        model_id: str,
        user_id: str,
        output_dir: Path,
        scoring: str,
        source_eval_timestamp: str | None,
        data_root: Path = Path("data"),
    ) -> None:
        self.model_id = model_id
        self.user_id = user_id
        self.output_dir = output_dir
        self.scoring = scoring
        self.source_eval_timestamp = source_eval_timestamp
        self.data_root = data_root

    async def run(self) -> OutputsReevaluationResult:
        stage_logger.info(
            "Outputs reeval started model_id={} user_id={} scoring={}",
            self.model_id,
            self.user_id,
            self.scoring,
            data={
                "model_id": self.model_id,
                "user_id": self.user_id,
                "scoring": self.scoring,
                "source_eval_timestamp": self.source_eval_timestamp,
            },
        )
        (
            checklist_summary,
            source_records,
            turn_paths_by_task_id,
            followup_turn_styles_by_task_id,
            intent_judge_turns_by_task_id,
            explicit_none_tasks,
        ) = load_reevaluation_inputs(
            output_dir=self.output_dir,
            model_id=self.model_id,
            user_id=self.user_id,
            source_eval_timestamp=self.source_eval_timestamp,
            data_root=self.data_root,
        )
        log_reused_checklist_sources(source_records)

        now = datetime.now()
        eval_run_ts = now.strftime("%Y%m%d_%H%M%S")
        checklist_summary = UserEvaluationScore(
            user_id=checklist_summary.user_id,
            agent_id=checklist_summary.agent_id,
            generated_at=now.isoformat(timespec="seconds"),
            overall_average_score=checklist_summary.overall_average_score,
            overall_aggregation=dict(checklist_summary.overall_aggregation),
            tasks=list(checklist_summary.tasks),
        )

        proactiveness_summary = None
        if self.scoring == "both":
            proactiveness_summary = await ProactivenessEvaluator(data_root=self.data_root).evaluate_user(
                user_id=self.user_id,
                agent_id=self.model_id,
                turn_paths_by_task_id=turn_paths_by_task_id,
                task_ids=self.task_ids or None,
                followup_turn_styles_by_task_id=followup_turn_styles_by_task_id,
                intent_judge_turns_by_task_id=intent_judge_turns_by_task_id,
                timestamp=now,
                eval_log_timestamp=eval_run_ts,
            )

        score_paths = write_combined_task_results(
            checklist_summary=checklist_summary,
            proactiveness_summary=proactiveness_summary,
            results_root=self.output_dir,
            timestamp=now,
            explicit_none_tasks=explicit_none_tasks,
        )
        user_root_dir = self.output_dir / safe_model_id(self.model_id) / self.user_id
        html_path = generate_trace_viewer_html(
            model_id=self.model_id,
            user_id=self.user_id,
            user_root_dir=user_root_dir,
        )
        result = OutputsReevaluationResult(
            model_id=self.model_id,
            user_id=self.user_id,
            scoring=self.scoring,
            output_dir=user_root_dir,
            checklist_reused_tasks=len(checklist_summary.tasks),
            proactiveness_evaluated_tasks=len(proactiveness_summary.tasks) if proactiveness_summary is not None else 0,
            overall_average_score=checklist_summary.overall_average_score,
            overall_proactiveness_average_score=(
                proactiveness_summary.overall_average_score if proactiveness_summary is not None else None
            ),
            score_paths=score_paths,
        )
        stage_logger.info(
            "Outputs reeval finished model_id={} user_id={} checklist_tasks={} checklist_avg={} proactiveness_tasks={} proactiveness_avg={} html_path={}",
            self.model_id,
            self.user_id,
            result.checklist_reused_tasks,
            _format_optional_score(checklist_summary.overall_average_score),
            result.proactiveness_evaluated_tasks,
            _format_optional_score(result.overall_proactiveness_average_score),
            html_path,
            data={
                "model_id": self.model_id,
                "user_id": self.user_id,
                "html_path": str(html_path),
                "score_paths": [str(path) for path in score_paths],
                "checklist_reused_tasks": result.checklist_reused_tasks,
                "proactiveness_evaluated_tasks": result.proactiveness_evaluated_tasks,
                "overall_average_score": result.overall_average_score,
                "overall_checklist_average_score": checklist_summary.overall_average_score,
                "overall_proactiveness_average_score": result.overall_proactiveness_average_score,
            },
        )
        result_logger.block(
            "Outputs reeval finished",
            f"model_id={result.model_id} user_id={result.user_id} scoring={result.scoring}",
            f"overall_avg={_format_optional_score(result.overall_average_score)}",
            (
                f"checklist_tasks={result.checklist_reused_tasks} "
                f"checklist_avg={_format_optional_score(checklist_summary.overall_average_score)}"
            ),
            (
                "proactiveness_tasks="
                f"{result.proactiveness_evaluated_tasks} "
                f"proactiveness_avg={_format_optional_score(result.overall_proactiveness_average_score)}"
                if result.overall_proactiveness_average_score is not None
                else f"proactiveness_tasks={result.proactiveness_evaluated_tasks} proactiveness_avg=n/a"
            ),
            f"score_files={len(result.score_paths)} output_dir={result.output_dir}",
            f"html_path={html_path}",
            *[f"score_path={path}" for path in result.score_paths],
            data={
                "output_dir": str(result.output_dir),
                "checklist_reused_tasks": result.checklist_reused_tasks,
                "proactiveness_evaluated_tasks": result.proactiveness_evaluated_tasks,
                "overall_average_score": result.overall_average_score,
                "overall_checklist_average_score": checklist_summary.overall_average_score,
                "overall_proactiveness_average_score": result.overall_proactiveness_average_score,
                "score_paths": [str(path) for path in result.score_paths],
                "html_path": str(html_path),
            },
        )
        return result

def _format_optional_score(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def _load_explicit_none_tasks(
    *,
    user_id: str,
    data_root: Path,
    task_ids: set[str],
) -> list[tuple[str, str]]:
    if not task_ids:
        return []
    try:
        _, episode, tasks = UserDataRepository(data_root=str(data_root)).load_user(user_id)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning(
            "Unable to resolve empty-criteria tasks user_id={} reason={}",
            user_id,
            str(exc),
        )
        return []
    ordered_task_ids = [task_id for task_id in episode.task_order if task_id in tasks and task_id in task_ids]
    for task_id in sorted(task_id for task_id in task_ids if task_id not in tasks):
        logger.warning("Ignoring evaluation output with unknown task_id user_id={} task_id={}", user_id, task_id)
    ordered_task_ids.extend(
        task_id
        for task_id in sorted(task_id for task_id in task_ids if task_id in tasks)
        if task_id not in ordered_task_ids
    )
    return [
        (task_id, tasks[task_id].title)
        for task_id in ordered_task_ids
        if not tasks[task_id].objectives
    ]
