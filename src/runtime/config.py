from __future__ import annotations

import argparse
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from ..utils import load_yaml_mapping, resolve_path
from .model_config import build_bench_runtime_config, load_model_config, normalize_llm_config, resolve_model_config_path

EVALUATION_SCORING_CHOICES = ("checklist", "proactiveness", "both")
REEVALUATION_SCORING_CHOICES = ("checklist", "both")


@dataclass(frozen=True)
class NanobotConfig:
    trace_logs_dir: Path
    workspace_dir: Path
    copy_task_assets_to_workspace: bool


@dataclass(frozen=True)
class BenchmarkConfig:
    turn_timeout: float
    user_id: str
    user_mode: str
    model_id: str
    task_ids: list[str] | None
    history_config_path: Path
    llm: dict[str, Any]


@dataclass(frozen=True)
class EvaluationConfig:
    model_id: str
    user_id: str
    task_ids: list[str] | None
    history_config_path: Path
    scoring: str
    llm: dict[str, Any] | None


@dataclass(frozen=True)
class ReevaluationConfig:
    model_id: str
    user_id: str
    scoring: str
    source_eval_timestamp: str | None


@dataclass(frozen=True)
class RunConfig:
    mode: str
    output_dir: Path
    log_level: str
    nanobot: NanobotConfig
    benchmark: BenchmarkConfig | None = None
    evaluation: EvaluationConfig | None = None
    reevaluation: ReevaluationConfig | None = None


def parse_llm_config(raw: Any, *, section_name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{section_name} must be a mapping")
    return normalize_llm_config(raw, section_name=section_name, default_temperature=None)


def read_nanobot_config(cfg: dict[str, Any]) -> NanobotConfig:
    nanobot_cfg = cfg.get("nanobot") or {}
    if not isinstance(nanobot_cfg, dict):
        raise ValueError("config.nanobot must be a mapping")
    return NanobotConfig(
        trace_logs_dir=resolve_path(str(nanobot_cfg.get("trace_logs_dir", "~/.nanobot/trace_logs"))),
        workspace_dir=resolve_path(str(nanobot_cfg.get("workspace_dir", "~/.nanobot/workspace"))),
        copy_task_assets_to_workspace=bool(nanobot_cfg.get("copy_task_assets_to_workspace", True)),
    )


def read_benchmark_config(run_cfg: dict[str, Any]) -> BenchmarkConfig:
    benchmark_cfg = run_cfg.get("interaction") or {}
    evaluation_cfg = run_cfg.get("evaluation") or {}
    if not isinstance(benchmark_cfg, dict):
        raise ValueError("config.run.interaction must be a mapping")
    if evaluation_cfg and not isinstance(evaluation_cfg, dict):
        raise ValueError("config.run.evaluation must be a mapping")

    task_ids = benchmark_cfg.get("task_ids")
    if task_ids is not None and not isinstance(task_ids, list):
        raise ValueError("config.run.interaction.task_ids must be a list of task_id strings")

    llm = parse_llm_config(benchmark_cfg.get("llm"), section_name="config.run.interaction.llm")
    model_id = str(
        benchmark_cfg.get("model_id")
        or (evaluation_cfg.get("model_id") if isinstance(evaluation_cfg, dict) else "")
        or llm["model"]
    ).strip()
    if not model_id:
        raise ValueError("config.run.interaction.model_id is required")

    return BenchmarkConfig(
        turn_timeout=float(benchmark_cfg.get("turn_timeout", 600.0)),
        user_id=str(benchmark_cfg.get("user_id", "user_003")),
        user_mode=str(benchmark_cfg.get("user_mode", "llm")),
        model_id=model_id,
        task_ids=task_ids,
        history_config_path=resolve_path(
            str(evaluation_cfg.get("history_config_path", "config/bench/evaluation/trace_history.yaml"))
        ),
        llm=llm,
    )


def _parse_evaluation_scoring(value: Any) -> str:
    scoring = str(value or "both").strip()
    if scoring not in EVALUATION_SCORING_CHOICES:
        raise ValueError(
            f"config.run.evaluation.scoring must be one of: {', '.join(EVALUATION_SCORING_CHOICES)}"
        )
    return scoring


def read_evaluation_config(
    run_cfg: dict[str, Any],
    *,
    scoring_override: str | None = None,
) -> EvaluationConfig:
    evaluation_cfg = run_cfg.get("evaluation") or {}
    benchmark_cfg = run_cfg.get("interaction") or {}
    if not isinstance(evaluation_cfg, dict):
        raise ValueError("config.run.evaluation must be a mapping")
    if not isinstance(benchmark_cfg, dict):
        raise ValueError("config.run.interaction must be a mapping")

    task_ids = evaluation_cfg.get("task_ids", benchmark_cfg.get("task_ids"))
    if task_ids is not None and not isinstance(task_ids, list):
        raise ValueError("config.run.evaluation.task_ids must be a list of task_id strings")

    model_id = str(evaluation_cfg.get("model_id") or "").strip()
    if not model_id:
        raise ValueError("config.run.evaluation.model_id is required for eval mode")

    user_id = str(evaluation_cfg.get("user_id") or benchmark_cfg.get("user_id") or "").strip()
    if not user_id:
        raise ValueError("config.run.evaluation.user_id is required for eval mode")

    scoring = _parse_evaluation_scoring(
        scoring_override if scoring_override is not None else evaluation_cfg.get("scoring", "both")
    )
    llm = None
    if scoring in {"checklist", "both"}:
        llm = parse_llm_config(evaluation_cfg.get("llm"), section_name="config.run.evaluation.llm")

    return EvaluationConfig(
        model_id=model_id,
        user_id=user_id,
        task_ids=task_ids,
        history_config_path=resolve_path(
            str(evaluation_cfg.get("history_config_path", "config/bench/evaluation/trace_history.yaml"))
        ),
        scoring=scoring,
        llm=llm,
    )


def _parse_reevaluation_scoring(value: Any) -> str:
    scoring = str(value or "both").strip()
    if scoring not in REEVALUATION_SCORING_CHOICES:
        raise ValueError(
            "config.run.evaluation.scoring must be one of: "
            f"{', '.join(REEVALUATION_SCORING_CHOICES)} for reeval mode"
        )
    return scoring


def read_reevaluation_config(
    run_cfg: dict[str, Any],
    *,
    scoring_override: str | None = None,
    source_eval_timestamp_override: str | None = None,
) -> ReevaluationConfig:
    evaluation_cfg = run_cfg.get("evaluation") or {}
    benchmark_cfg = run_cfg.get("interaction") or {}
    if not isinstance(evaluation_cfg, dict):
        raise ValueError("config.run.evaluation must be a mapping")
    if not isinstance(benchmark_cfg, dict):
        raise ValueError("config.run.interaction must be a mapping")

    model_id = str(evaluation_cfg.get("model_id") or "").strip()
    if not model_id:
        raise ValueError("config.run.evaluation.model_id is required for reeval mode")

    user_id = str(evaluation_cfg.get("user_id") or benchmark_cfg.get("user_id") or "").strip()
    if not user_id:
        raise ValueError("config.run.evaluation.user_id is required for reeval mode")

    scoring = _parse_reevaluation_scoring(
        scoring_override if scoring_override is not None else evaluation_cfg.get("scoring", "both")
    )

    source_eval_timestamp = str(
        source_eval_timestamp_override
        if source_eval_timestamp_override is not None
        else evaluation_cfg.get("source_eval_timestamp", "")
    ).strip()
    if not source_eval_timestamp:
        source_eval_timestamp = None

    return ReevaluationConfig(
        model_id=model_id,
        user_id=user_id,
        scoring=scoring,
        source_eval_timestamp=source_eval_timestamp,
    )


def build_run_config(args: argparse.Namespace) -> RunConfig:
    config_path = getattr(args, "config", None)
    model_config_path = getattr(args, "model_config", None)
    if config_path is not None:
        cfg = load_yaml_mapping(config_path)
    else:
        model_id = str(getattr(args, "model_id", "") or "").strip()
        if not model_id and model_config_path is None:
            raise ValueError("--model-id or --model-config is required when --config is not provided")
        if model_config_path is None:
            model_config_path = resolve_model_config_path(model_id)
        if not model_config_path.is_file():
            raise ValueError(f"model config not found: {model_config_path}")
        if not model_id:
            model_id = model_config_path.stem
        model_cfg = load_model_config(model_config_path, model_id=model_config_path.stem, resolve_env=True)
        cfg = build_bench_runtime_config(
            model_cfg,
            model_id=model_id,
            user_id=getattr(args, "user_id", None),
            task_ids=getattr(args, "task_id", None),
            output_dir=getattr(args, "output_dir", None),
            history_config_path=getattr(args, "history_config_path", None),
        )
    run_cfg = cfg.get("run") or {}
    if not isinstance(run_cfg, dict):
        raise ValueError("config.run must be a mapping")

    mode = str(args.mode or run_cfg.get("mode", "run")).strip()
    if mode not in {"run", "eval", "reeval"}:
        raise ValueError(f"unsupported mode: {mode}")
    log_level = str(args.log_level or run_cfg.get("log_level") or os.getenv("BENCH_LOG_LEVEL", "INFO")).upper()

    nanobot = read_nanobot_config(cfg)
    if args.trace_logs_dir:
        nanobot = replace(nanobot, trace_logs_dir=resolve_path(str(args.trace_logs_dir)))
    if args.workspace_dir:
        nanobot = replace(nanobot, workspace_dir=resolve_path(str(args.workspace_dir)))

    output_dir = resolve_path(str(run_cfg.get("output_dir") or "outputs"))
    if args.output_dir:
        output_dir = resolve_path(str(args.output_dir))

    if mode == "eval":
        evaluation = read_evaluation_config(
            run_cfg,
            scoring_override=args.evaluation_scoring,
        )
        if args.model_id:
            evaluation = replace(evaluation, model_id=args.model_id)
        if args.user_id:
            evaluation = replace(evaluation, user_id=args.user_id)
        if args.task_id is not None:
            evaluation = replace(evaluation, task_ids=args.task_id)
        if args.history_config_path:
            evaluation = replace(
                evaluation,
                history_config_path=resolve_path(str(args.history_config_path)),
            )
        if args.llm_timeout is not None and evaluation.llm is not None:
            evaluation = replace(
                evaluation,
                llm={**evaluation.llm, "request_timeout": args.llm_timeout},
            )
        if args.evaluation_output_dir:
            output_dir = resolve_path(str(args.evaluation_output_dir))
        return RunConfig(
            mode=mode,
            output_dir=output_dir,
            log_level=log_level,
            nanobot=nanobot,
            evaluation=evaluation,
        )

    if mode == "reeval":
        if args.trace_logs_dir is not None:
            raise ValueError("--trace-logs-dir is not supported in reeval mode")
        if args.workspace_dir is not None:
            raise ValueError("--workspace-dir is not supported in reeval mode")
        if args.history_config_path is not None:
            raise ValueError("--history-config-path is not supported in reeval mode")
        if args.llm_timeout is not None:
            raise ValueError("--llm-timeout is not supported in reeval mode")
        if args.evaluation_output_dir is not None:
            raise ValueError("--evaluation-output-dir is not supported in reeval mode")

        reevaluation = read_reevaluation_config(
            run_cfg,
            scoring_override=args.evaluation_scoring,
            source_eval_timestamp_override=args.source_eval_timestamp,
        )
        if args.model_id:
            reevaluation = replace(reevaluation, model_id=args.model_id)
        if args.user_id:
            reevaluation = replace(reevaluation, user_id=args.user_id)
        return RunConfig(
            mode=mode,
            output_dir=output_dir,
            log_level=log_level,
            nanobot=nanobot,
            reevaluation=reevaluation,
        )

    benchmark = read_benchmark_config(run_cfg)
    if args.turn_timeout is not None:
        benchmark = replace(benchmark, turn_timeout=args.turn_timeout)
    if args.llm_timeout is not None:
        benchmark = replace(
            benchmark,
            llm={**benchmark.llm, "request_timeout": args.llm_timeout},
        )
    if args.user_id:
        benchmark = replace(benchmark, user_id=args.user_id)
    if args.user_mode:
        benchmark = replace(benchmark, user_mode=args.user_mode)
    if args.task_id is not None:
        benchmark = replace(benchmark, task_ids=args.task_id)
    if args.model_id:
        benchmark = replace(benchmark, model_id=args.model_id)
    if args.history_config_path:
        benchmark = replace(
            benchmark,
            history_config_path=resolve_path(str(args.history_config_path)),
        )
    return RunConfig(
        mode=mode,
        output_dir=output_dir,
        log_level=log_level,
        nanobot=nanobot,
        benchmark=benchmark,
    )


def as_mapping(value: BenchmarkConfig | EvaluationConfig | ReevaluationConfig | NanobotConfig) -> dict[str, Any]:
    return asdict(value)
