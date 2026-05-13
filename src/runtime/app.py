from __future__ import annotations

import os
from pathlib import Path

from ..evaluation import OutputsReevaluationRunner, TraceEvaluationRunner
from ..llm import LLMClient
from ..runner.runner import BenchmarkRunner
from ..utils import bind_log_run, clear_log_run
from ..user_agent.terminal_user_agent import TerminalUserAgent
from ..user_agent.user_agent import UserAgent
from .config import BenchmarkConfig, EvaluationConfig, NanobotConfig, ReevaluationConfig, RunConfig


def build_channel():
    from ..channels.test import TestChannel

    return TestChannel(
        config={
            "base_url": os.environ.get("BENCH_TEST_SERVER_URL", "http://localhost:9999"),
        }
    )


def build_user_agent(config: BenchmarkConfig, nanobot: NanobotConfig, output_dir: Path):
    user_root = f"data/{config.user_id}"
    if config.user_mode == "llm":
        return UserAgent(
            user_root=user_root,
            llm_client=LLMClient(**config.llm),
            task_ids=config.task_ids,
            model_id=config.model_id,
            output_root=str(output_dir),
            workspace_dir=nanobot.workspace_dir,
            copy_task_assets_to_workspace=nanobot.copy_task_assets_to_workspace,
            history_config_path=config.history_config_path,
        )
    return TerminalUserAgent(
        user_root=user_root,
        task_ids=config.task_ids,
        model_id=config.model_id,
        output_root=str(output_dir),
        workspace_dir=nanobot.workspace_dir,
        copy_task_assets_to_workspace=nanobot.copy_task_assets_to_workspace,
    )


async def run_application(config: RunConfig) -> None:
    if config.mode == "eval":
        await _run_evaluation(config.evaluation, config)
        return
    if config.mode == "reeval":
        await _run_reevaluation(config.reevaluation, config)
        return
    await _run_benchmark(config.benchmark, config)


async def _run_evaluation(config: EvaluationConfig | None, run_config: RunConfig) -> None:
    clear_log_run()
    if config is None:
        raise ValueError("evaluation config is required for eval mode")
    bind_log_run(
        output_root=run_config.output_dir,
        model_id=config.model_id,
        user_id=config.user_id,
        agent_id=config.model_id,
        task_log_dirname="eval/logs",
    )
    llm_client = LLMClient(**config.llm) if config.llm is not None else None
    evaluator = TraceEvaluationRunner(
        model_id=config.model_id,
        user_id=config.user_id,
        logs_dir=run_config.nanobot.trace_logs_dir,
        workspace_dir=run_config.nanobot.workspace_dir,
        config_path=config.history_config_path,
        output_dir=run_config.output_dir,
        scoring=config.scoring,
        llm_client=llm_client,
        task_ids=config.task_ids,
    )
    try:
        await evaluator.run()
    finally:
        clear_log_run()


async def _run_reevaluation(config: ReevaluationConfig | None, run_config: RunConfig) -> None:
    clear_log_run()
    if config is None:
        raise ValueError("reevaluation config is required for reeval mode")
    bind_log_run(
        output_root=run_config.output_dir,
        model_id=config.model_id,
        user_id=config.user_id,
        agent_id=config.model_id,
        task_log_dirname="eval/logs",
    )
    evaluator = OutputsReevaluationRunner(
        model_id=config.model_id,
        user_id=config.user_id,
        output_dir=run_config.output_dir,
        scoring=config.scoring,
        source_eval_timestamp=config.source_eval_timestamp,
    )
    try:
        await evaluator.run()
    finally:
        clear_log_run()


async def _run_benchmark(config: BenchmarkConfig | None, run_config: RunConfig) -> None:
    if config is None:
        raise ValueError("benchmark config is required for run mode")
    channel = build_channel()
    user_agent = build_user_agent(config, run_config.nanobot, run_config.output_dir)
    runner = BenchmarkRunner(
        channel=channel,
        user_agent=user_agent,
        turn_timeout=config.turn_timeout,
    )

    try:
        async with channel:
            result = await runner.run()
    finally:
        clear_log_run()

    print(f"\n[benchmark] status={result.status}")
    for item in result.tasks:
        print(f"[task] id={item.task_id} status={item.status} turns={item.turns}")
        if item.error:
            print(f"  error={item.error}")
