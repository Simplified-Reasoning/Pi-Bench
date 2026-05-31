from __future__ import annotations

from pathlib import Path

from pytest import approx

from src.docker_launcher import (
    Job,
    ScorePair,
    _discover_user_ids,
    _latest_runtime_status,
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
