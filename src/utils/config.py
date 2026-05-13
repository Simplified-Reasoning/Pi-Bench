from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def resolve_path(value: str) -> Path:
    path = Path(os.path.expanduser(value))
    if path.is_absolute():
        return path
    return Path.cwd() / path


def load_yaml_mapping(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"invalid config format: {config_path}")
    return cfg

