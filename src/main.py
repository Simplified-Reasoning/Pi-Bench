import asyncio
import argparse
from pathlib import Path
from .runtime import (
    EVALUATION_SCORING_CHOICES,
    REEVALUATION_SCORING_CHOICES,
    as_mapping,
    build_run_config,
    parse_llm_config,
    read_benchmark_config,
    read_evaluation_config,
    run_application,
)
from .utils import configure_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bench benchmark.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/bench/nanobot.yaml"),
        help="Run config YAML path.",
    )
    parser.add_argument("--mode", type=str, choices=("run", "eval", "reeval"), default=None)
    parser.add_argument("--trace-logs-dir", type=Path, default=None)
    parser.add_argument("--workspace-dir", type=Path, default=None)
    parser.add_argument("--turn-timeout", type=float, default=None)
    parser.add_argument("--llm-timeout", type=float, default=None)
    parser.add_argument("--user-id", type=str, default=None)
    parser.add_argument("--user-mode", type=str, choices=("llm", "terminal"), default=None)
    parser.add_argument(
        "--task-id",
        action="append",
        default=None,
        help="Override task list by repeating this flag; empty means use YAML.",
    )
    parser.add_argument("--model-id", type=str, default=None)
    parser.add_argument("--history-config-path", type=Path, default=None)
    parser.add_argument(
        "--evaluation-scoring",
        type=str,
        choices=tuple(sorted(set(EVALUATION_SCORING_CHOICES).union(REEVALUATION_SCORING_CHOICES))),
        default=None,
        help="Eval scoring mode: checklist, proactiveness, or both.",
    )
    parser.add_argument(
        "--source-eval-timestamp",
        type=str,
        default=None,
        help="Reuse checklist payloads from a specific prior eval timestamp in reeval mode.",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--evaluation-output-dir", type=Path, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    return parser.parse_args()


async def main():
    args = _parse_args()
    config = build_run_config(args)
    configure_logging(level=config.log_level)
    await run_application(config)


def _parse_llm_config(raw, *, section_name: str):
    return parse_llm_config(raw, section_name=section_name)


def _read_benchmark_config(run_cfg):
    return as_mapping(read_benchmark_config(run_cfg))


def _read_evaluation_config(run_cfg):
    return as_mapping(read_evaluation_config(run_cfg))


if __name__ == "__main__":
    asyncio.run(main())
