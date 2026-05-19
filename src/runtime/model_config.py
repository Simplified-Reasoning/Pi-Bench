from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from ..utils import load_yaml_mapping, resolve_path


DEFAULT_MODEL_CONFIG: dict[str, Any] = {
    "model": {
        "provider": "custom",
        "base_url": "https://api.example.com/v1",
        "api_key": "__SET_BY_CONFIG__",
        "max_tokens": 16384,
        "max_tool_iterations": 120,
        "memory_window": 100,
        "reasoning_effort": None,
        "extra_headers": None,
    },
    "user_agent": {
        "model": "gpt-5.4",
        "base_url": "https://api.example.com/v1",
        "api_key": "__SET_BY_CONFIG__",
        "temperature": 0.0,
        "request_timeout": 360.0,
        "max_concurrency": 32,
        "max_retries": 4,
    },
    "judger": {
        "model": "gpt-5.4",
        "base_url": "https://api.example.com/v1",
        "api_key": "__SET_BY_CONFIG__",
        "temperature": 0.0,
        "request_timeout": 360.0,
        "max_concurrency": 128,
        "max_retries": 4,
        "reasoning_effort": "high",
    },
    "tools": {
        "brave_search_api_key": "",
        "web_search_max_results": 10,
        "exec_timeout": 60,
        "exec_path_append": "",
        "restrict_to_workspace": False,
    },
    "proxy": {
        "http_proxy": None,
        "https_proxy": None,
        "no_proxy": None,
    },
    "nanobot": {
        "trace_logs_dir": "~/.nanobot/trace_logs",
        "workspace_dir": "~/.nanobot/workspace",
        "copy_task_assets_to_workspace": True,
        "gateway_host": "0.0.0.0",
        "gateway_port": 18790,
        "heartbeat_enabled": True,
        "heartbeat_interval_seconds": 1800,
    },
    "run": {
        "mode": "run",
        "output_dir": "outputs",
        "log_level": "INFO",
        "user_id": "law_trainee",
        "user_mode": "llm",
        "turn_timeout": 2400.0,
        "task_ids": [],
        "scoring": "both",
        "history_config_path": "config/bench/evaluation/trace_history.yaml",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_model_config(path: Path, *, model_id: str | None = None) -> dict[str, Any]:
    cfg = _deep_merge(DEFAULT_MODEL_CONFIG, load_yaml_mapping(path))
    inferred_model_id = model_id or path.stem
    model_cfg = cfg.setdefault("model", {})
    model_cfg.setdefault("id", inferred_model_id)
    if not str(model_cfg.get("model") or "").strip():
        model_cfg["model"] = inferred_model_id
    return cfg


def _require_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must be a mapping")
    return raw


def _llm_config(raw: dict[str, Any], *, section_name: str) -> dict[str, Any]:
    llm = {
        "model": raw.get("model"),
        "base_url": raw.get("base_url"),
        "api_key": raw.get("api_key"),
        "temperature": raw.get("temperature", 0.0),
        "request_timeout": raw.get("request_timeout", 60.0),
        "max_concurrency": raw.get("max_concurrency", 1),
        "max_retries": raw.get("max_retries", 16),
    }
    for key, value in raw.items():
        if key not in llm:
            llm[key] = value
    for key in ("model", "base_url", "api_key"):
        if not str(llm.get(key) or "").strip():
            raise ValueError(f"{section_name}.{key} is required")
    return llm


def build_bench_runtime_config(
    model_cfg: dict[str, Any],
    *,
    model_id: str,
    user_id: str | None = None,
    task_ids: list[str] | None = None,
    trace_logs_dir: str | Path | None = None,
    workspace_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    history_config_path: str | Path | None = None,
) -> dict[str, Any]:
    run_cfg = _require_mapping(model_cfg.get("run"), "run")
    nanobot_cfg = _require_mapping(model_cfg.get("nanobot"), "nanobot")
    selected_user_id = user_id or str(run_cfg.get("user_id") or "law_trainee")
    selected_task_ids = task_ids if task_ids is not None else run_cfg.get("task_ids", [])
    selected_history_config_path = history_config_path or run_cfg.get(
        "history_config_path", "config/bench/evaluation/trace_history.yaml"
    )

    return {
        "version": 1,
        "nanobot": {
            "trace_logs_dir": str(trace_logs_dir or nanobot_cfg.get("trace_logs_dir")),
            "workspace_dir": str(workspace_dir or nanobot_cfg.get("workspace_dir")),
            "copy_task_assets_to_workspace": bool(nanobot_cfg.get("copy_task_assets_to_workspace", True)),
        },
        "run": {
            "mode": str(run_cfg.get("mode", "run")),
            "output_dir": str(output_dir or run_cfg.get("output_dir", "outputs")),
            "log_level": str(run_cfg.get("log_level", "INFO")),
            "interaction": {
                "model_id": model_id,
                "user_id": selected_user_id,
                "user_mode": str(run_cfg.get("user_mode", "llm")),
                "turn_timeout": float(run_cfg.get("turn_timeout", 2400.0)),
                "task_ids": selected_task_ids,
                "llm": _llm_config(
                    _require_mapping(model_cfg.get("user_agent"), "user_agent"),
                    section_name="user_agent",
                ),
            },
            "evaluation": {
                "model_id": model_id,
                "user_id": selected_user_id,
                "scoring": str(run_cfg.get("scoring", "both")),
                "history_config_path": str(selected_history_config_path),
                "llm": _llm_config(
                    _require_mapping(model_cfg.get("judger"), "judger"),
                    section_name="judger",
                ),
            },
        },
    }


def build_nanobot_runtime_config(
    model_cfg: dict[str, Any],
    *,
    workspace_dir: str | Path,
    test_server_url: str,
    appworld_mcp_url: str,
    enable_appworld: bool,
) -> dict[str, Any]:
    agent_cfg = _require_mapping(model_cfg.get("model"), "model")
    tools_cfg = _require_mapping(model_cfg.get("tools"), "tools")
    nanobot_cfg = _require_mapping(model_cfg.get("nanobot"), "nanobot")

    model_name = str(agent_cfg.get("model") or "").strip()
    base_url = str(agent_cfg.get("base_url") or "").strip()
    api_key = str(agent_cfg.get("api_key") or "").strip()
    if not model_name:
        raise ValueError("model.model is required")
    if not base_url:
        raise ValueError("model.base_url is required")
    if not api_key:
        raise ValueError("model.api_key is required")

    mcp_servers: dict[str, Any] = {}
    if enable_appworld:
        mcp_servers["appworld"] = {
            "url": appworld_mcp_url,
            "headers": {"Accept": "application/json"},
        }

    return {
        "agents": {
            "defaults": {
                "workspace": str(workspace_dir),
                "model": model_name,
                "provider": str(agent_cfg.get("provider", "custom")),
                "maxTokens": int(agent_cfg.get("max_tokens", 16384)),
                "maxToolIterations": int(agent_cfg.get("max_tool_iterations", 120)),
                "memoryWindow": int(agent_cfg.get("memory_window", 100)),
                "reasoningEffort": agent_cfg.get("reasoning_effort"),
            }
        },
        "channels": {
            "sendProgress": False,
            "sendToolHints": False,
            "test_bench": {
                "enabled": True,
                "base_url": test_server_url,
                "poll_timeout": 30,
                "allow_from": ["*"],
            },
        },
        "providers": {
            "custom": {
                "apiKey": api_key,
                "apiBase": base_url,
                "extraHeaders": agent_cfg.get("extra_headers"),
            }
        },
        "gateway": {
            "host": str(nanobot_cfg.get("gateway_host", "0.0.0.0")),
            "port": int(nanobot_cfg.get("gateway_port", 18790)),
            "heartbeat": {
                "enabled": bool(nanobot_cfg.get("heartbeat_enabled", True)),
                "intervalS": int(nanobot_cfg.get("heartbeat_interval_seconds", 1800)),
            },
        },
        "tools": {
            "web": {
                "proxy": "",
                "search": {
                    "apiKey": str(tools_cfg.get("brave_search_api_key") or ""),
                    "maxResults": int(tools_cfg.get("web_search_max_results", 10)),
                },
            },
            "exec": {
                "timeout": int(tools_cfg.get("exec_timeout", 60)),
                "pathAppend": str(tools_cfg.get("exec_path_append") or ""),
            },
            "restrictToWorkspace": bool(tools_cfg.get("restrict_to_workspace", False)),
            "mcpServers": mcp_servers,
        },
    }


def model_proxy_env(model_cfg: dict[str, Any]) -> dict[str, str]:
    proxy_cfg = _require_mapping(model_cfg.get("proxy"), "proxy")
    env: dict[str, str] = {}
    mapping = {
        "http_proxy": "HTTP_PROXY",
        "https_proxy": "HTTPS_PROXY",
        "no_proxy": "NO_PROXY",
    }
    for key, upper_key in mapping.items():
        value = proxy_cfg.get(key)
        if value is None or str(value).strip() == "":
            continue
        text = str(value).strip()
        env[upper_key] = text
        env[upper_key.lower()] = text
    return env


def write_runtime_files(
    *,
    model_config_path: Path,
    bench_config_path: Path,
    nanobot_config_path: Path,
    model_id: str,
    user_id: str,
    task_ids: list[str] | None,
    trace_logs_dir: Path,
    workspace_dir: Path,
    output_dir: Path | None,
    history_config_path: Path,
    test_server_url: str,
    appworld_mcp_url: str,
    enable_appworld: bool,
) -> None:
    model_cfg = load_model_config(model_config_path, model_id=model_config_path.stem)
    bench_cfg = build_bench_runtime_config(
        model_cfg,
        model_id=model_id,
        user_id=user_id,
        task_ids=task_ids,
        trace_logs_dir=trace_logs_dir,
        workspace_dir=workspace_dir,
        output_dir=output_dir,
        history_config_path=history_config_path,
    )
    nanobot_cfg = build_nanobot_runtime_config(
        model_cfg,
        workspace_dir=workspace_dir,
        test_server_url=test_server_url,
        appworld_mcp_url=appworld_mcp_url,
        enable_appworld=enable_appworld,
    )
    bench_config_path.parent.mkdir(parents=True, exist_ok=True)
    nanobot_config_path.parent.mkdir(parents=True, exist_ok=True)
    bench_config_path.write_text(yaml.safe_dump(bench_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    nanobot_config_path.write_text(json.dumps(nanobot_cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_model_config_path(model_id: str, *, config_dir: Path = Path("config/models")) -> Path:
    path = config_dir / f"{model_id}.yaml"
    if path.is_file():
        return resolve_path(str(path))
    yml_path = config_dir / f"{model_id}.yml"
    if yml_path.is_file():
        return resolve_path(str(yml_path))
    return resolve_path(str(path))
