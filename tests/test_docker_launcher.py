from __future__ import annotations

from pathlib import Path

from pytest import approx

from src.docker_launcher import ScorePair, _discover_user_ids, _score_summary, _score_summary_by_run_average


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
