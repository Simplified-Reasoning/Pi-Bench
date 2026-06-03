from __future__ import annotations

from pathlib import Path

from pytest import approx

from src.docker_launcher import (
    APPWORLD_ROOT_CONTAINER,
    Job,
    ScorePair,
    _create_container,
    _discover_user_ids,
    _latest_runtime_status,
    _prepare_runtime_appworld_dir,
    _prepare_runtime_data_dir,
    _score_summary,
    _score_summary_by_run_average,
    _split_rerun_failed_jobs,
)


def _write_user(root: Path, user_id: str) -> None:
    user_root = root / "data" / user_id
    user_root.mkdir(parents=True)
    (user_root / "profile.yaml").write_text(f"user_id: {user_id}\n", encoding="utf-8")
    (user_root / "episode.yaml").write_text(f"user_id: {user_id}\n", encoding="utf-8")


def test_discover_user_ids_returns_all_valid_data_users(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    _write_user(tmp_path, "researcher")
    _write_user(tmp_path, "law_trainee")
    (tmp_path / "data" / "scratch").mkdir()

    assert _discover_user_ids(tmp_path) == ["law_trainee", "researcher"]


def test_prepare_runtime_data_dir_uses_isolated_copy(tmp_path: Path) -> None:
    source_task = tmp_path / "data" / "researcher" / "tasks" / "task_001"
    source_task.mkdir(parents=True)
    source_file = source_task / "task.md"
    source_file.write_text("original\n", encoding="utf-8")
    other_user = tmp_path / "data" / "marketer"
    other_user.mkdir(parents=True)
    job = _job(tmp_path / "outputs", "model__run01", "researcher")

    runtime_data_dir = _prepare_runtime_data_dir(tmp_path, job, reset=True)
    runtime_file = runtime_data_dir / "researcher" / "tasks" / "task_001" / "task.md"
    runtime_file.write_text("container edit\n", encoding="utf-8")

    assert runtime_data_dir == job.runtime_dir / "data"
    assert not (runtime_data_dir / "marketer").exists()
    assert runtime_file.read_text(encoding="utf-8") == "container edit\n"
    assert source_file.read_text(encoding="utf-8") == "original\n"


def test_prepare_runtime_data_dir_keeps_existing_copy_when_reset_is_false(tmp_path: Path) -> None:
    source_user = tmp_path / "data" / "researcher"
    source_user.mkdir(parents=True)
    (source_user / "profile.yaml").write_text("source\n", encoding="utf-8")
    job = _job(tmp_path / "outputs", "model__run01", "researcher")
    runtime_user = job.runtime_dir / "data" / "researcher"
    runtime_user.mkdir(parents=True)
    runtime_file = runtime_user / "profile.yaml"
    runtime_file.write_text("kept\n", encoding="utf-8")

    runtime_data_dir = _prepare_runtime_data_dir(tmp_path, job, reset=False)

    assert runtime_data_dir == job.runtime_dir / "data"
    assert runtime_file.read_text(encoding="utf-8") == "kept\n"


def test_prepare_runtime_data_dir_replaces_existing_copy_when_reset_is_true(tmp_path: Path) -> None:
    source_user = tmp_path / "data" / "researcher"
    source_user.mkdir(parents=True)
    (source_user / "profile.yaml").write_text("source\n", encoding="utf-8")
    job = _job(tmp_path / "outputs", "model__run01", "researcher")
    runtime_user = job.runtime_dir / "data" / "researcher"
    runtime_user.mkdir(parents=True)
    runtime_file = runtime_user / "profile.yaml"
    runtime_file.write_text("stale\n", encoding="utf-8")

    _prepare_runtime_data_dir(tmp_path, job, reset=True)

    assert runtime_file.read_text(encoding="utf-8") == "source\n"


def test_prepare_runtime_appworld_dir_uses_isolated_copy(tmp_path: Path) -> None:
    source_root = tmp_path / "third_party" / "appworld"
    source_root.mkdir(parents=True)
    source_file = source_root / "pyproject.toml"
    source_file.write_text("source\n", encoding="utf-8")
    (source_root / ".git").mkdir()
    (source_root / ".git" / "config").write_text("git metadata\n", encoding="utf-8")
    job = _job(tmp_path / "outputs", "model__run01", "researcher")

    runtime_appworld_dir = _prepare_runtime_appworld_dir(tmp_path, job, reset=True)
    runtime_file = runtime_appworld_dir / "pyproject.toml"
    runtime_file.write_text("container edit\n", encoding="utf-8")

    assert runtime_appworld_dir == job.runtime_dir / "appworld"
    assert runtime_file.read_text(encoding="utf-8") == "container edit\n"
    assert source_file.read_text(encoding="utf-8") == "source\n"
    assert not (runtime_appworld_dir / ".git").exists()


def test_create_container_mounts_runtime_appworld_copy(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    _write_user(repo_root, "researcher")
    (repo_root / "src").mkdir()
    (repo_root / "config" / "models").mkdir(parents=True)
    (repo_root / "config" / "models" / "example.yaml").write_text(
        "model:\n  provider: custom\n  model: openai/gpt-test\n  api_key: test-key\n",
        encoding="utf-8",
    )
    (repo_root / "config" / "bench" / "evaluation").mkdir(parents=True)
    (repo_root / "scripts").mkdir()
    (repo_root / "scripts" / "entrypoint.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (repo_root / "third_party" / "nanobot").mkdir(parents=True)
    source_appworld = repo_root / "third_party" / "appworld"
    source_appworld.mkdir(parents=True)
    (source_appworld / "pyproject.toml").write_text("source\n", encoding="utf-8")
    job = Job(
        user_id="researcher",
        model_id="example",
        run_model_id="example",
        model_config_host_path=repo_root / "config" / "models" / "example.yaml",
        runtime_dir=repo_root / "outputs" / "example" / "researcher" / "run" / "20260101_000000-runtime",
        service_logs_dir=repo_root / "outputs" / "example" / "researcher" / "run" / "20260101_000000-runtime" / "service-logs",
        container_name="bench-test",
    )
    commands: list[list[str]] = []

    def fake_check_output(cmd, *, text):
        commands.append(cmd)
        return "container-id\n"

    def fake_run(cmd, **kwargs):
        class Result:
            stdout = "inspect\n"

        commands.append(cmd)
        return Result()

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            commands.append(cmd)

    monkeypatch.setattr("src.docker_launcher.subprocess.check_output", fake_check_output)
    monkeypatch.setattr("src.docker_launcher.subprocess.run", fake_run)
    monkeypatch.setattr("src.docker_launcher.subprocess.Popen", FakePopen)

    _create_container(
        repo_root=repo_root,
        output_root=repo_root / "outputs",
        image_name="image",
        job=job,
        task_ids=[],
        enable_appworld=True,
        remove_existing_runtime=True,
    )

    create_cmd = commands[0]
    runtime_appworld = job.runtime_dir / "appworld"
    assert f"{runtime_appworld}:{APPWORLD_ROOT_CONTAINER}" in create_cmd
    assert f"{source_appworld}:{APPWORLD_ROOT_CONTAINER}" not in create_cmd
    assert runtime_appworld.is_dir()


def test_run_average_summary_std_uses_run_level_averages() -> None:
    pairs_by_run = {
        "model__run01": [
            ScorePair(comp=0.0, proc=0.2),
            ScorePair(comp=1.0, proc=0.8),
        ],
        "model__run02": [
            ScorePair(comp=0.6, proc=0.4),
            ScorePair(comp=0.8, proc=1.0),
        ],
    }

    summary = _score_summary_by_run_average(pairs_by_run, include_std=True)
    flattened_summary = _score_summary(
        [pair for pairs in pairs_by_run.values() for pair in pairs],
        include_std=True,
    )

    assert summary is not None
    assert summary.comp == approx(0.6)
    assert summary.proc == approx(0.6)
    assert summary.comp_std == approx(0.1414213562)
    assert summary.proc_std == approx(0.1414213562)
    assert flattened_summary is not None
    assert flattened_summary.comp_std != approx(summary.comp_std)
    assert flattened_summary.proc_std != approx(summary.proc_std)


def _job(output_root: Path, run_model_id: str, user_id: str = "researcher") -> Job:
    return Job(
        user_id=user_id,
        model_id=run_model_id.split("__run", 1)[0],
        run_model_id=run_model_id,
        model_config_host_path=Path("config/models/example.yaml"),
        runtime_dir=output_root / run_model_id / user_id / "run" / "20260101_000000-runtime",
        service_logs_dir=output_root / run_model_id / user_id / "run" / "20260101_000000-runtime" / "service-logs",
        container_name=f"bench-{run_model_id}-{user_id}",
    )


def _write_runtime(job: Job, timestamp: str, exit_code: int) -> Path:
    runtime_dir = job.runtime_dir.parent / f"{timestamp}-runtime"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "inspect.summary.log").write_text(
        f"status=exited exit_code={exit_code} started_at=x finished_at=y oom_killed=false error=\n",
        encoding="utf-8",
    )
    return runtime_dir


def test_latest_runtime_status_uses_latest_attempt(tmp_path: Path) -> None:
    job = _job(tmp_path, "model__run01")
    _write_runtime(job, "20260101_000000", 0)
    latest_runtime = _write_runtime(job, "20260101_010000", 137)

    status = _latest_runtime_status(job)

    assert status is not None
    assert status.runtime_dir == latest_runtime
    assert status.exit_code == 137


def test_split_rerun_failed_jobs_reruns_entire_failed_repeat(tmp_path: Path) -> None:
    run01_researcher = _job(tmp_path, "model__run01", "researcher")
    run01_marketer = _job(tmp_path, "model__run01", "marketer")
    run02_researcher = _job(tmp_path, "model__run02", "researcher")
    run02_marketer = _job(tmp_path, "model__run02", "marketer")
    run03_researcher = _job(tmp_path, "model__run03", "researcher")

    latest_passed_runtime = _write_runtime(run01_researcher, "20260101_010000", 0)
    _write_runtime(run01_marketer, "20260101_010000", 0)
    _write_runtime(run02_researcher, "20260101_010000", 0)
    _write_runtime(run02_marketer, "20260101_010000", 1)

    cached_runs, jobs_to_run = _split_rerun_failed_jobs(
        [run01_researcher, run01_marketer, run02_researcher, run02_marketer, run03_researcher]
    )

    assert [run.job.run_model_id for run in cached_runs] == ["model__run01", "model__run01"]
    assert cached_runs[0].job.runtime_dir == latest_passed_runtime
    assert all(run.exit_code == 0 and run.proc is None for run in cached_runs)
    assert [(job.run_model_id, job.user_id) for job in jobs_to_run] == [
        ("model__run02", "researcher"),
        ("model__run02", "marketer"),
        ("model__run03", "researcher"),
    ]
