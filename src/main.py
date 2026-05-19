import asyncio
import argparse
import sys
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
from .runtime.model_config import write_runtime_files
from .utils import configure_logging


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bench benchmark.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Run config YAML path.",
    )
    parser.add_argument("--model-config", type=Path, default=None, help="Model config YAML path.")
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
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None):
    args = _parse_args(argv)
    config = build_run_config(args)
    configure_logging(level=config.log_level)
    await run_application(config)


def _prepare_runtime(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Prepare container runtime config files.")
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--bench-config-output", type=Path, required=True)
    parser.add_argument("--nanobot-config-output", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--task-id", action="append", default=None)
    parser.add_argument("--trace-logs-dir", type=Path, required=True)
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--history-config-path", type=Path, required=True)
    parser.add_argument("--test-server-url", required=True)
    parser.add_argument("--appworld-mcp-url", required=True)
    parser.add_argument("--enable-appworld", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)
    write_runtime_files(
        model_config_path=args.model_config,
        bench_config_path=args.bench_config_output,
        nanobot_config_path=args.nanobot_config_output,
        model_id=args.model_id,
        user_id=args.user_id,
        task_ids=args.task_id,
        trace_logs_dir=args.trace_logs_dir,
        workspace_dir=args.workspace_dir,
        output_dir=args.output_dir,
        history_config_path=args.history_config_path,
        test_server_url=args.test_server_url,
        appworld_mcp_url=args.appworld_mcp_url,
        enable_appworld=args.enable_appworld,
    )
    print(
        "[pibench] prepared runtime configs "
        f"bench={args.bench_config_output} nanobot={args.nanobot_config_output}"
    )
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    invoked_as_pibench = Path(sys.argv[0]).name == "pibench"
    if invoked_as_pibench or (argv and argv[0] == "docker-run"):
        from .docker_launcher import main as docker_main

        return docker_main(argv)
    if argv and argv[0] == "prepare-runtime":
        return _prepare_runtime(argv[1:])
    asyncio.run(main(argv))
    return 0


def _parse_llm_config(raw, *, section_name: str):
    return parse_llm_config(raw, section_name=section_name)


def _read_benchmark_config(run_cfg):
    return as_mapping(read_benchmark_config(run_cfg))


def _read_evaluation_config(run_cfg):
    return as_mapping(read_evaluation_config(run_cfg))


if __name__ == "__main__":
    raise SystemExit(cli_main())
