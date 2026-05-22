from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .runtime.model_config import load_model_config, model_proxy_env, referenced_config_env_vars
from .utils import load_yaml_mapping


IMAGE_NAME = "zzzhr97/pi-bench:latest"
CONTAINER_PREFIX = "bench"
PROACTIVE_ROOT_CONTAINER = "/opt/proactive"
CONFIG_ROOT_CONTAINER = f"{PROACTIVE_ROOT_CONTAINER}/config"
SCRIPTS_ROOT_CONTAINER = f"{PROACTIVE_ROOT_CONTAINER}/scripts"
ENTRYPOINT_CONTAINER_FILE = f"{SCRIPTS_ROOT_CONTAINER}/entrypoint.sh"
APPWORLD_ROOT_CONTAINER = f"{PROACTIVE_ROOT_CONTAINER}/appworld"
PLANNED_TASKS_RE = re.compile(r"planned_tasks=(\d+)")
TASK_STARTED_RE = re.compile(r"Task started task_id=(\S+)")
TASK_FINISHED_RE = re.compile(r"Task finished task_id=(\S+) status=(\S+)")
TASK_SUMMARY_RE = re.compile(r"\[task\] id=(\S+) status=(\S+)")
RUN_SUFFIX_RE = re.compile(r"__run\d+$")


@dataclass(frozen=True)
class Job:
    user_id: str
    model_id: str
    run_model_id: str
    model_config_host_path: Path
    runtime_dir: Path
    service_logs_dir: Path
    container_name: str


@dataclass
class TaskProgress:
    total: int | None = None
    current_task_id: str | None = None
    completed_statuses: dict[str, str] = field(default_factory=dict)


@dataclass
class RunningJob:
    job: Job
    cid: str
    proc: subprocess.Popen
    exit_code: int | None = None
    inspect_summary: str = ""


@dataclass(frozen=True)
class ScorePair:
    comp: float | None
    proc: float | None


@dataclass(frozen=True)
class ScoreSummary:
    comp: float | None
    proc: float | None
    comp_std: float | None = None
    proc_std: float | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _trimmed_csv(value: str, *, arg_name: str) -> list[str]:
    parts = [item.strip() for item in value.split(",")]
    if not parts or any(not item for item in parts):
        raise SystemExit(f"[pibench] --{arg_name} contains an empty item: {value}")
    return parts


def _flatten_csv_values(values: list[str] | None, *, arg_name: str) -> list[str]:
    if not values:
        return []
    flattened: list[str] = []
    for value in values:
        flattened.extend(_trimmed_csv(value, arg_name=arg_name))
    return flattened


def _sanitize_token(raw: str) -> str:
    return "".join(ch.lower() if ch.isalnum() or ch in "_.-" else "-" for ch in raw)


def _safe_model_id(raw: str) -> str:
    return raw.replace("/", "_")


def _run(cmd: list[str], *, check: bool = True, stdout=None, stderr=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, text=True, stdout=stdout, stderr=stderr)


def _parse_bench_progress(bench_log_path: Path) -> TaskProgress:
    progress = TaskProgress()
    if not bench_log_path.is_file():
        return progress

    try:
        lines = bench_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return progress

    for line in lines:
        if progress.total is None:
            planned_match = PLANNED_TASKS_RE.search(line)
            if planned_match:
                progress.total = int(planned_match.group(1))

        started_match = TASK_STARTED_RE.search(line)
        if started_match:
            progress.current_task_id = started_match.group(1)

        finished_match = TASK_FINISHED_RE.search(line)
        if finished_match:
            task_id, status = finished_match.groups()
            progress.completed_statuses[task_id] = status
            if progress.current_task_id == task_id:
                progress.current_task_id = None
            continue

        summary_match = TASK_SUMMARY_RE.search(line)
        if summary_match:
            task_id, status = summary_match.groups()
            progress.completed_statuses[task_id] = status
            if progress.current_task_id == task_id:
                progress.current_task_id = None

    return progress


def _short_cid(cid: str) -> str:
    return cid[:12] if len(cid) > 12 else cid


def _status_cell(run: RunningJob) -> Spinner | Text:
    if run.exit_code is None:
        return Spinner("dots", text=Text("running", style="yellow"))
    if run.exit_code == 0:
        return Text("passed", style="green")
    return Text(f"failed ({run.exit_code})", style="red")


def _tasks_cell(progress: TaskProgress) -> Text:
    total = str(progress.total) if progress.total is not None else "?"
    completed = len(progress.completed_statuses)
    style = "green" if progress.total is not None and completed >= progress.total else "cyan"
    return Text(f"{completed}/{total}", style=style)


def _current_task_cell(progress: TaskProgress, run: RunningJob) -> Text:
    if progress.current_task_id:
        return Text(progress.current_task_id, style="yellow")
    if run.exit_code is None:
        if progress.completed_statuses:
            return Text("between tasks", style="dim")
        return Text("starting", style="dim")
    return Text("-", style="dim")


def _service_log_paths(job: Job) -> tuple[Path, Path]:
    return job.service_logs_dir / "bench.log", job.service_logs_dir / "nanobot_gateway.log"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(_repo_root()))
    except ValueError:
        return str(path)


def _build_runs_table(runs: list[RunningJob]) -> Table:
    table = Table(
        box=box.SIMPLE,
        expand=True,
        show_lines=False,
    )
    table.add_column("Run", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Tasks", justify="right", no_wrap=True)
    table.add_column("Current task", overflow="fold")
    table.add_column("CID", style="dim", no_wrap=True)
    table.add_column("Output", style="dim", overflow="fold")

    for run in runs:
        progress = _parse_bench_progress(run.job.service_logs_dir / "bench.log")
        bench_log_path, gateway_log_path = _service_log_paths(run.job)
        run_label = Text()
        run_label.append(run.job.run_model_id, style="cyan")
        run_label.append(f"\n-> {run.job.user_id}", style="dim cyan")
        output = Text()
        output.append(f"service-logs: {_display_path(run.job.service_logs_dir)}/\n")
        output.append(f"logs: {bench_log_path.name}, {gateway_log_path.name}")
        table.add_row(
            run_label,
            _status_cell(run),
            _tasks_cell(progress),
            _current_task_cell(progress, run),
            _short_cid(run.cid),
            output,
        )
    return table


def _base_model_id(model_id: str) -> str:
    return RUN_SUFFIX_RE.sub("", model_id)


def _latest_eval_result_path(job: Job) -> Path | None:
    user_root = job.runtime_dir.parent.parent
    result_paths = sorted(user_root.glob("*/eval/results/*_result.json"))
    return result_paths[-1] if result_paths else None


def _extract_score(value: object, *, result_path: Path, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {field_name} in {result_path}: {value!r}")
    score = float(value)
    if not math.isfinite(score):
        raise ValueError(f"non-finite {field_name} in {result_path}: {value!r}")
    return score


def _read_overall_score_pair(job: Job) -> ScorePair | None:
    result_path = _latest_eval_result_path(job)
    if result_path is None:
        return None
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return ScorePair(
        comp=_extract_score(
            payload.get("overall_checklist_average_score"),
            result_path=result_path,
            field_name="overall_checklist_average_score",
        ),
        proc=_extract_score(
            payload.get("overall_proactiveness_average_score"),
            result_path=result_path,
            field_name="overall_proactiveness_average_score",
        ),
    )


def _score_summary(pairs: list[ScorePair | None], *, include_std: bool) -> ScoreSummary | None:
    present = [pair for pair in pairs if pair is not None]
    if not present:
        return None

    comp_values = [pair.comp for pair in present if pair.comp is not None]
    proc_values = [pair.proc for pair in present if pair.proc is not None]
    comp = sum(comp_values) / len(comp_values) if comp_values else None
    proc = sum(proc_values) / len(proc_values) if proc_values else None
    if comp is None and proc is None:
        return None

    return ScoreSummary(
        comp=comp,
        proc=proc,
        comp_std=statistics.stdev(comp_values) if include_std and len(comp_values) > 1 else None,
        proc_std=statistics.stdev(proc_values) if include_std and len(proc_values) > 1 else None,
    )


def _format_score(value: float | None) -> str:
    if value is None:
        return "none"
    return f"{value * 100:.2f}"


def _format_score_with_std(value: float | None, std: float | None) -> str:
    score = _format_score(value)
    if value is None or std is None:
        return score
    return f"{score} +/- {_format_score(std)}"


def _score_summary_text(summary: ScoreSummary | None) -> Text:
    if summary is None:
        return Text("comp none\nproc none", style="dim")

    style = "green" if (summary.comp or 0.0) >= 1.0 and (summary.proc or 0.0) >= 1.0 else "yellow"
    text = Text(style=style)
    text.append(f"comp {_format_score_with_std(summary.comp, summary.comp_std)}\n")
    text.append(f"proc {_format_score_with_std(summary.proc, summary.proc_std)}")
    return text


def _aggregate_result_cell(pairs: list[ScorePair | None], *, include_std: bool) -> Text:
    return _score_summary_text(_score_summary(pairs, include_std=include_std))


def _build_results_table(runs: list[RunningJob], users: list[str]) -> Table:
    table = Table(
        title="Model Results",
        caption="comp/proc are overall checklist and proactiveness scores; repeated runs show mean +/- std",
        box=box.SIMPLE,
        expand=True,
        title_style="bold cyan",
        caption_style="dim",
    )
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Avg", justify="right", no_wrap=True)
    for user_id in users:
        table.add_column(user_id, justify="right", no_wrap=True)

    runs_by_model: dict[str, dict[str, list[RunningJob]]] = {}
    for run in runs:
        runs_by_model.setdefault(_base_model_id(run.job.model_id), {}).setdefault(run.job.user_id, []).append(run)

    for model_id in sorted(runs_by_model):
        row_by_user = runs_by_model[model_id]
        cells: list[Text] = []
        score_pairs: list[ScorePair | None] = []
        repeated_runs = any(len(row_by_user.get(user_id, [])) > 1 for user_id in users)
        for user_id in users:
            user_runs = row_by_user.get(user_id)
            if not user_runs:
                cells.append(Text("-", style="dim"))
                continue
            user_score_pairs = [_read_overall_score_pair(run.job) for run in user_runs]
            cells.append(_aggregate_result_cell(user_score_pairs, include_std=len(user_runs) > 1))
            score_pairs.extend(user_score_pairs)
        table.add_row(model_id, _score_summary_text(_score_summary(score_pairs, include_std=repeated_runs)), *cells)

    return table


def _build_header(*, image: str, users: list[str], models: list[str], run_count: int, output_root: Path) -> Panel:
    details = Table.grid(padding=(0, 2))
    details.add_column(style="cyan", no_wrap=True)
    details.add_column(style="white")
    details.add_row("image", image)
    details.add_row("users", f"{len(users)}: {', '.join(users)}")
    details.add_row("models", f"{len(models)}: {', '.join(models)}")
    details.add_row("runs/model", str(run_count))
    details.add_row("output", str(output_root))
    return Panel(details, title="pibench", title_align="left", border_style="cyan", box=box.ROUNDED)


def _inspect_finished_job(job: Job, start_code: int) -> tuple[int, str]:
    inspect_after = subprocess.run(["docker", "inspect", job.container_name], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (job.runtime_dir / "inspect.after.log").write_text(inspect_after.stdout, encoding="utf-8")
    state = subprocess.run(
        [
            "docker",
            "inspect",
            job.container_name,
            "--format",
            "status={{.State.Status}} exit_code={{.State.ExitCode}} started_at={{.State.StartedAt}} finished_at={{.State.FinishedAt}} oom_killed={{.State.OOMKilled}} error={{.State.Error}}",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    summary = state.stdout.strip() or f"status=unknown exit_code={start_code}"
    (job.runtime_dir / "inspect.summary.log").write_text(summary + "\n", encoding="utf-8")
    exit_code = start_code
    for part in summary.split():
        if part.startswith("exit_code="):
            try:
                exit_code = int(part.split("=", 1)[1])
            except ValueError:
                exit_code = start_code
    return exit_code, summary


def _shutdown_running_jobs(runs: list[RunningJob], *, console: Console) -> None:
    active_runs = [run for run in runs if run.exit_code is None]
    if not active_runs:
        return

    console.print("[yellow]interrupt received; stopping running Docker container(s)[/yellow]")
    for run in active_runs:
        console.print(f"[yellow]stopping[/yellow] container={run.job.container_name}")
        _run(["docker", "stop", run.job.container_name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for run in active_runs:
        try:
            start_code = run.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            run.proc.terminate()
            try:
                start_code = run.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                run.proc.kill()
                start_code = run.proc.wait(timeout=5)

        try:
            run.exit_code, run.inspect_summary = _inspect_finished_job(run.job, start_code)
        except Exception as exc:
            run.exit_code = start_code
            run.inspect_summary = f"inspect_failed={exc}"


def _docker_available() -> None:
    try:
        _run(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit("[pibench] docker command not found or unavailable") from exc


def _require_image(image_name: str) -> None:
    inspected = _run(
        ["docker", "image", "inspect", image_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if inspected.returncode == 0:
        return
    raise SystemExit(
        f"[pibench] docker image not found locally: {image_name}\n"
        "[pibench] run the Docker image setup step before launching experiments"
    )


def _validate_repo_paths(repo_root: Path) -> None:
    required_dirs = [
        repo_root / "src",
        repo_root / "data",
        repo_root / "config",
        repo_root / "scripts",
        repo_root / "third_party" / "nanobot",
        repo_root / "third_party" / "appworld",
    ]
    required_files = [repo_root / "scripts" / "entrypoint.sh"]
    missing = [str(path) for path in [*required_dirs, *required_files] if not path.exists()]
    if missing:
        raise SystemExit("[pibench] missing required path(s):\n  - " + "\n  - ".join(missing))


def _validate_users(repo_root: Path, user_ids: list[str]) -> None:
    missing: list[str] = []
    for user_id in user_ids:
        user_dir = repo_root / "data" / user_id
        for filename in ("profile.yaml", "episode.yaml"):
            path = user_dir / filename
            if not path.is_file():
                missing.append(f"{user_id}:{path}")
    if missing:
        raise SystemExit("[pibench] user data check failed:\n  - " + "\n  - ".join(missing))


def _model_config_path(repo_root: Path, model_id: str) -> Path:
    yaml_path = repo_root / "config" / "models" / f"{model_id}.yaml"
    if yaml_path.is_file():
        return yaml_path
    yml_path = repo_root / "config" / "models" / f"{model_id}.yml"
    if yml_path.is_file():
        return yml_path
    raise SystemExit(f"[pibench] missing model config: {yaml_path}")


def _build_jobs(
    *,
    repo_root: Path,
    output_root: Path,
    users: list[str],
    models: list[str],
    run_count: int,
    timestamp: str,
) -> list[Job]:
    jobs: list[Job] = []
    container_timestamp = timestamp.replace("_", "")
    seen_run_models: set[str] = set()
    for user_id in users:
        safe_user = _sanitize_token(user_id)
        for model_id in models:
            config_path = _model_config_path(repo_root, model_id)
            for run_number in range(1, run_count + 1):
                run_model_id = model_id if run_count == 1 else f"{model_id}__run{run_number:02d}"
                if run_model_id in seen_run_models and len(users) == 1:
                    raise SystemExit(f"[pibench] duplicate generated run model id: {run_model_id}")
                seen_run_models.add(run_model_id)
                safe_run_model = _safe_model_id(run_model_id)
                runtime_dir = output_root / safe_run_model / user_id / "run" / f"{timestamp}-runtime"
                jobs.append(
                    Job(
                        user_id=user_id,
                        model_id=model_id,
                        run_model_id=run_model_id,
                        model_config_host_path=config_path,
                        runtime_dir=runtime_dir,
                        service_logs_dir=runtime_dir / "service-logs",
                        container_name=f"{CONTAINER_PREFIX}-{container_timestamp}-{safe_user}-{safe_run_model}",
                    )
                )
    return jobs


def _container_model_config_path(repo_root: Path, host_path: Path) -> str:
    return f"{CONFIG_ROOT_CONTAINER}/{host_path.relative_to(repo_root / 'config')}"


def _build_container_env_args(
    *,
    repo_root: Path,
    job: Job,
    task_ids: list[str],
    enable_appworld: bool,
) -> list[str]:
    model_cfg = load_model_config(job.model_config_host_path, model_id=job.model_id)
    raw_model_cfg = load_yaml_mapping(job.model_config_host_path)
    env_args = [
        "-e",
        f"MODEL_ID={job.run_model_id}",
        "-e",
        f"MODEL_CONFIG_PATH={_container_model_config_path(repo_root, job.model_config_host_path)}",
        "-e",
        f"ENABLE_APPWORLD={str(enable_appworld).lower()}",
        "-e",
        f"BENCH_USER_ID={job.user_id}",
        "-e",
        f"BENCH_HISTORY_CONFIG_PATH={CONFIG_ROOT_CONTAINER}/bench/evaluation/trace_history.yaml",
        "-e",
        f"BENCH_WORKDIR={PROACTIVE_ROOT_CONTAINER}",
        "-e",
        f"BENCH_TEST_SERVER_SCRIPT={SCRIPTS_ROOT_CONTAINER}/test_server.py",
        "-e",
        f"APPWORLD_ROOT={APPWORLD_ROOT_CONTAINER}",
    ]
    if task_ids:
        env_args.extend(["-e", f"BENCH_TASK_IDS={','.join(task_ids)}"])
    for key, value in model_proxy_env(model_cfg).items():
        env_args.extend(["-e", f"{key}={value}"])
    for key in sorted(referenced_config_env_vars(raw_model_cfg)):
        env_args.extend(["-e", f"{key}={os.getenv(key, '')}"])
    return env_args


def _create_container(
    *,
    repo_root: Path,
    output_root: Path,
    image_name: str,
    job: Job,
    task_ids: list[str],
    enable_appworld: bool,
    remove_existing_runtime: bool,
) -> tuple[str, subprocess.Popen]:
    if remove_existing_runtime and job.runtime_dir.exists():
        import shutil

        shutil.rmtree(job.runtime_dir)
    job.service_logs_dir.mkdir(parents=True, exist_ok=True)

    create_cmd = [
        "docker",
        "create",
        "--name",
        job.container_name,
        "--entrypoint",
        ENTRYPOINT_CONTAINER_FILE,
        *_build_container_env_args(
            repo_root=repo_root,
            job=job,
            task_ids=task_ids,
            enable_appworld=enable_appworld,
        ),
        "-v",
        f"{job.service_logs_dir}:/root/.nanobot/logs",
        "-v",
        f"{output_root}:{PROACTIVE_ROOT_CONTAINER}/outputs",
        "-v",
        f"{repo_root / 'src'}:{PROACTIVE_ROOT_CONTAINER}/src",
        "-v",
        f"{repo_root / 'data'}:{PROACTIVE_ROOT_CONTAINER}/data",
        "-v",
        f"{repo_root / 'config'}:{CONFIG_ROOT_CONTAINER}",
        "-v",
        f"{repo_root / 'scripts'}:{SCRIPTS_ROOT_CONTAINER}",
        "-v",
        f"{repo_root / 'third_party' / 'nanobot'}:{PROACTIVE_ROOT_CONTAINER}/nanobot",
        "-v",
        f"{repo_root / 'third_party' / 'appworld'}:{APPWORLD_ROOT_CONTAINER}",
        image_name,
    ]
    cid = subprocess.check_output(create_cmd, text=True).strip()
    (job.runtime_dir / "inspect.before.log").write_text(
        subprocess.run(["docker", "inspect", job.container_name], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout,
        encoding="utf-8",
    )
    log_file = job.runtime_dir / "container.log"
    log_handle = log_file.open("w", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            ["docker", "start", "-a", job.container_name],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
    finally:
        log_handle.close()
    return cid, proc


def run_docker(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    repo_root = _repo_root()
    output_root = (repo_root / args.output_dir).resolve() if not args.output_dir.is_absolute() else args.output_dir
    users = _trimmed_csv(args.user_id, arg_name="user-id")
    models = _trimmed_csv(args.model_id, arg_name="model-id")
    if len(set(models)) != len(models):
        raise SystemExit("[pibench] duplicate --model-id values are not supported; use --run for repeated runs")
    if args.run < 1:
        raise SystemExit("[pibench] --run must be >= 1")

    _docker_available()
    _validate_repo_paths(repo_root)
    _validate_users(repo_root, users)
    for model_id in models:
        load_model_config(_model_config_path(repo_root, model_id), model_id=model_id)
    _require_image(args.image)

    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    jobs = _build_jobs(
        repo_root=repo_root,
        output_root=output_root,
        users=users,
        models=models,
        run_count=args.run,
        timestamp=timestamp,
    )

    console.print(_build_header(image=args.image, users=users, models=models, run_count=args.run, output_root=output_root))

    running: list[RunningJob] = []
    overall_code = 0
    try:
        for job in jobs:
            console.print(
                f"[cyan]launching[/cyan] user={job.user_id} model={job.model_id} "
                f"run_model_id={job.run_model_id} container={job.container_name}"
            )
            cid, proc = _create_container(
                repo_root=repo_root,
                output_root=output_root,
                image_name=args.image,
                job=job,
                task_ids=_flatten_csv_values(args.task_id, arg_name="task-id"),
                enable_appworld=not args.disable_appworld,
                remove_existing_runtime=not args.keep_runtime,
            )
            running.append(RunningJob(job=job, cid=cid, proc=proc))

        if running:
            with Live(_build_runs_table(running), console=console, auto_refresh=False, transient=False) as live:
                while True:
                    all_done = True
                    for run in running:
                        if run.exit_code is not None:
                            continue
                        poll_code = run.proc.poll()
                        if poll_code is None:
                            all_done = False
                            continue
                        run.exit_code, run.inspect_summary = _inspect_finished_job(run.job, poll_code)
                        if run.exit_code != 0:
                            overall_code = 1
                    live.update(_build_runs_table(running), refresh=True)
                    if all_done:
                        break
                    time.sleep(1.0)
    except KeyboardInterrupt:
        _shutdown_running_jobs(running, console=console)
        overall_code = 130
        console.print(_build_runs_table(running))

    if running:
        console.print(_build_results_table(running, users))

    failed_runs = [run for run in running if run.exit_code not in (None, 0)]
    for run in failed_runs:
        bench_log_path, gateway_log_path = _service_log_paths(run.job)
        console.print(
            "\n".join(
                [
                    f"[red]failed[/red] user={run.job.user_id} model={run.job.model_id} run_model_id={run.job.run_model_id}",
                    f"exit_code={run.exit_code} container={run.job.container_name}",
                    f"runtime_dir={run.job.runtime_dir}",
                    f"bench_log={bench_log_path}",
                    f"nanobot_gateway_log={gateway_log_path}",
                    f"container_log={run.job.runtime_dir / 'container.log'}",
                ]
            )
        )

    for run in running:
        if args.remove_container:
            _run(["docker", "rm", run.job.container_name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return overall_code


def add_launcher_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model-id", required=True, help="Comma-separated model ids from config/models/<model-id>.yaml.")
    parser.add_argument("--user-id", default="law_trainee", help="Comma-separated user ids.")
    parser.add_argument("--run", type=int, default=1, help="Number of repeated runs per model.")
    parser.add_argument("--task-id", action="append", default=None, help="Limit to task id; repeat for multiple tasks.")
    parser.add_argument("--image", default=IMAGE_NAME, help="Docker image to run.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Output directory.")
    parser.add_argument("--disable-appworld", action="store_true", help="Disable AppWorld MCP integration.")
    parser.add_argument("--keep-runtime", action="store_true", help="Do not delete an existing timestamp runtime dir.")
    parser.add_argument("--remove-container", action="store_true", help="Remove containers after they exit.")
    parser.set_defaults(func=run_docker)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pibench", description="Run Pi-Bench jobs in Docker containers.")
    add_launcher_args(parser)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
