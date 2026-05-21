from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from ..utils import load_yaml_mapping, resolve_path


DEFAULT_MODEL_CONFIG: dict[str, Any] = {
    "model": {
        "provider": "custom",
        "base_url": "${MODEL_BASE_URL}",
        "api_key": "${MODEL_API_KEY}",
        "max_tokens": 16384,
        "max_tool_iterations": 120,
        "memory_window": 100,
        "reasoning_effort": None,
        "extra_headers": None,
    },
    "user_agent": {
        "model": "gpt-5.4",
        "base_url": "${USER_BASE_URL}",
        "api_key": "${USER_API_KEY}",
        "temperature": 0.0,
        "request_timeout": 360.0,
        "max_concurrency": 32,
        "max_retries": 4,
    },
    "judger": {
        "model": "gpt-5.4",
        "base_url": "${JUDGER_BASE_URL}",
        "api_key": "${JUDGER_API_KEY}",
        "temperature": 0.0,
        "request_timeout": 360.0,
        "max_concurrency": 128,
        "max_retries": 4,
        "reasoning_effort": "high",
    },
    "tools": {
        "brave_search_api_key": "${BRAVE_SEARCH_API_KEY}",
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

ENV_PLACEHOLDERS = {
    "model": {
        "base_url": {
            "${MODEL_BASE_URL}": "MODEL_BASE_URL",
        },
        "api_key": {
            "${MODEL_API_KEY}": "MODEL_API_KEY",
        },
    },
    "user_agent": {
        "base_url": {
            "${USER_BASE_URL}": "USER_BASE_URL",
        },
        "api_key": {
            "${USER_API_KEY}": "USER_API_KEY",
        },
    },
    "judger": {
        "base_url": {
            "${JUDGER_BASE_URL}": "JUDGER_BASE_URL",
        },
        "api_key": {
            "${JUDGER_API_KEY}": "JUDGER_API_KEY",
        },
    },
    "tools": {
        "brave_search_api_key": {
            "${BRAVE_SEARCH_API_KEY}": "BRAVE_SEARCH_API_KEY",
        },
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


def load_model_config(path: Path, *, model_id: str | None = None, resolve_env: bool = False) -> dict[str, Any]:
    cfg = _deep_merge(DEFAULT_MODEL_CONFIG, load_yaml_mapping(path))
    if resolve_env:
        _resolve_model_config_env_refs(cfg, strict=True)
    inferred_model_id = model_id or path.stem
    model_cfg = cfg.setdefault("model", {})
    model_cfg.setdefault("id", inferred_model_id)
    if not str(model_cfg.get("model") or "").strip():
        model_cfg["model"] = inferred_model_id
    return cfg


def _resolve_env_ref(value: Any, *, key: str, section_name: str, strict: bool) -> Any:
    if not isinstance(value, str):
        return value
    env_name = ENV_PLACEHOLDERS.get(section_name, {}).get(key, {}).get(value.strip())
    if env_name is None:
        return value
    env_value = os.getenv(env_name, "").strip()
    if not env_value:
        if strict:
            raise ValueError(
                f"{section_name}.{key} references ${{{env_name}}}, "
                f"but environment variable {env_name} is empty"
            )
        return value
    return env_value


def resolve_llm_env_refs(raw: dict[str, Any], *, section_name: str, strict: bool = True) -> dict[str, Any]:
    if section_name == "config.run.interaction.llm":
        section_name = "user_agent"
    elif section_name == "config.run.evaluation.llm":
        section_name = "judger"

    resolved = dict(raw)
    for key in ("base_url", "api_key"):
        if key in resolved:
            resolved[key] = _resolve_env_ref(resolved[key], key=key, section_name=section_name, strict=strict)
    return resolved


def resolve_tools_env_refs(raw: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
    resolved = dict(raw)
    key = "brave_search_api_key"
    if key in resolved:
        resolved[key] = _resolve_env_ref(resolved[key], key=key, section_name="tools", strict=strict)
    return resolved


def _resolve_model_config_env_refs(cfg: dict[str, Any], *, strict: bool) -> None:
    for section_name in ("model", "user_agent", "judger"):
        section = cfg.get(section_name)
        if not isinstance(section, dict):
            continue
        section.update(resolve_llm_env_refs(section, section_name=section_name, strict=strict))
    tools_cfg = cfg.get("tools")
    if isinstance(tools_cfg, dict):
        tools_cfg.update(resolve_tools_env_refs(tools_cfg, strict=strict))


def referenced_config_env_vars(raw: dict[str, Any]) -> set[str]:
    cfg = _deep_merge(DEFAULT_MODEL_CONFIG, raw)
    env_vars: set[str] = set()
    for section_name, section_placeholders in ENV_PLACEHOLDERS.items():
        section = cfg.get(section_name)
        if not isinstance(section, dict):
            continue
        for key, placeholders in section_placeholders.items():
            value = section.get(key)
            if isinstance(value, str):
                env_name = placeholders.get(value.strip())
                if env_name:
                    env_vars.add(env_name)
    return env_vars


def _require_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must be a mapping")
    return raw


def normalize_llm_config(
    raw: dict[str, Any],
    *,
    section_name: str,
    default_temperature: float | None = 0.0,
    resolve_env: bool = True,
) -> dict[str, Any]:
    if resolve_env:
        raw = resolve_llm_env_refs(raw, section_name=section_name, strict=True)
    llm = {
        "model": raw.get("model"),
        "base_url": raw.get("base_url"),
        "api_key": raw.get("api_key"),
        "temperature": raw.get("temperature", default_temperature),
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
    if llm["temperature"] is None:
        raise ValueError(f"{section_name}.temperature is required")
    llm["model"] = str(llm["model"]).strip()
    llm["base_url"] = str(llm["base_url"]).strip()
    llm["api_key"] = str(llm["api_key"]).strip()
    llm["temperature"] = float(llm["temperature"])
    llm["request_timeout"] = float(llm["request_timeout"])
    llm["max_concurrency"] = int(llm["max_concurrency"])
    llm["max_retries"] = int(llm["max_retries"])
    if llm["request_timeout"] <= 0:
        raise ValueError(f"{section_name}.request_timeout must be > 0")
    if llm["max_concurrency"] < 1:
        raise ValueError(f"{section_name}.max_concurrency must be >= 1")
    if llm["max_retries"] < 1:
        raise ValueError(f"{section_name}.max_retries must be >= 1")
    extra_kwargs = llm.get("extra_kwargs")
    if isinstance(extra_kwargs, str):
        try:
            llm["extra_kwargs"] = json.loads(extra_kwargs)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{section_name}.extra_kwargs must be valid JSON object string") from exc
        extra_kwargs = llm["extra_kwargs"]
    if extra_kwargs is not None and not isinstance(extra_kwargs, dict):
        raise ValueError(f"{section_name}.extra_kwargs must be a mapping or JSON object string")
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
                "llm": normalize_llm_config(
                    _require_mapping(model_cfg.get("user_agent"), "user_agent"),
                    section_name="user_agent",
                ),
            },
            "evaluation": {
                "model_id": model_id,
                "user_id": selected_user_id,
                "scoring": str(run_cfg.get("scoring", "both")),
                "history_config_path": str(selected_history_config_path),
                "llm": normalize_llm_config(
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
    agent_cfg = resolve_llm_env_refs(
        _require_mapping(model_cfg.get("model"), "model"),
        section_name="model",
        strict=True,
    )
    tools_cfg = resolve_tools_env_refs(_require_mapping(model_cfg.get("tools"), "tools"), strict=True)
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
    model_cfg = load_model_config(model_config_path, model_id=model_config_path.stem, resolve_env=True)
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
