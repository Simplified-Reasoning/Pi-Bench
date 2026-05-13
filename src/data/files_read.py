from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import TaskSpec

FILE_MISSING_PLACEHOLDER = "[file missing]"
TRUNCATED_SUFFIX = "...[truncated]"


@dataclass(frozen=True)
class TaskFileReadEntry:
    name: str
    content: str
    exists: bool


def parse_files_read_truncate_chars(config: Mapping[str, Any], *, source: str) -> int:
    text_policy_cfg = config.get("text_policy")
    if not isinstance(text_policy_cfg, Mapping):
        raise ValueError(f"{source}: config.text_policy must be a mapping")
    field_overrides_cfg = text_policy_cfg.get("field_overrides")
    if not isinstance(field_overrides_cfg, Mapping):
        raise ValueError(f"{source}: config.text_policy.field_overrides must be a mapping")
    files_read_cfg = field_overrides_cfg.get("files_read")
    if not isinstance(files_read_cfg, Mapping):
        raise ValueError(f"{source}: config.text_policy.field_overrides.files_read must be a mapping")

    raw_value = files_read_cfg.get("truncate_chars")
    try:
        truncate_chars = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{source}: config.text_policy.field_overrides.files_read.truncate_chars must be an integer >= 0"
        ) from exc
    if truncate_chars < 0:
        raise ValueError(
            f"{source}: config.text_policy.field_overrides.files_read.truncate_chars must be an integer >= 0"
        )
    return truncate_chars


def load_files_read_truncate_chars(config_path: Path) -> int:
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, Mapping):
        raise ValueError(f"invalid config format: {config_path}")
    return parse_files_read_truncate_chars(config, source=f"trace history config {config_path}")


def truncate_files_read_content(text: str, *, truncate_chars: int) -> str:
    if truncate_chars <= 0 or len(text) <= truncate_chars:
        return text
    return text[:truncate_chars] + TRUNCATED_SUFFIX


def load_task_files_read_entries(
    *,
    task: TaskSpec,
    workspace_dir: Path | None,
    truncate_chars: int = 0,
) -> list[TaskFileReadEntry]:
    if workspace_dir is None:
        return []

    attached_files: list[TaskFileReadEntry] = []
    for file_name in list(getattr(task, "files_read", [])):
        file_path = Path(file_name)
        resolved_path = file_path if file_path.is_absolute() else workspace_dir / file_path
        if not resolved_path.exists() or not resolved_path.is_file():
            attached_files.append(
                TaskFileReadEntry(
                    name=file_name,
                    content=FILE_MISSING_PLACEHOLDER,
                    exists=False,
                )
            )
            continue
        attached_files.append(
            TaskFileReadEntry(
                name=file_name,
                content=truncate_files_read_content(
                    resolved_path.read_text(encoding="utf-8"),
                    truncate_chars=truncate_chars,
                ),
                exists=True,
            )
        )
    return attached_files
