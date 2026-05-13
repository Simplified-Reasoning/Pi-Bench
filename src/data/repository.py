from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml

from .models import (
    RoleProfile,
    EpisodeSpec,
    HiddenIntentItem,
    TaskSpec,
    ToolTraceSpec,
    VALID_TASK_HIDDEN_INTENT_STATUSES,
)

_ALLOWED_OBJECTIVES_FIELDS = frozenset(
    {"checklist", "files_read", "tools", "tools_evaluation_path"}
)


class UserDataRepository:

    def __init__(self, data_root: str = "data", repo_root: str | Path | None = None):
        self.data_root = Path(data_root)
        if repo_root is None:
            self.repo_root = Path(__file__).resolve().parents[2]
        else:
            self.repo_root = Path(repo_root).resolve()

    def load_user(
            self, user_id: str
    ) -> tuple[RoleProfile, EpisodeSpec, Dict[str, TaskSpec]]:
        user_root = self.data_root / user_id
        profile = self._load_profile(user_root / "profile.yaml")
        episode = self._load_episode(user_root / "episode.yaml")
        tasks_dir = user_root / "tasks"
        tasks: Dict[str, TaskSpec] = {}
        if tasks_dir.exists():
            for task_path in tasks_dir.glob("*/task.yaml"):
                task = self._load_task(task_path)
                tasks[task.task_id] = task
        return profile, episode, tasks

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Invalid yaml content in {path}")
        return data

    def _load_profile(self, path: Path) -> RoleProfile:
        data = self._load_yaml(path)
        user_id = str(data.get("user_id", ""))
        role = data.get("role") or ""
        role_text = role if isinstance(role, str) else str(
            role.get("role_text", ""))
        preferences = data.get("preferences") or {}
        long_term_goals = data.get("long_term_goals") or []
        return RoleProfile(
            user_id=user_id,
            role_text=role_text,
            preferences=preferences,
            long_term_goals=long_term_goals,
        )

    def _load_episode(self, path: Path) -> EpisodeSpec:
        data = self._load_yaml(path)
        runtime = data.get("runtime") or {}
        docker_image_id = str(runtime.get("docker_image_id", ""))
        task_order = [
            t["task_id"] for t in data.get("tasks", []) if "task_id" in t
        ]
        return EpisodeSpec(
            episode_id=str(data.get("episode_id", "")),
            user_id=str(data.get("user_id", "")),
            docker_image_id=docker_image_id,
            task_order=task_order,
            raw=data,
        )

    def _load_task(self, path: Path) -> TaskSpec:
        data = self._load_yaml(path)
        schema_version = str(data.get("schema_version", "")).strip()
        if schema_version != "v2":
            raise ValueError(
                f"Unsupported task schema_version in {path}: {schema_version!r}"
            )

        trigger = data.get("trigger") or {}
        intent = data.get("intent") or {}
        objectives = data.get("objectives") or {}
        metadata = data.get("metadata") or {}

        if not isinstance(objectives, dict):
            raise ValueError(f"Invalid objectives in {path}: expected mapping")
        if "tools_checklist" in objectives:
            raise ValueError(
                f"Invalid objectives.tools_checklist in {path}: "
                "field has been removed; use objectives.tools_evaluation_path instead"
            )
        unexpected_objectives_fields = sorted(
            key for key in objectives.keys() if key not in _ALLOWED_OBJECTIVES_FIELDS
        )
        if unexpected_objectives_fields:
            unexpected = ", ".join(unexpected_objectives_fields)
            allowed = ", ".join(sorted(_ALLOWED_OBJECTIVES_FIELDS))
            raise ValueError(
                f"Invalid objectives in {path}: unexpected fields: {unexpected}. "
                f"Allowed fields: {allowed}."
            )

        if "detailed_intent" in intent:
            raise ValueError(
                f"task schema v2 does not allow intent.detailed_intent in {path}"
            )

        raw_hidden_intents = intent.get("hidden_intent")
        if not isinstance(raw_hidden_intents, list) or not raw_hidden_intents:
            raise ValueError(
                f"task schema v2 requires a non-empty intent.hidden_intent list in {path}"
            )

        hidden_intents: list[HiddenIntentItem] = []
        for idx, item in enumerate(raw_hidden_intents, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"invalid hidden_intent item at index {idx} in {path}")
            content = str(item.get("content", "")).strip()
            if not content:
                raise ValueError(
                    f"empty hidden_intent content at index {idx} in {path}")
            status = str(item.get("status", "not_provided")).strip()
            if status not in VALID_TASK_HIDDEN_INTENT_STATUSES:
                allowed = ", ".join(VALID_TASK_HIDDEN_INTENT_STATUSES)
                raise ValueError(
                    f"invalid hidden_intent status at index {idx} in {path}: {status!r}. "
                    f"Allowed: {allowed}"
                )
            hidden_intents.append(
                HiddenIntentItem(content=content, status=status))

        tool_trace_specs = self._parse_tool_trace_specs(
            objectives=objectives,
            source_path=path,
        )
        checklist = self._parse_checklist_objectives(
            objectives=objectives,
            source_path=path,
        )
        tools_evaluation_path = self._parse_tools_evaluation_path(
            objectives=objectives,
            source_path=path,
        )

        files_read = [
            str(item).strip()
            for item in objectives.get("files_read", []) or []
            if str(item).strip()
        ]

        return TaskSpec(
            schema_version=schema_version,
            task_id=str(data.get("task_id", "")),
            user_id=str(data.get("user_id", "")),
            environment_id=str(data.get("environment_id", "")),
            task_dir=path.parent,
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            task_type=str(data.get("task_type", "")),
            metadata=metadata
            if isinstance(metadata, dict) else {"value": metadata},
            trigger_type=str(trigger.get("type", "")),
            initial_input=str(intent.get("initial_input", "")),
            hidden_intents=hidden_intents,
            files_read=files_read,
            objectives=checklist,
            tool_trace_specs=tool_trace_specs,
            tools_evaluation_path=tools_evaluation_path,
            raw=data,
        )

    def _parse_tool_trace_specs(
        self,
        *,
        objectives: dict[str, Any],
        source_path: Path,
    ) -> list[ToolTraceSpec]:
        raw_tools = objectives.get("tools") or []
        if not isinstance(raw_tools, list):
            raise ValueError(f"Invalid objectives.tools in {source_path}: expected list")

        parsed_specs: list[ToolTraceSpec] = []
        for idx, raw_item in enumerate(raw_tools, start=1):
            tool_name, tool_cfg = self._parse_named_tool_config(
                raw_item=raw_item,
                source_path=source_path,
                context=f"objectives.tools[{idx}]",
            )
            call_paths = self._parse_path_list(
                raw_value=tool_cfg.get("call", []),
                source_path=source_path,
                context=f"objectives.tools[{idx}].{tool_name}.call",
            )
            result_paths = self._parse_path_list(
                raw_value=tool_cfg.get("result", []),
                source_path=source_path,
                context=f"objectives.tools[{idx}].{tool_name}.result",
            )
            if not call_paths and not result_paths:
                raise ValueError(
                    f"Invalid objectives.tools in {source_path}: {tool_name} must declare call or result paths"
                )
            parsed_specs.append(
                ToolTraceSpec(
                    tool_name=tool_name,
                    call_paths=call_paths,
                    result_paths=result_paths,
                )
            )
        return parsed_specs

    def _parse_checklist_objectives(
        self,
        *,
        objectives: dict[str, Any],
        source_path: Path,
    ) -> list[dict[str, Any]]:
        raw_checklist = objectives.get("checklist", []) or []
        if not isinstance(raw_checklist, list):
            raise ValueError(f"Invalid objectives.checklist in {source_path}: expected list")

        parsed: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_checklist, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Invalid objectives.checklist[{idx}] in {source_path}: expected mapping"
                )
            if "tools" in item:
                raise ValueError(
                    "Invalid objectives.checklist["
                    f"{idx}] in {source_path}: field 'tools' is not supported under objectives.checklist"
                )

            criterion = str(item.get("criterion", "")).strip()
            if not criterion:
                continue

            weight_raw = item.get("weight", 1)
            try:
                weight = float(weight_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid checklist weight in {source_path}: {weight_raw!r}"
                ) from exc
            if weight <= 0:
                raise ValueError(
                    f"Checklist weight must be > 0 in {source_path}: {weight_raw!r}"
                )

            if criterion:
                parsed.append(
                    {
                        "criterion": criterion,
                        "weight": weight,
                        "evaluation": "llm",
                    }
                )
        return parsed

    def _parse_tools_evaluation_path(
        self,
        *,
        objectives: dict[str, Any],
        source_path: Path,
    ) -> Path | None:
        if "tools_checklist" in objectives:
            raise ValueError(
                f"Invalid objectives.tools_checklist in {source_path}: "
                "field has been removed; use objectives.tools_evaluation_path instead"
            )

        raw_path = objectives.get("tools_evaluation_path")
        if raw_path is None:
            return None
        if not isinstance(raw_path, str):
            raise ValueError(
                f"Invalid objectives.tools_evaluation_path in {source_path}: expected string path"
            )

        path_text = raw_path.strip()
        if not path_text:
            raise ValueError(
                f"Invalid objectives.tools_evaluation_path in {source_path}: path must be non-empty"
            )

        path = Path(path_text)
        resolved = path.resolve() if path.is_absolute() else (self.repo_root / path).resolve()
        if resolved.suffix != ".py":
            raise ValueError(
                f"Invalid objectives.tools_evaluation_path in {source_path}: expected .py file path, got {path_text!r}"
            )
        if not resolved.is_file():
            raise FileNotFoundError(
                f"Invalid objectives.tools_evaluation_path in {source_path}: file not found: {resolved}"
            )
        return resolved

    def _parse_named_tool_config(
        self,
        *,
        raw_item: Any,
        source_path: Path,
        context: str,
        allow_list_wrapped_config: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        if not isinstance(raw_item, dict):
            raise ValueError(f"Invalid {context} in {source_path}: expected mapping")

        known_cfg_fields = {"call", "result"}
        tool_name_keys = [key for key in raw_item.keys() if str(key) not in known_cfg_fields]
        if len(tool_name_keys) != 1:
            raise ValueError(
                f"Invalid {context} in {source_path}: expected exactly one tool name key"
            )
        tool_name = str(tool_name_keys[0]).strip()
        if not tool_name:
            raise ValueError(f"Invalid {context} in {source_path}: tool name must be non-empty")

        raw_cfg = raw_item.get(tool_name_keys[0])
        cfg: dict[str, Any]
        if raw_cfg is None:
            cfg = {}
        elif isinstance(raw_cfg, dict):
            cfg = dict(raw_cfg)
        elif allow_list_wrapped_config and isinstance(raw_cfg, list) and len(raw_cfg) == 1 and isinstance(raw_cfg[0], dict):
            cfg = dict(raw_cfg[0])
        else:
            raise ValueError(
                f"Invalid {context}.{tool_name} in {source_path}: expected mapping"
            )

        for field in known_cfg_fields:
            if field in raw_item and field not in cfg:
                cfg[field] = raw_item[field]
        return tool_name, cfg

    def _parse_path_list(
        self,
        *,
        raw_value: Any,
        source_path: Path,
        context: str,
    ) -> list[str]:
        if raw_value is None:
            return []
        if not isinstance(raw_value, list):
            raise ValueError(f"Invalid {context} in {source_path}: expected list")
        parsed_paths: list[str] = []
        for idx, item in enumerate(raw_value, start=1):
            path = str(item).strip()
            if not path:
                raise ValueError(f"Invalid {context}[{idx}] in {source_path}: path must be non-empty")
            parsed_paths.append(path)
        return parsed_paths


TASK_WORKSPACE_ASSET_BLACKLIST = frozenset({
    "task.yaml",
    ".history",
    ".result",
    ".eval_result",
})


def list_task_workspace_assets(task: TaskSpec) -> list[Path]:
    if not task.task_dir.exists():
        return []
    return sorted(
        (path for path in task.task_dir.iterdir()
         if path.name not in TASK_WORKSPACE_ASSET_BLACKLIST),
        key=lambda item: item.name,
    )
