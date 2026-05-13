from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

import yaml

from src.data import (
    TaskFileReadEntry,
    TaskSpec,
    UserDataRepository,
    load_task_files_read_entries,
    parse_files_read_truncate_chars,
)
from src.user_agent.followup_style import (
    TARGETED_FOLLOWUP_STYLES,
    normalize_targeted_followup_style,
)

from ..utils import get_logger, safe_model_id

TURN_FILENAME_INT_PATTERN = re.compile(r"^turn_(\d+)\.json$")
TURN_FILENAME_TS_PATTERN = re.compile(r"^turn_(\d{8})_(\d{6})\.json$")
TRACE_SESSION_DIR_PATTERN = re.compile(r"^\d{8}_\d{6}$")
MESSAGES_HISTORY_FILENAME_PATTERN = re.compile(r"^(\d{8}_\d{6})-messages\.jsonl$")
HISTORY_LOG_FILENAME_PATTERN = re.compile(r"^(\d{8}_\d{6})-log\.jsonl$")
INTENT_SATISFACTION_COMPLETED_PREFIX = "Intent satisfaction completed"
TARGETED_FOLLOWUP_COMPLETED_PREFIX = "Targeted followup completed"
TRACE_VIEWER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "trace_viewer.py"
logger = get_logger("Bench.Evaluation.TraceHistory").profile("eval")
stage_logger = logger.profile("eval_stage")
aux_logger = logger.profile("eval_aux")


@dataclass(frozen=True)
class TaskTurnSession:
    user_id: str
    task_id: str
    session_timestamp: str
    session_dir: Path
    turn_paths: list[Path]


@dataclass(frozen=True)
class FollowupStyleMatch:
    hidden_intent_idx: int
    content: str
    style: str


@dataclass(frozen=True)
class FollowupTurnStyle:
    assistant_turn_index: int
    assistant_message_round: int
    user_message_round: int
    matched_hidden_intents: list[FollowupStyleMatch]


@dataclass(frozen=True)
class IntentJudgeTurn:
    assistant_turn_index: int
    inferred_indexes: list[int]
    matched_indexes: list[int]


def collect_model_task_turn_sessions(
    *,
    model_id: str,
    logs_dir: Path,
    user_id: str | None = None,
) -> dict[tuple[str, str], TaskTurnSession]:
    return _collect_model_task_turn_sessions(model_id=model_id, logs_dir=logs_dir, user_id=user_id)


def collect_model_task_turns(
    *,
    model_id: str,
    logs_dir: Path,
    user_id: str | None = None,
) -> dict[tuple[str, str], list[Path]]:
    sessions = _collect_model_task_turn_sessions(model_id=model_id, logs_dir=logs_dir, user_id=user_id)
    return {(session.user_id, session.task_id): session.turn_paths for session in sessions.values()}


def _collect_model_task_turn_sessions(
    *,
    model_id: str,
    logs_dir: Path,
    user_id: str | None = None,
) -> dict[tuple[str, str], TaskTurnSession]:
    model_dir = logs_dir / safe_model_id(model_id)
    if not model_dir.is_dir():
        raise FileNotFoundError(f"model_id not found under logs dir: {model_dir}")

    search_root = model_dir / user_id if user_id else model_dir
    if not search_root.is_dir():
        return {}

    grouped: dict[tuple[str, str, str], list[Path]] = {}
    for path in search_root.rglob("turn_*.json"):
        rel = path.relative_to(model_dir)
        if len(rel.parts) != 4:
            raise ValueError(
                "invalid trace log layout: expected "
                "trace_logs/{model_id}/{user_id}/{task_id}/{task_start_timestamp}/turn_*.json "
                f"but got {rel}"
            )
        current_user_id, task_id, session_timestamp, _ = rel.parts
        if not TRACE_SESSION_DIR_PATTERN.match(session_timestamp):
            raise ValueError(
                "invalid trace session directory: expected YYYYMMDD_HHMMSS under "
                "trace_logs/{model_id}/{user_id}/{task_id}/ "
                f"but got {rel}"
            )
        grouped.setdefault((current_user_id, task_id, session_timestamp), []).append(path)

    selected: dict[tuple[str, str], TaskTurnSession] = {}
    for (current_user_id, task_id, session_timestamp), turn_paths in grouped.items():
        turn_paths.sort(key=TraceHistoryBuilder._normalize_turn_sort_key)
        task_key = (current_user_id, task_id)
        session_dir = model_dir / current_user_id / task_id / session_timestamp
        current = TaskTurnSession(
            user_id=current_user_id,
            task_id=task_id,
            session_timestamp=session_timestamp,
            session_dir=session_dir,
            turn_paths=turn_paths,
        )
        previous = selected.get(task_key)
        if previous is None or current.session_timestamp > previous.session_timestamp:
            selected[task_key] = current
    return selected


def load_task_followup_turn_styles(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> list[FollowupTurnStyle]:
    messages_path = _select_latest_messages_history_path(
        output_dir=output_dir,
        model_id=model_id,
        user_id=user_id,
        task_id=task_id,
    )

    assistant_turn_index = 0
    previous_entry: dict[str, Any] | None = None
    parsed: list[FollowupTurnStyle] = []
    with messages_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid json in {messages_path}:{line_number}: {exc}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"message entry must be an object in {messages_path}:{line_number}")

            role = str(entry.get("role") or "")
            if role == "assistant":
                assistant_turn_index += 1
            metadata = entry.get("metadata")
            if role == "user" and isinstance(metadata, dict) and "targeted_followup" in metadata:
                parsed.append(
                    _parse_followup_turn_style_entry(
                        messages_path=messages_path,
                        line_number=line_number,
                        entry=entry,
                        previous_entry=previous_entry,
                        assistant_turn_index=assistant_turn_index,
                    )
                )
            previous_entry = entry
    return parsed


def load_task_intent_judge_turns(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> list[IntentJudgeTurn]:
    history_log_path = _select_latest_history_log_path(
        output_dir=output_dir,
        model_id=model_id,
        user_id=user_id,
        task_id=task_id,
    )

    parsed: list[IntentJudgeTurn] = []
    current_turn: dict[str, Any] | None = None
    with history_log_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid json in {history_log_path}:{line_number}: {exc}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"log entry must be an object in {history_log_path}:{line_number}")

            message = str(entry.get("message") or "")
            data = entry.get("data")
            if not isinstance(data, dict):
                data = {}

            if message.startswith(INTENT_SATISFACTION_COMPLETED_PREFIX):
                if current_turn is not None:
                    parsed.append(
                        IntentJudgeTurn(
                            assistant_turn_index=current_turn["assistant_turn_index"],
                            inferred_indexes=list(current_turn["inferred_indexes"]),
                            matched_indexes=list(current_turn["matched_indexes"]),
                        )
                    )
                current_turn = {
                    "assistant_turn_index": len(parsed) + 1,
                    "inferred_indexes": _parse_index_list(
                        data.get("newly_inferred_indexes"),
                        source_path=history_log_path,
                        line_number=line_number,
                        field_name="data.newly_inferred_indexes",
                    ),
                    "matched_indexes": [],
                }
                continue

            if current_turn is None:
                continue
            if message.startswith(TARGETED_FOLLOWUP_COMPLETED_PREFIX):
                current_turn["matched_indexes"] = _parse_index_list(
                    data.get("matched_indexes"),
                    source_path=history_log_path,
                    line_number=line_number,
                    field_name="data.matched_indexes",
                )

    if current_turn is not None:
        parsed.append(
            IntentJudgeTurn(
                assistant_turn_index=current_turn["assistant_turn_index"],
                inferred_indexes=list(current_turn["inferred_indexes"]),
                matched_indexes=list(current_turn["matched_indexes"]),
            )
        )
    return parsed


def _select_latest_messages_history_path(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> Path:
    history_dir = output_dir / safe_model_id(model_id) / user_id / task_id / "history"
    if not history_dir.is_dir():
        raise FileNotFoundError(f"messages history directory not found for followup styles: {history_dir}")

    latest_path: Path | None = None
    latest_timestamp: str | None = None
    for path in history_dir.iterdir():
        if not path.is_file():
            continue
        match = MESSAGES_HISTORY_FILENAME_PATTERN.match(path.name)
        if match is None:
            continue
        timestamp = match.group(1)
        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_path = path

    if latest_path is None:
        raise FileNotFoundError(f"messages history not found for followup styles under: {history_dir}")
    return latest_path


def _select_latest_history_log_path(
    *,
    output_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> Path:
    history_dir = output_dir / safe_model_id(model_id) / user_id / task_id / "history"
    if not history_dir.is_dir():
        raise FileNotFoundError(f"history directory not found for intent judges: {history_dir}")

    latest_path: Path | None = None
    latest_timestamp: str | None = None
    for path in history_dir.iterdir():
        if not path.is_file():
            continue
        match = HISTORY_LOG_FILENAME_PATTERN.match(path.name)
        if match is None:
            continue
        timestamp = match.group(1)
        if latest_timestamp is None or timestamp > latest_timestamp:
            latest_timestamp = timestamp
            latest_path = path
    if latest_path is None:
        raise FileNotFoundError(f"history log not found for intent judges under: {history_dir}")
    return latest_path


def _parse_followup_turn_style_entry(
    *,
    messages_path: Path,
    line_number: int,
    entry: dict[str, Any],
    previous_entry: dict[str, Any] | None,
    assistant_turn_index: int,
) -> FollowupTurnStyle:
    metadata = entry.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"targeted followup metadata must be an object in {messages_path}:{line_number}")
    targeted_followup = metadata.get("targeted_followup")
    if not isinstance(targeted_followup, dict):
        raise ValueError(f"targeted_followup must be an object in {messages_path}:{line_number}")
    if previous_entry is None or str(previous_entry.get("role") or "") != "assistant":
        raise ValueError(
            f"targeted_followup metadata must be attached to a user message immediately after assistant in {messages_path}:{line_number}"
        )

    assistant_message_round = _parse_positive_int(
        previous_entry.get("round"),
        messages_path=messages_path,
        line_number=line_number,
        field_name="previous assistant round",
    )
    declared_assistant_round = targeted_followup.get("assistant_message_round")
    if declared_assistant_round is not None:
        declared_round = _parse_positive_int(
            declared_assistant_round,
            messages_path=messages_path,
            line_number=line_number,
            field_name="metadata.targeted_followup.assistant_message_round",
        )
        if declared_round != assistant_message_round:
            raise ValueError(
                "assistant_message_round mismatch in "
                f"{messages_path}:{line_number} expected={assistant_message_round} got={declared_round}"
            )

    declared_assistant_turn_index = targeted_followup.get("assistant_turn_index")
    if declared_assistant_turn_index is not None:
        declared_turn_index = _parse_positive_int(
            declared_assistant_turn_index,
            messages_path=messages_path,
            line_number=line_number,
            field_name="metadata.targeted_followup.assistant_turn_index",
        )
        if declared_turn_index != assistant_turn_index:
            raise ValueError(
                "assistant_turn_index mismatch in "
                f"{messages_path}:{line_number} expected={assistant_turn_index} got={declared_turn_index}"
            )

    user_message_round = _parse_positive_int(
        entry.get("round"),
        messages_path=messages_path,
        line_number=line_number,
        field_name="round",
    )
    raw_matches = targeted_followup.get("matched_hidden_intents")
    if not isinstance(raw_matches, list) or not raw_matches:
        raise ValueError(f"matched_hidden_intents must be a non-empty list in {messages_path}:{line_number}")

    matches: list[FollowupStyleMatch] = []
    seen_indexes: set[int] = set()
    for item in raw_matches:
        if not isinstance(item, dict):
            raise ValueError(f"matched_hidden_intents items must be objects in {messages_path}:{line_number}")
        hidden_intent_idx = _parse_positive_int(
            item.get("idx"),
            messages_path=messages_path,
            line_number=line_number,
            field_name="matched_hidden_intents.idx",
        )
        if hidden_intent_idx in seen_indexes:
            raise ValueError(
                f"duplicate matched hidden intent idx in {messages_path}:{line_number}: {hidden_intent_idx}"
            )
        content = str(item.get("content") or "").strip()
        if not content:
            raise ValueError(f"matched_hidden_intents.content must be non-empty in {messages_path}:{line_number}")
        style = normalize_targeted_followup_style(str(item.get("style") or ""))
        if style not in TARGETED_FOLLOWUP_STYLES:
            raise ValueError(f"invalid targeted followup style in {messages_path}:{line_number}: {style!r}")
        seen_indexes.add(hidden_intent_idx)
        matches.append(
            FollowupStyleMatch(
                hidden_intent_idx=hidden_intent_idx,
                content=content,
                style=style,
            )
        )

    return FollowupTurnStyle(
        assistant_turn_index=assistant_turn_index,
        assistant_message_round=assistant_message_round,
        user_message_round=user_message_round,
        matched_hidden_intents=matches,
    )


def _parse_positive_int(
    value: Any,
    *,
    messages_path: Path,
    line_number: int,
    field_name: str,
) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer in {messages_path}:{line_number}") from exc
    if parsed < 1:
        raise ValueError(f"{field_name} must be a positive integer in {messages_path}:{line_number}")
    return parsed


def _parse_index_list(
    value: Any,
    *,
    source_path: Path,
    line_number: int,
    field_name: str,
) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list in {source_path}:{line_number}")
    parsed: list[int] = []
    seen: set[int] = set()
    for item in value:
        try:
            idx = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} items must be positive integers in {source_path}:{line_number}") from exc
        if idx < 1:
            raise ValueError(f"{field_name} items must be positive integers in {source_path}:{line_number}")
        if idx in seen:
            continue
        seen.add(idx)
        parsed.append(idx)
    return parsed


def extract_dotted_path(payload: Any, path: str) -> tuple[bool, Any]:
    current = payload
    for token in (part.strip() for part in str(path).split(".")):
        if token == "":
            return False, None
        if isinstance(current, dict):
            if token not in current:
                return False, None
            current = current[token]
            continue
        if isinstance(current, list):
            if not token.isdigit():
                return False, None
            index = int(token)
            if index < 0 or index >= len(current):
                return False, None
            current = current[index]
            continue
        return False, None
    return True, current


def collect_last_tool_payloads(turn_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_tool: dict[str, dict[str, Any]] = {}
    for item in collect_tool_history(turn_data):
        tool_name = str(item.get("tool_name") or "").strip()
        if not tool_name:
            continue
        by_tool[tool_name] = {
            "call": item.get("call"),
            "result": item.get("result"),
        }
    return by_tool


def collect_tool_history(
    turn_data: dict[str, Any],
    *,
    allowed_tool_names: set[str] | None = None,
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    latest_by_tool_name: dict[str, dict[str, Any]] = {}

    def _is_allowed(tool_name: str) -> bool:
        return allowed_tool_names is None or tool_name in allowed_tool_names

    def _remember(item: dict[str, Any]) -> None:
        tool_name = str(item.get("tool_name") or "").strip()
        if not tool_name or not _is_allowed(tool_name):
            return
        latest_by_tool_name[tool_name] = item

    tool_steps = turn_data.get("tool_steps")
    if isinstance(tool_steps, list):
        for step in tool_steps:
            if not isinstance(step, dict):
                continue
            tool_name = str(step.get("name") or "").strip()
            if not tool_name or not _is_allowed(tool_name):
                continue
            _remember(
                {
                    "tool_name": tool_name,
                    "call": step.get("arguments"),
                    "result": TraceHistoryBuilder._parse_json_if_possible(step.get("result")),
                }
            )
        if latest_by_tool_name:
            return list(latest_by_tool_name.values())

    messages = turn_data.get("messages")
    if not isinstance(messages, list):
        return history
    pending_calls: dict[str, tuple[str, Any]] = {}
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "")
        if role == "assistant":
            raw_tool_calls = message.get("tool_calls")
            if not isinstance(raw_tool_calls, list):
                continue
            for call in raw_tool_calls:
                if not isinstance(call, dict):
                    continue
                function = call.get("function")
                if not isinstance(function, dict):
                    continue
                call_id = str(call.get("id") or "").strip()
                tool_name = str(function.get("name") or "").strip()
                if not call_id or not tool_name or not _is_allowed(tool_name):
                    continue
                pending_calls[call_id] = (
                    tool_name,
                    TraceHistoryBuilder._parse_json_if_possible(function.get("arguments")),
                )
            continue
        if role != "tool":
            continue
        call_id = str(message.get("tool_call_id") or "").strip()
        tool_name = str(message.get("name") or "").strip()
        parsed_result = TraceHistoryBuilder._parse_json_if_possible(message.get("content"))
        if call_id and call_id in pending_calls:
            mapped_name, arguments = pending_calls[call_id]
            _remember({"tool_name": mapped_name, "call": arguments, "result": parsed_result})
            continue
        if tool_name and _is_allowed(tool_name):
            _remember({"tool_name": tool_name, "call": None, "result": parsed_result})
    return list(latest_by_tool_name.values())


@dataclass(frozen=True)
class ToolRenderConfig:
    enabled: bool
    include_tool_call_keys: tuple[str, ...] | str
    include_tool_result: bool


@dataclass(frozen=True)
class MessageRenderConfig:
    enabled: bool
    include_message_role_attr: bool
    include_message_index_attr: bool
    include_system: bool
    include_user: bool
    include_assistant_thinking_content: bool
    include_assistant_thinking_reasoning: bool
    include_assistant_content: bool
    include_assistant_reasoning: bool
    include_assistant_tool_calls: bool
    require_matching_tool_call: bool
    include_tool_call_id: bool
    tool_configs: dict[str, ToolRenderConfig]


@dataclass(frozen=True)
class FormatConfig:
    root_tag: str
    turn_tag: str
    message_tag: str
    file_tag: str
    tool_call_tag_prefix: str
    tool_result_tag_prefix: str


@dataclass(frozen=True)
class FileRenderConfig:
    enabled: bool


@dataclass(frozen=True)
class TextPolicyConfig:
    default: dict[str, Any]
    field_overrides: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class RenderConfig:
    format: FormatConfig
    messages: MessageRenderConfig
    files: FileRenderConfig
    include_session_key: bool
    text_policy: TextPolicyConfig


@dataclass(frozen=True)
class MessageRenderOutput:
    lines: list[str]
    trailing_assistant_nodes: list[str]


class TraceHistoryBuilder:
    def __init__(
        self,
        *,
        model_id: str,
        user_id: str | None,
        logs_dir: Path,
        config_path: Path,
        output_dir: Path,
        workspace_dir: Path | None = None,
        data_root: Path = Path("data"),
    ) -> None:
        self.model_id = model_id
        self.user_id = user_id
        self.safe_model_id = safe_model_id(model_id)
        self.logs_dir = logs_dir
        self.config_path = config_path
        self.output_dir = output_dir
        self.workspace_dir = workspace_dir
        self.data_root = data_root
        self.config = self._load_config(config_path)
        self.files_read_truncate_chars = parse_files_read_truncate_chars(
            self.config,
            source=f"trace history config {config_path}",
        )
        self.render = self._parse_render_config(self.config)
        self.should_load_files = self.render.files.enabled and workspace_dir is not None
        self.repository = UserDataRepository(data_root=str(data_root))
        self.task_cache: dict[str, dict[str, TaskSpec]] = {}

    def build(self, *, eval_timestamp: str | None = None) -> list[tuple[str, str, Path]]:
        snapshot_timestamp = eval_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        stage_logger.info("Building trace histories model_id={} user_id={}", self.model_id, self.user_id or "*")
        written: list[tuple[str, str, Path]] = []
        for (user_id, task_id), session in sorted(self._collect_task_turn_sessions().items()):
            aux_logger.info(
                "Selected trace session model_id={} user_id={} task_id={} session_dir={}",
                self.model_id,
                user_id,
                task_id,
                session.session_dir,
                data={
                    "model_id": self.model_id,
                    "user_id": user_id,
                    "task_id": task_id,
                    "session_dir": str(session.session_dir),
                    "session_timestamp": session.session_timestamp,
                },
            )
            turn_paths = session.turn_paths
            task = self._load_task(user_id, task_id)
            attached_files = self._load_attached_files(user_id, task_id)
            task_eval_dir = self.output_dir / self.safe_model_id / user_id / task_id / "eval"
            task_eval_dir.mkdir(parents=True, exist_ok=True)
            for trace_file in task_eval_dir.glob("trace*.txt"):
                if trace_file.is_file():
                    trace_file.unlink()
            trace_logs_dir = task_eval_dir / "trace_logs"
            turn_output_dir = trace_logs_dir / snapshot_timestamp
            if turn_output_dir.exists():
                shutil.rmtree(turn_output_dir)
            turn_output_dir.mkdir(parents=True, exist_ok=True)
            for turn_path in turn_paths:
                shutil.copy2(turn_path, turn_output_dir / turn_path.name)

            for turn_index, turn_path in enumerate(turn_paths, start=1):
                content = self._render_task_history(
                    user_id,
                    task_id,
                    [(turn_index, turn_path)],
                    attached_files,
                    task=task,
                )
                out_path = task_eval_dir / f"trace_{turn_index}.txt"
                out_path.write_text(content, encoding="utf-8")

            written.append((user_id, task_id, task_eval_dir))
            aux_logger.info(
                "History file written model_id={} user_id={} task_id={} turns={}",
                self.model_id,
                user_id,
                task_id,
                len(turn_paths),
            )

        stage_logger.info("Trace history build completed model_id={} tasks={}", self.model_id, len(written))
        return written

    def _collect_task_turns(self) -> dict[tuple[str, str], list[Path]]:
        return collect_model_task_turns(model_id=self.model_id, logs_dir=self.logs_dir, user_id=self.user_id)

    def _collect_task_turn_sessions(self) -> dict[tuple[str, str], TaskTurnSession]:
        return _collect_model_task_turn_sessions(model_id=self.model_id, logs_dir=self.logs_dir, user_id=self.user_id)

    def _load_attached_files(self, user_id: str, task_id: str) -> list[TaskFileReadEntry]:
        if not self.should_load_files or self.workspace_dir is None:
            return []
        task = self._load_task(user_id, task_id)
        if task is None:
            return []
        return load_task_files_read_entries(
            task=task,
            workspace_dir=self.workspace_dir,
            truncate_chars=self.files_read_truncate_chars,
        )

    def _load_task(self, user_id: str, task_id: str) -> TaskSpec | None:
        if user_id not in self.task_cache:
            try:
                _, _, tasks = self.repository.load_user(user_id)
            except FileNotFoundError:
                tasks = {}
            self.task_cache[user_id] = tasks
        return self.task_cache.get(user_id, {}).get(task_id)

    def _render_task_history(
        self,
        user_id: str,
        task_id: str,
        turn_entries: list[tuple[int, Path]],
        attached_files: list[TaskFileReadEntry],
        *,
        task: TaskSpec | None,
    ) -> str:
        header = (
            f'<{self.render.format.root_tag} model_id="{escape(self.model_id)}" '
            f'user_id="{escape(user_id)}" task_id="{escape(task_id)}">'
        )
        blocks = [header]
        for index, turn_path in turn_entries:
            turn_data = self._load_turn_data(turn_path)
            turn_lines = [f'<{self.render.format.turn_tag} index="{index}" file="{escape(turn_path.name)}">']
            if self.render.include_session_key:
                session_tag = self._render_value_tag(
                    "session_key",
                    turn_data.get("session_key"),
                    self._text_policy("session_key"),
                )
                if session_tag:
                    turn_lines.append(session_tag)
            message_output = self._render_messages(turn_data)
            turn_lines.extend(message_output.lines)
            turn_lines.extend(self._render_tool_trace_extracts(task=task, turn_data=turn_data))
            turn_lines.extend(message_output.trailing_assistant_nodes)
            turn_lines.append(f"</{self.render.format.turn_tag}>")
            blocks.append("\n".join(turn_lines))

        blocks.extend(self._render_files(attached_files))
        blocks.append(f"</{self.render.format.root_tag}>")
        return "\n".join(blocks)

    def _render_messages(self, turn_data: dict[str, Any]) -> MessageRenderOutput:
        if not self.render.messages.enabled:
            return MessageRenderOutput(lines=[], trailing_assistant_nodes=[])
        messages = turn_data.get("messages")
        if not isinstance(messages, list):
            raise ValueError("turn_data.messages must be a list")

        lines: list[str] = []
        pending_tool_call_ids: set[str] = set()
        pending_tool_results: dict[str, bool] = {}
        deferred_assistant_nodes: list[str] = []
        last_assistant_idx = self._find_last_assistant_index(messages)

        for idx, message in enumerate(messages, start=1):
            if not isinstance(message, dict):
                continue

            role = str(message.get("role") or "")
            if role != "tool" and deferred_assistant_nodes:
                lines.extend(deferred_assistant_nodes)
                deferred_assistant_nodes = []
            if role == "system" and self.render.messages.include_system:
                node = self._render_message(role="system", content=message.get("content"), index=idx)
                if node:
                    lines.append(node)
                continue
            if role == "user" and self.render.messages.include_user:
                node = self._render_message(role="user", content=message.get("content"), index=idx)
                if node:
                    lines.append(node)
                continue
            if role == "assistant":
                assistant_nodes: list[str] = []
                is_final_assistant = idx == last_assistant_idx
                if is_final_assistant:
                    if self.render.messages.include_assistant_content:
                        node = self._render_message(role="assistant", content=message.get("content"), index=idx)
                        if node:
                            assistant_nodes.append(node)
                    if self.render.messages.include_assistant_reasoning:
                        node = self._render_message(
                            role="assistant_reasoning",
                            content=message.get("reasoning_content"),
                            index=idx,
                            field_name="assistant_reasoning",
                        )
                        if node:
                            assistant_nodes.append(node)
                else:
                    if self.render.messages.include_assistant_thinking_content:
                        node = self._render_message(role="assistant", content=message.get("content"), index=idx)
                        if node:
                            assistant_nodes.append(node)
                    if self.render.messages.include_assistant_thinking_reasoning:
                        node = self._render_message(
                            role="assistant_reasoning",
                            content=message.get("reasoning_content"),
                            index=idx,
                            field_name="assistant_reasoning",
                        )
                        if node:
                            assistant_nodes.append(node)

                if not self.render.messages.include_assistant_tool_calls:
                    lines.extend(assistant_nodes)
                    continue
                tool_calls = message.get("tool_calls", [])
                if not isinstance(tool_calls, list):
                    raise ValueError("assistant.tool_calls must be a list")
                rendered_tool_call_count = 0
                for call in tool_calls:
                    if not isinstance(call, dict):
                        continue
                    node, call_id, include_result = self._render_tool_call(call)
                    if call_id:
                        pending_tool_call_ids.add(call_id)
                        pending_tool_results[call_id] = include_result
                    if node:
                        rendered_tool_call_count += 1
                        lines.append(node)
                if rendered_tool_call_count > 0:
                    deferred_assistant_nodes.extend(assistant_nodes)
                else:
                    lines.extend(assistant_nodes)
                continue
            if role != "tool":
                continue

            call_id = str(message.get("tool_call_id") or "")
            if self.render.messages.require_matching_tool_call and (not call_id or call_id not in pending_tool_call_ids):
                continue
            if not pending_tool_results.get(call_id, False):
                continue
            node = self._render_tool_result(message, str(message.get("name") or "unknown_tool"))
            if node:
                lines.append(node)

        return MessageRenderOutput(lines=lines, trailing_assistant_nodes=deferred_assistant_nodes)

    def _render_message(
        self,
        *,
        role: str,
        content: Any,
        index: int,
        field_name: str | None = None,
    ) -> str:
        if self._is_empty_content(content):
            return ""

        attrs: list[str] = []
        if self.render.messages.include_message_role_attr:
            attrs.append(f'role="{escape(role)}"')
        if self.render.messages.include_message_index_attr:
            attrs.append(f'index="{index}"')
        content_tag = self._render_value_tag(
            "content",
            content,
            self._text_policy(field_name or f"{role}_content"),
        )
        if not content_tag:
            return ""
        attr_text = f" {' '.join(attrs)}" if attrs else ""
        return f"<{self.render.format.message_tag}{attr_text}>{content_tag}</{self.render.format.message_tag}>"

    def _render_tool_call(self, call: dict[str, Any]) -> tuple[str, str, bool]:
        function = call.get("function")
        if not isinstance(function, dict):
            function = {}

        tool_name = str(function.get("name") or "unknown_tool")
        tool_cfg = self.render.messages.tool_configs.get(
            tool_name,
            ToolRenderConfig(enabled=False, include_tool_call_keys=(), include_tool_result=False),
        )
        if not tool_cfg.enabled:
            return "", "", False

        call_id = str(call.get("id") or "")
        attrs = [f'id="{escape(call_id)}"'] if self.render.messages.include_tool_call_id and call_id else []
        parsed_args = self._parse_json_if_possible(function.get("arguments"))
        fields: list[str] = []
        if isinstance(parsed_args, dict):
            items = parsed_args.items() if tool_cfg.include_tool_call_keys == "*" else (
                (key, parsed_args[key]) for key in tool_cfg.include_tool_call_keys if key in parsed_args
            )
            for key, value in items:
                field = self._render_value_tag(
                    self._safe_tag_name(str(key)),
                    value,
                    self._text_policy("tool_call_arguments"),
                )
                if field:
                    fields.append(field)

        node_tag = f"{self.render.format.tool_call_tag_prefix}:{self._safe_tag_name(tool_name)}"
        attr_text = f" {' '.join(attrs)}" if attrs else ""
        return f"<{node_tag}{attr_text}>{''.join(fields)}</{node_tag}>", call_id, tool_cfg.include_tool_result

    def _render_tool_result(self, message: dict[str, Any], tool_name: str) -> str:
        attrs = []
        if self.render.messages.include_tool_call_id:
            attrs.append(f'tool_call_id="{escape(str(message.get("tool_call_id") or ""))}"')
        content_tag = self._render_value_tag(
            "content",
            message.get("content"),
            self._text_policy("tool_result_content"),
        )
        if not content_tag:
            return ""
        node_tag = f"{self.render.format.tool_result_tag_prefix}:{self._safe_tag_name(tool_name)}"
        attr_text = f" {' '.join(attrs)}" if attrs else ""
        return f"<{node_tag}{attr_text}>{content_tag}</{node_tag}>"

    def _render_tool_trace_extracts(self, *, task: TaskSpec | None, turn_data: dict[str, Any]) -> list[str]:
        if task is None or not task.tool_trace_specs:
            return []
        last_calls_by_tool = collect_last_tool_payloads(turn_data)
        lines: list[str] = ["<tool_trace_extracts>"]
        for spec in task.tool_trace_specs:
            payloads = last_calls_by_tool.get(spec.tool_name)
            for source, paths in (("call", spec.call_paths), ("result", spec.result_paths)):
                source_payload = payloads.get(source) if isinstance(payloads, dict) else None
                for path in paths:
                    found, value = extract_dotted_path(source_payload, path)
                    attrs = (
                        f'tool="{escape(spec.tool_name)}" source="{escape(source)}" '
                        f'path="{escape(path)}" status="{"ok" if found else "missing"}"'
                    )
                    lines.append(f"<tool_trace_extract {attrs}>{self._to_untruncated_text(value)}</tool_trace_extract>")
        lines.append("</tool_trace_extracts>")
        return lines

    def _render_files(self, attached_files: list[TaskFileReadEntry]) -> list[str]:
        if not self.render.files.enabled:
            return []
        lines: list[str] = []
        file_policy = self._text_policy("file_content")
        mask_newlines = bool(file_policy.get("mask_newlines", False))
        for attached_file in attached_files:
            content = attached_file.content.replace("\n", "\\n") if mask_newlines else attached_file.content
            if not content and attached_file.exists:
                continue
            attrs = [f'name="{escape(attached_file.name)}"']
            if not attached_file.exists:
                attrs.append('status="missing"')
            lines.append(f"<{self.render.format.file_tag} {' '.join(attrs)}>{content}</{self.render.format.file_tag}>")
        return lines

    def _text_policy(self, field_name: str | None) -> dict[str, Any]:
        policy = dict(self.render.text_policy.default)
        if field_name is not None:
            policy.update(self.render.text_policy.field_overrides.get(field_name, {}))
        return policy

    def _load_config(self, config_path: Path) -> dict[str, Any]:
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        if not isinstance(config, dict):
            raise ValueError(f"Invalid config format: {config_path}")
        return config

    def _parse_render_config(self, config: dict[str, Any]) -> RenderConfig:
        format_cfg = config.get("format", {})
        fields_cfg = config.get("fields", {})
        turn_cfg = fields_cfg.get("turn", {})
        messages_cfg = fields_cfg.get("messages", {})
        files_cfg = fields_cfg.get("files", {})
        tool_calls_cfg = messages_cfg.get("tool_calls", {})
        text_policy_cfg = config.get("text_policy", {})
        if not isinstance(format_cfg, dict):
            raise ValueError("config.format must be a mapping")
        if not isinstance(fields_cfg, dict):
            raise ValueError("config.fields must be a mapping")
        if not isinstance(turn_cfg, dict):
            raise ValueError("config.fields.turn must be a mapping")
        if not isinstance(messages_cfg, dict):
            raise ValueError("config.fields.messages must be a mapping")
        if not isinstance(files_cfg, dict):
            raise ValueError("config.fields.files must be a mapping")
        if not isinstance(tool_calls_cfg, dict):
            raise ValueError("config.fields.messages.tool_calls must be a mapping")
        if not isinstance(text_policy_cfg, dict):
            raise ValueError("config.text_policy must be a mapping")

        include_assistant_content = bool(messages_cfg.get("include_assistant_content", True))
        include_assistant_reasoning = bool(messages_cfg.get("include_assistant_reasoning", False))
        default_policy = text_policy_cfg.get("default", text_policy_cfg)
        field_overrides = text_policy_cfg.get("field_overrides", {})
        if not isinstance(default_policy, dict):
            raise ValueError("config.text_policy.default must be a mapping")
        if not isinstance(field_overrides, dict):
            raise ValueError("config.text_policy.field_overrides must be a mapping")
        for field_name, value in field_overrides.items():
            if not isinstance(value, dict):
                raise ValueError(f"config.text_policy.field_overrides.{field_name} must be a mapping")

        tools_cfg = tool_calls_cfg.get("tools", {})
        if not isinstance(tools_cfg, dict):
            raise ValueError("config.fields.messages.tool_calls.tools must be a mapping")
        tool_configs: dict[str, ToolRenderConfig] = {}
        for tool_name, tool_cfg in tools_cfg.items():
            if not isinstance(tool_cfg, dict):
                raise ValueError(f"tool config for {tool_name} must be a mapping")
            keys = tool_cfg.get("include_tool_call_keys", [])
            if keys == "*" or keys == ["*"]:
                include_keys: tuple[str, ...] | str = "*"
            elif isinstance(keys, list):
                include_keys = tuple(str(item) for item in keys)
            else:
                raise ValueError(f"tool config include_tool_call_keys for {tool_name} must be list or ['*']")
            tool_configs[str(tool_name)] = ToolRenderConfig(
                enabled=bool(tool_cfg.get("enabled", False)),
                include_tool_call_keys=include_keys,
                include_tool_result=bool(tool_cfg.get("include_tool_result", False)),
            )

        return RenderConfig(
            format=FormatConfig(
                root_tag=str(format_cfg.get("root_tag", "trace")),
                turn_tag=str(format_cfg.get("turn_tag", "turn")),
                message_tag=str(format_cfg.get("message_tag", "message")),
                file_tag=str(format_cfg.get("file_tag", "file")),
                tool_call_tag_prefix=str(format_cfg.get("tool_call_tag_prefix", "tool_call")),
                tool_result_tag_prefix=str(format_cfg.get("tool_result_tag_prefix", "tool_result")),
            ),
            messages=MessageRenderConfig(
                enabled=bool(messages_cfg.get("enabled", True)),
                include_message_role_attr=bool(messages_cfg.get("include_message_role_attr", True)),
                include_message_index_attr=bool(messages_cfg.get("include_message_index_attr", True)),
                include_system=bool(messages_cfg.get("include_system", True)),
                include_user=bool(messages_cfg.get("include_user", True)),
                include_assistant_thinking_content=bool(
                    messages_cfg.get("include_assistant_thinking_content", include_assistant_content)
                ),
                include_assistant_thinking_reasoning=bool(
                    messages_cfg.get("include_assistant_thinking_reasoning", include_assistant_reasoning)
                ),
                include_assistant_content=include_assistant_content,
                include_assistant_reasoning=include_assistant_reasoning,
                include_assistant_tool_calls=bool(messages_cfg.get("include_assistant_tool_calls", True)),
                require_matching_tool_call=bool(messages_cfg.get("require_matching_tool_call", True)),
                include_tool_call_id=bool(tool_calls_cfg.get("include_tool_call_id", True)),
                tool_configs=tool_configs,
            ),
            files=FileRenderConfig(enabled=bool(files_cfg.get("enabled", False))),
            include_session_key=bool(turn_cfg.get("include_session_key", True)),
            text_policy=TextPolicyConfig(
                default=dict(default_policy),
                field_overrides={str(field_name): dict(value) for field_name, value in field_overrides.items()},
            ),
        )

    def _load_turn_data(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Turn file must contain a JSON object: {path}")
        return data

    def _generate_trace_viewer_html(self, user_root_dir: Path, *, user_id: str) -> Path:
        return generate_trace_viewer_html(
            model_id=self.model_id,
            user_id=user_id,
            user_root_dir=user_root_dir,
        )

    @staticmethod
    def _normalize_turn_sort_key(path: Path) -> tuple[int, str]:
        match = TURN_FILENAME_INT_PATTERN.match(path.name)
        if match:
            return int(match.group(1)), path.name
        match = TURN_FILENAME_TS_PATTERN.match(path.name)
        if match:
            return int(f"{match.group(1)}{match.group(2)}"), path.name
        return 10**18, path.name

    @staticmethod
    def _safe_tag_name(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)

    @staticmethod
    def _apply_text_policy(text: str, policy: dict[str, Any]) -> str:
        truncate_chars = int(policy.get("truncate_chars", 0) or 0)
        if truncate_chars > 0 and len(text) > truncate_chars:
            text = text[:truncate_chars] + "...[truncated]"
        if policy.get("mask_newlines", False):
            text = text.replace("\n", "\\n")
        return text

    @classmethod
    def _to_text(cls, value: Any, policy: dict[str, Any]) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return cls._apply_text_policy(value, policy)
        return cls._apply_text_policy(json.dumps(value, ensure_ascii=False, sort_keys=True), policy)

    @staticmethod
    def _to_untruncated_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    @classmethod
    def _render_value_tag(cls, tag_name: str, value: Any, policy: dict[str, Any]) -> str:
        text = cls._to_text(value, policy)
        if not text:
            return ""
        return f"<{tag_name}>{text}</{tag_name}>"

    @staticmethod
    def _parse_json_if_possible(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    @staticmethod
    def _is_empty_content(value: Any) -> bool:
        return value is None or (isinstance(value, str) and value.strip() == "")

    @staticmethod
    def _find_last_assistant_index(messages: list[Any]) -> int | None:
        for idx in range(len(messages) - 1, -1, -1):
            if isinstance(messages[idx], dict) and str(messages[idx].get("role") or "") == "assistant":
                return idx + 1
        return None


def build_model_trace_histories(
    *,
    model_id: str,
    logs_dir: Path,
    config_path: Path,
    output_dir: Path,
    user_id: str | None = None,
    workspace_dir: Path | None = None,
    data_root: Path = Path("data"),
    eval_timestamp: str | None = None,
) -> list[tuple[str, str, Path]]:
    return TraceHistoryBuilder(
        model_id=model_id,
        user_id=user_id,
        logs_dir=logs_dir,
        config_path=config_path,
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        data_root=data_root,
    ).build(eval_timestamp=eval_timestamp)


def generate_trace_viewer_html(*, model_id: str, user_id: str, user_root_dir: Path) -> Path:
    output_path = user_root_dir / f"{safe_model_id(model_id)}-{user_id}.html"
    subprocess.run(
        [
            sys.executable,
            str(TRACE_VIEWER_PATH),
            "--logs-dir",
            str(user_root_dir),
            "--output-file",
            str(output_path),
            "--default-model-id",
            model_id,
            "--default-user-id",
            user_id,
            "--no-open",
            "--quiet",
        ],
        check=True,
        cwd=str(TRACE_VIEWER_PATH.parent.parent),
    )
    return output_path
