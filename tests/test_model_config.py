from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.runtime.model_config import (
    load_model_config,
    referenced_config_env_vars,
    write_runtime_files,
)


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_load_model_config_keeps_default_env_placeholders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "MODEL_BASE_URL",
        "MODEL_API_KEY",
        "USER_BASE_URL",
        "USER_API_KEY",
        "JUDGER_BASE_URL",
        "JUDGER_API_KEY",
        "BRAVE_SEARCH_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    config_path = _write_yaml(tmp_path / "model.yaml", {})

    cfg = load_model_config(config_path, model_id="demo")

    assert cfg["model"]["base_url"] == "${MODEL_BASE_URL}"
    assert cfg["user_agent"]["api_key"] == "${USER_API_KEY}"
    assert cfg["judger"]["base_url"] == "${JUDGER_BASE_URL}"
    assert cfg["tools"]["brave_search_api_key"] == "${BRAVE_SEARCH_API_KEY}"


def test_load_model_config_resolve_env_fails_with_clear_missing_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_BASE_URL", raising=False)
    config_path = _write_yaml(tmp_path / "model.yaml", {})

    with pytest.raises(ValueError, match=r"model\.base_url.*MODEL_BASE_URL"):
        load_model_config(config_path, model_id="demo", resolve_env=True)


def test_referenced_env_vars_include_defaults_after_merge() -> None:
    assert referenced_config_env_vars({"model": {"base_url": "https://example.test/v1"}}) == {
        "MODEL_API_KEY",
        "USER_BASE_URL",
        "USER_API_KEY",
        "JUDGER_BASE_URL",
        "JUDGER_API_KEY",
        "BRAVE_SEARCH_API_KEY",
    }


def test_write_runtime_files_resolves_env_only_at_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_values = {
        "MODEL_BASE_URL": "https://model.example/v1",
        "MODEL_API_KEY": "model-key",
        "USER_BASE_URL": "https://user.example/v1",
        "USER_API_KEY": "user-key",
        "JUDGER_BASE_URL": "https://judge.example/v1",
        "JUDGER_API_KEY": "judge-key",
        "BRAVE_SEARCH_API_KEY": "brave-key",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    config_path = _write_yaml(tmp_path / "demo.yaml", {"model": {"model": "provider/demo"}})
    bench_path = tmp_path / "runtime" / "bench.yaml"
    nanobot_path = tmp_path / "runtime" / "nanobot.json"

    write_runtime_files(
        model_config_path=config_path,
        bench_config_path=bench_path,
        nanobot_config_path=nanobot_path,
        model_id="demo",
        user_id="law_trainee",
        task_ids=["law_trainee_task_001"],
        trace_logs_dir=tmp_path / "traces",
        workspace_dir=tmp_path / "workspace",
        output_dir=tmp_path / "outputs",
        history_config_path=Path("config/bench/evaluation/trace_history.yaml"),
        test_server_url="http://127.0.0.1:9999",
        appworld_mcp_url="http://127.0.0.1:10000/mcp",
        enable_appworld=True,
    )

    bench_cfg = yaml.safe_load(bench_path.read_text(encoding="utf-8"))
    nanobot_cfg = json.loads(nanobot_path.read_text(encoding="utf-8"))

    assert bench_cfg["run"]["interaction"]["llm"]["base_url"] == "https://user.example/v1"
    assert bench_cfg["run"]["evaluation"]["llm"]["api_key"] == "judge-key"
    assert nanobot_cfg["providers"]["custom"]["apiBase"] == "https://model.example/v1"
    assert nanobot_cfg["tools"]["web"]["search"]["apiKey"] == "brave-key"
