from __future__ import annotations

from pathlib import Path

from src.docker_launcher import _discover_user_ids


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
