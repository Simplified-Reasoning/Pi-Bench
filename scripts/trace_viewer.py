"""
Trace log 可视化：支持以下布局，并按 model_id / user_id 聚合生成 HTML。

- trace_logs/{model_id}/{user_id}/{task_id}/{task_session_ts}/turn_*.json
- {user_root}/{task_id}/eval/trace_logs/{task_session_ts}/turn_*.json
- trace_logs/{task_id}/{task_session_ts}/turn_*.json
- trace_logs/{task_session_ts}/turn_*.json
"""
from __future__ import annotations

import json
import math
import os
import re
import webbrowser
from pathlib import Path
from typing import Any
import yaml

LOGS_DIR = Path(
    os.environ.get("NANOBOT_TRACE_LOGS", os.path.expanduser("~/.nanobot/trace_logs"))
)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRACE_SESSION_DIR_PATTERN = re.compile(r"^\d{8}_\d{6}$")
HISTORY_LOG_FILENAME_PATTERN = re.compile(r"^(\d{8}_\d{6})-log\.jsonl$")
RESULT_FILENAME_PATTERN = re.compile(r"^(\d{8}_\d{6})_result\.json$")
HIDDEN_INTENTS_INITIALIZED_PREFIX = "Hidden intents initialized"
INTENT_SATISFACTION_COMPLETED_PREFIX = "Intent satisfaction completed"
INTENT_SATISFACTION_SKIPPED_PREFIX = "Intent satisfaction skipped"
TARGETED_FOLLOWUP_COMPLETED_PREFIX = "Targeted followup completed"
TARGETED_FOLLOWUP_SKIPPED_PREFIX = "Targeted followup skipped"
REPLY_BUILT_PREFIX = "Reply built updated_indexes="


def _safe_model_id(model_id: str) -> str:
    return str(model_id).strip().replace("/", "_")


def _read_turn_meta(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    input_text = data.get("input") or ""
    output_text = data.get("output") or ""
    return {
        "session_key": data.get("session_key") or "unknown",
        "input_preview": input_text,
        "output_len": len(output_text),
        "iterations": data.get("iterations") or 0,
        "llm_steps": len(data.get("llm_steps") or []),
        "tool_steps": len(data.get("tool_steps") or []),
    }


def scan_logs(
    logs_dir: Path,
    *,
    default_model_id: str | None = None,
    default_user_id: str | None = None,
) -> dict[str, dict[str, dict[str, dict[str, list[dict[str, Any]]]]]]:
    """
    扫描日志目录。

    返回结构:
    model_id -> user_id -> task_id -> task_session_ts -> [turn items]
    """
    if not logs_dir.is_dir():
        return {}

    models: dict[str, dict[str, dict[str, dict[str, list[dict[str, Any]]]]]] = {}
    for path in logs_dir.rglob("turn_*.json"):
        rel = path.relative_to(logs_dir)
        model_id, user_id, task_id, session_timestamp = _resolve_trace_location(
            rel.parts,
            rel_path=rel,
            default_model_id=default_model_id,
            default_user_id=default_user_id,
        )
        meta = _read_turn_meta(path)
        item = {
            "path": str(path),
            "rel_path": str(rel),
            "name": path.name,
            "mtime": path.stat().st_mtime,
            "meta": meta or {},
        }
        session_map = (
            models.setdefault(model_id, {})
            .setdefault(user_id, {})
            .setdefault(task_id, {})
        )
        session_map.setdefault(session_timestamp, []).append(item)

    for user_map in models.values():
        for task_map in user_map.values():
            for session_map in task_map.values():
                for turn_items in session_map.values():
                    turn_items.sort(key=lambda item: (item["mtime"], item["name"]))
    return models


def _resolve_trace_location(
    parts: tuple[str, ...],
    *,
    rel_path: Path,
    default_model_id: str | None,
    default_user_id: str | None,
) -> tuple[str, str, str, str]:
    if (
        len(parts) == 5
        and parts[1] == "eval"
        and parts[2] == "trace_logs"
        and TRACE_SESSION_DIR_PATTERN.match(parts[3])
    ):
        task_id, _, _, session_timestamp, _ = parts
        return (
            default_model_id or "trace",
            default_user_id or "eval_user",
            task_id,
            session_timestamp,
        )

    if len(parts) == 5 and TRACE_SESSION_DIR_PATTERN.match(parts[3]):
        model_id, user_id, task_id, session_timestamp, _ = parts
        return model_id, user_id, task_id, session_timestamp

    if len(parts) == 3 and TRACE_SESSION_DIR_PATTERN.match(parts[1]):
        task_id, session_timestamp, _ = parts
        return (
            default_model_id or "trace",
            default_user_id or "eval_user",
            task_id,
            session_timestamp,
        )

    if len(parts) == 3 and parts[0] == "trace_logs" and TRACE_SESSION_DIR_PATTERN.match(parts[1]):
        _, session_timestamp, _ = parts
        return (
            default_model_id or "trace",
            default_user_id or "eval_user",
            "task_session",
            session_timestamp,
        )

    if len(parts) == 2 and TRACE_SESSION_DIR_PATTERN.match(parts[0]):
        session_timestamp, _ = parts
        return (
            default_model_id or "trace",
            default_user_id or "eval_user",
            "task_session",
            session_timestamp,
        )

    raise ValueError(
        "invalid trace log layout: expected one of "
        "{model_id}/{user_id}/{task_id}/{task_session_ts}/turn_*.json, "
        "{task_id}/eval/trace_logs/{task_session_ts}/turn_*.json, "
        "{task_id}/{task_session_ts}/turn_*.json, "
        "trace_logs/{task_session_ts}/turn_*.json, "
        "or {task_session_ts}/turn_*.json "
        f"but got {rel_path}"
    )


def _load_episode_task_order(user_id: str, data_dir: Path = DATA_DIR) -> list[str]:
    path = data_dir / user_id / "episode.yaml"
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(data, dict):
        return []
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return []
    order: list[str] = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("task_id", "")).strip()
        if task_id:
            order.append(task_id)
    return order


def _empty_intent_phase(reason: str = "Not executed") -> dict[str, Any]:
    return {
        "executed": False,
        "reason": reason,
    }


def _empty_intent_process() -> dict[str, Any]:
    return {
        "intent_satisfaction": _empty_intent_phase(),
        "targeted_followup": _empty_intent_phase(),
        "newly_provided": _empty_intent_phase(),
    }


def _normalize_indexes(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    parsed: list[int] = []
    seen: set[int] = set()
    for item in value:
        try:
            idx = int(item)
        except (TypeError, ValueError):
            continue
        if idx < 1 or idx in seen:
            continue
        seen.add(idx)
        parsed.append(idx)
    return parsed


def _update_intent_map_from_items(hidden_intents_by_idx: dict[int, str], items: Any) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("idx"))
        except (TypeError, ValueError):
            continue
        if idx < 1:
            continue
        content = str(item.get("content") or "").strip()
        if content:
            hidden_intents_by_idx[idx] = content


def _intents_from_indexes(indexes: list[int], hidden_intents_by_idx: dict[int, str]) -> list[dict[str, Any]]:
    return [{"idx": idx, "content": hidden_intents_by_idx.get(idx, "")} for idx in indexes]


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _extract_status_indexes(statuses: Any, target_status: str) -> list[int]:
    if not isinstance(statuses, list):
        return []
    parsed: list[int] = []
    seen: set[int] = set()
    for item in statuses:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip() != target_status:
            continue
        try:
            idx = int(item.get("idx"))
        except (TypeError, ValueError):
            continue
        if idx < 1 or idx in seen:
            continue
        seen.add(idx)
        parsed.append(idx)
    return parsed


def _decision_matches_hidden_intent(
    decision: dict[str, Any],
    idx: int,
    hidden_intents_by_idx: dict[int, str],
) -> bool:
    decision_content = str(decision.get("content") or "").strip()
    canonical_content = str(hidden_intents_by_idx.get(idx) or "").strip()
    if not decision_content or not canonical_content:
        return True
    return _normalize_whitespace(decision_content) == _normalize_whitespace(canonical_content)


def _parse_intent_process_turns(history_log_path: Path) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    hidden_intents_by_idx: dict[int, str] = {}

    with history_log_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue

            message = str(entry.get("message") or "")
            data = entry.get("data")
            if not isinstance(data, dict):
                data = {}

            if message.startswith(HIDDEN_INTENTS_INITIALIZED_PREFIX):
                _update_intent_map_from_items(hidden_intents_by_idx, data.get("hidden_intents"))
                continue

            _update_intent_map_from_items(hidden_intents_by_idx, data.get("statuses"))

            if message.startswith(INTENT_SATISFACTION_COMPLETED_PREFIX):
                if current is not None:
                    turns.append(current)
                current = _empty_intent_process()
                status_groups = data.get("status_groups")
                if not isinstance(status_groups, dict):
                    status_groups = {}
                newly_inferred = _normalize_indexes(data.get("newly_inferred_indexes"))
                not_provided = _normalize_indexes(status_groups.get("not_provided"))
                provided = _normalize_indexes(status_groups.get("provided"))
                current["intent_satisfaction"] = {
                    "executed": True,
                    "newly_inferred_indexes": newly_inferred,
                    "not_provided_indexes": not_provided,
                    "provided_indexes": provided,
                    "details": {
                        "newly_inferred": _intents_from_indexes(newly_inferred, hidden_intents_by_idx),
                        "not_provided": _intents_from_indexes(not_provided, hidden_intents_by_idx),
                        "provided": _intents_from_indexes(provided, hidden_intents_by_idx),
                    },
                }
                continue

            if message.startswith(INTENT_SATISFACTION_SKIPPED_PREFIX):
                if current is not None:
                    turns.append(current)
                current = _empty_intent_process()
                current["intent_satisfaction"] = _empty_intent_phase(reason=message)
                continue

            if current is None:
                continue

            if message.startswith(TARGETED_FOLLOWUP_COMPLETED_PREFIX):
                decisions = data.get("decisions")
                if not isinstance(decisions, list):
                    decisions = []
                matched_indexes = _normalize_indexes(data.get("matched_indexes"))
                decision_by_idx: dict[int, dict[str, Any]] = {}
                candidate_indexes = _extract_status_indexes(data.get("statuses"), "not_provided")
                if not candidate_indexes:
                    intent_satisfaction = current.get("intent_satisfaction")
                    if isinstance(intent_satisfaction, dict):
                        candidate_indexes = _normalize_indexes(intent_satisfaction.get("not_provided_indexes"))
                decision_by_candidate_idx: dict[int, dict[str, Any]] = {}
                yes_count = 0
                no_count = 0
                for decision in decisions:
                    if not isinstance(decision, dict):
                        continue
                    try:
                        idx = int(decision.get("idx"))
                    except (TypeError, ValueError):
                        continue
                    if idx < 1:
                        continue
                    decision_by_idx[idx] = decision
                    if 1 <= idx <= len(candidate_indexes):
                        decision_by_candidate_idx[candidate_indexes[idx - 1]] = decision
                    normalized_decision = str(decision.get("decision") or "").upper()
                    if normalized_decision == "YES":
                        yes_count += 1
                    elif normalized_decision == "NO":
                        no_count += 1

                matched_intents: list[dict[str, Any]] = []
                for idx in matched_indexes:
                    decision = decision_by_idx.get(idx)
                    if decision is None:
                        decision = decision_by_candidate_idx.get(idx, {})
                    elif not _decision_matches_hidden_intent(
                        decision,
                        idx,
                        hidden_intents_by_idx,
                    ):
                        legacy_decision = decision_by_candidate_idx.get(idx)
                        if legacy_decision is not None:
                            decision = legacy_decision
                    content = str(hidden_intents_by_idx.get(idx) or decision.get("content") or "").strip()
                    item: dict[str, Any] = {
                        "idx": idx,
                        "content": content,
                    }
                    style = str(decision.get("style") or "").strip()
                    if style:
                        item["style"] = style
                    matched_intents.append(item)

                current["targeted_followup"] = {
                    "executed": True,
                    "matched_indexes": matched_indexes,
                    "summary": {
                        "total_candidates": len(decision_by_idx),
                        "yes_count": yes_count,
                        "no_count": no_count,
                    },
                    "matched_intents": matched_intents,
                }
                continue

            if message.startswith(TARGETED_FOLLOWUP_SKIPPED_PREFIX):
                current["targeted_followup"] = _empty_intent_phase(reason=message)
                continue

            if message.startswith(REPLY_BUILT_PREFIX):
                updated_indexes = _normalize_indexes(data.get("updated_indexes"))
                current["newly_provided"] = {
                    "executed": True,
                    "updated_indexes": updated_indexes,
                    "intents": _intents_from_indexes(updated_indexes, hidden_intents_by_idx),
                }

    if current is not None:
        turns.append(current)
    return turns


def _select_latest_history_log_path(
    *,
    logs_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> Path | None:
    candidate_dirs = [
        logs_dir / task_id / "history",
        logs_dir / _safe_model_id(model_id) / user_id / task_id / "history",
    ]
    latest: tuple[str, Path] | None = None
    seen_dirs: set[Path] = set()
    for history_dir in candidate_dirs:
        resolved = history_dir.resolve()
        if resolved in seen_dirs or not history_dir.is_dir():
            continue
        seen_dirs.add(resolved)
        for file_path in history_dir.iterdir():
            if not file_path.is_file():
                continue
            match = HISTORY_LOG_FILENAME_PATTERN.match(file_path.name)
            if match is None:
                continue
            timestamp = match.group(1)
            if latest is None or timestamp > latest[0]:
                latest = (timestamp, file_path)
    return latest[1] if latest is not None else None


def _load_task_intent_turns(
    *,
    logs_dir: Path | None,
    model_id: str,
    user_id: str,
    task_id: str,
) -> list[dict[str, Any]]:
    if logs_dir is None:
        return []
    history_log_path = _select_latest_history_log_path(
        logs_dir=logs_dir,
        model_id=model_id,
        user_id=user_id,
        task_id=task_id,
    )
    if history_log_path is None:
        return []
    return _parse_intent_process_turns(history_log_path)


def _select_latest_eval_result_path(
    *,
    logs_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
) -> Path | None:
    candidate_roots = [
        logs_dir / task_id / "eval",
        logs_dir / _safe_model_id(model_id) / user_id / task_id / "eval",
    ]
    latest: tuple[str, Path] | None = None
    seen_dirs: set[Path] = set()
    for eval_dir in candidate_roots:
        resolved = eval_dir.resolve()
        if resolved in seen_dirs or not eval_dir.is_dir():
            continue
        seen_dirs.add(resolved)
        result_dir = eval_dir / "results"
        if not result_dir.is_dir():
            continue
        for file_path in result_dir.iterdir():
            if not file_path.is_file():
                continue
            match = RESULT_FILENAME_PATTERN.match(file_path.name)
            if match is None:
                continue
            timestamp = match.group(1)
            if not _has_matching_trace_snapshot(
                logs_dir=logs_dir,
                eval_dir=eval_dir,
                model_id=model_id,
                user_id=user_id,
                task_id=task_id,
                timestamp=timestamp,
            ):
                continue
            if latest is None or timestamp > latest[0]:
                latest = (timestamp, file_path)
    return latest[1] if latest is not None else None


def _has_matching_trace_snapshot(
    *,
    logs_dir: Path,
    eval_dir: Path,
    model_id: str,
    user_id: str,
    task_id: str,
    timestamp: str,
) -> bool:
    eval_trace_dir = eval_dir / "trace_logs" / timestamp
    if eval_trace_dir.is_dir() and any(
        path.is_file() and path.name.startswith("turn_") and path.suffix == ".json"
        for path in eval_trace_dir.iterdir()
    ):
        return True

    raw_trace_dir = logs_dir / _safe_model_id(model_id) / user_id / task_id / timestamp
    if raw_trace_dir.is_dir() and any(
        path.is_file() and path.name.startswith("turn_") and path.suffix == ".json"
        for path in raw_trace_dir.iterdir()
    ):
        return True
    return False


def _load_task_eval_result(
    *,
    logs_dir: Path | None,
    model_id: str,
    user_id: str,
    task_id: str,
) -> tuple[str, dict[str, Any]] | None:
    if logs_dir is None:
        return None
    result_path = _select_latest_eval_result_path(
        logs_dir=logs_dir,
        model_id=model_id,
        user_id=user_id,
        task_id=task_id,
    )
    if result_path is None:
        return None
    match = RESULT_FILENAME_PATTERN.match(result_path.name)
    if match is None:
        return None
    timestamp = match.group(1)
    try:
        with result_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return timestamp, payload


def _format_score_percent(score: Any, *, missing_text: str = "--") -> str:
    if score is None:
        return missing_text
    try:
        value = float(score)
    except (TypeError, ValueError):
        return missing_text
    if not math.isfinite(value):
        return missing_text
    return f"{value * 100:.2f}"


def _serialize_payload_for_html_script(payload: dict[str, Any]) -> str:
    # Embed JSON safely in <script type="application/json"> without allowing
    # any literal tag delimiters to terminate the script element early.
    return (
        json.dumps(payload, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _attach_intent_process(
    *,
    session_entries: list[dict[str, Any]],
    intent_turns: list[dict[str, Any]],
) -> None:
    for session in session_entries:
        turns = session.get("turns")
        if not isinstance(turns, list):
            continue
        for turn in turns:
            if isinstance(turn, dict):
                turn["intent_process"] = _empty_intent_process()

    if not session_entries:
        return
    latest_session = session_entries[0]
    turns = latest_session.get("turns")
    if not isinstance(turns, list):
        return
    for idx, intent_process in enumerate(intent_turns):
        if idx >= len(turns):
            break
        if not isinstance(turns[idx], dict):
            continue
        turns[idx]["intent_process"] = intent_process


def build_html(
    model_id: str,
    user_id: str,
    tasks: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    logs_dir: Path | None = None,
) -> str:
    episode_task_order = _load_episode_task_order(user_id)
    task_order_index = {task_id: idx for idx, task_id in enumerate(episode_task_order)}
    task_entries: list[dict[str, Any]] = []
    latest_user_result_timestamp: str | None = None
    latest_user_result_payload: dict[str, Any] | None = None
    for task_id, sessions in tasks.items():
        intent_turns = _load_task_intent_turns(
            logs_dir=logs_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_id,
        )
        task_eval_result = _load_task_eval_result(
            logs_dir=logs_dir,
            model_id=model_id,
            user_id=user_id,
            task_id=task_id,
        )
        task_result_payload: dict[str, Any] = {}
        task_checklist_payload: dict[str, Any] = {}
        task_proactiveness_payload: dict[str, Any] = {}
        if task_eval_result is not None:
            result_ts, result_payload = task_eval_result
            if latest_user_result_timestamp is None or result_ts > latest_user_result_timestamp:
                latest_user_result_timestamp = result_ts
                latest_user_result_payload = result_payload
            raw_task_payload = result_payload.get("task")
            if isinstance(raw_task_payload, dict):
                task_result_payload = raw_task_payload
            raw_checklist_payload = task_result_payload.get("checklist")
            if isinstance(raw_checklist_payload, dict):
                task_checklist_payload = raw_checklist_payload
            raw_proactiveness_payload = task_result_payload.get("proactiveness")
            if isinstance(raw_proactiveness_payload, dict):
                task_proactiveness_payload = raw_proactiveness_payload

        checklist_score = task_checklist_payload.get("average_score")
        proactiveness_score = task_proactiveness_payload.get("average_score")
        independent_proactiveness_score = task_proactiveness_payload.get("independent_average_score")
        if independent_proactiveness_score is None:
            independent_proactiveness_score = proactiveness_score
        checklist_criteria = task_checklist_payload.get("criterion_scores")
        checklist_criteria = checklist_criteria if isinstance(checklist_criteria, list) else []
        raw_turn_evaluations = task_checklist_payload.get("turn_evaluations")
        raw_turn_evaluations = raw_turn_evaluations if isinstance(raw_turn_evaluations, list) else []
        checklist_turn_evaluations: list[dict[str, Any]] = []
        for item in raw_turn_evaluations:
            if not isinstance(item, dict):
                continue
            try:
                turn_index = int(item.get("turn_index"))
            except (TypeError, ValueError):
                continue
            if turn_index < 1:
                continue
            criterion_scores = item.get("criterion_scores")
            criterion_scores = criterion_scores if isinstance(criterion_scores, list) else []
            llm_evaluation = item.get("llm_evaluation")
            llm_evaluation = llm_evaluation if isinstance(llm_evaluation, dict) else {}
            tools_evaluation = item.get("tools_evaluation")
            tools_evaluation = tools_evaluation if isinstance(tools_evaluation, dict) else {}
            checklist_turn_evaluations.append(
                {
                    "turn_index": turn_index,
                    "average_score": item.get("average_score"),
                    "criterion_scores": criterion_scores,
                    "llm_evaluation": llm_evaluation,
                    "tools_evaluation": tools_evaluation,
                }
            )
        checklist_turn_evaluations.sort(key=lambda item: int(item["turn_index"]))

        session_entries: list[dict[str, Any]] = []
        task_latest = 0.0
        task_turn_count = 0
        for session_id, turns in sessions.items():
            loaded_turns: list[dict[str, Any]] = []
            session_latest = 0.0
            for turn in turns:
                try:
                    with open(turn["path"], "r", encoding="utf-8") as handle:
                        content = json.load(handle)
                except Exception:
                    content = {"error": "failed to load"}
                session_latest = max(session_latest, float(turn["mtime"]))
                loaded_turns.append(
                    {
                        "name": turn["name"],
                        "mtime": turn["mtime"],
                        "meta": turn.get("meta") or {},
                        "rel_path": turn["rel_path"],
                        "data": content,
                        "checklist_evaluation": {},
                    }
                )
            session_entries.append(
                {
                    "sessionId": session_id,
                    "turnCount": len(loaded_turns),
                    "latest": session_latest,
                    "turns": loaded_turns,
                }
            )
            task_latest = max(task_latest, session_latest)
            task_turn_count += len(loaded_turns)

        session_entries.sort(key=lambda item: item["sessionId"], reverse=True)
        if session_entries:
            turn_eval_by_index = {
                int(item["turn_index"]): item for item in checklist_turn_evaluations if isinstance(item, dict)
            }
            latest_turns = session_entries[0].get("turns")
            if isinstance(latest_turns, list):
                for idx, turn in enumerate(latest_turns, start=1):
                    if isinstance(turn, dict):
                        turn["checklist_evaluation"] = turn_eval_by_index.get(idx, {})
        _attach_intent_process(session_entries=session_entries, intent_turns=intent_turns)
        task_entries.append(
            {
                "taskId": task_id,
                "sessionCount": len(session_entries),
                "turnCount": task_turn_count,
                "latest": task_latest,
                "sessions": session_entries,
                "evaluation": {
                    "checklistScore": checklist_score,
                    "checklistScoreText": _format_score_percent(checklist_score, missing_text="none"),
                    "proactivenessScore": proactiveness_score,
                    "proactivenessScoreText": _format_score_percent(proactiveness_score, missing_text="none"),
                    "independentProactivenessScore": independent_proactiveness_score,
                    "independentProactivenessScoreText": _format_score_percent(
                        independent_proactiveness_score,
                        missing_text="none",
                    ),
                    "checklistCriteria": checklist_criteria,
                    "checklistTurnEvaluations": checklist_turn_evaluations,
                },
            }
        )

    if task_order_index:
        task_entries.sort(
            key=lambda item: (
                task_order_index.get(item["taskId"], len(task_order_index)),
                -item["latest"],
                item["taskId"],
            )
        )
    else:
        task_entries.sort(key=lambda item: (item["latest"], item["taskId"]), reverse=True)
    user_checklist_score = None
    user_proactiveness_score = None
    if isinstance(latest_user_result_payload, dict):
        user_checklist_score = latest_user_result_payload.get("overall_checklist_average_score")
        user_proactiveness_score = latest_user_result_payload.get("overall_proactiveness_average_score")

    payload = {
        "modelId": model_id,
        "userId": user_id,
        "taskCount": len(task_entries),
        "userEvaluation": {
            "checklistScore": user_checklist_score,
            "checklistScoreText": _format_score_percent(user_checklist_score, missing_text="none"),
            "proactivenessScore": user_proactiveness_score,
            "proactivenessScoreText": _format_score_percent(user_proactiveness_score, missing_text="none"),
        },
        "tasks": task_entries,
    }
    data_json = _serialize_payload_for_html_script(payload)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trace Viewer · {model_id} · {user_id}</title>
  <style>
    :root {{
      --bg: #f4efe7;
      --bg-strong: #e7ddcf;
      --panel: rgba(255, 250, 243, 0.84);
      --panel-strong: rgba(255, 248, 239, 0.96);
      --panel-border: rgba(88, 62, 38, 0.16);
      --text: #1f1a16;
      --muted: #6f6458;
      --accent: #a8432f;
      --accent-soft: rgba(168, 67, 47, 0.12);
      --accent-strong: #7f2414;
      --shadow: 0 22px 54px rgba(80, 51, 23, 0.12);
      --mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
      --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: var(--sans);
      background:
        radial-gradient(circle at top left, rgba(168, 67, 47, 0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(67, 114, 161, 0.12), transparent 24%),
        linear-gradient(180deg, #f7f2ea 0%, #efe6d8 100%);
    }}

    .shell {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 28px;
    }}

    .hero {{
      position: relative;
      overflow: hidden;
      padding: 28px 30px;
      border: 1px solid var(--panel-border);
      border-radius: 28px;
      background:
        linear-gradient(135deg, rgba(255, 251, 246, 0.94), rgba(246, 236, 222, 0.9)),
        linear-gradient(120deg, rgba(168, 67, 47, 0.06), rgba(86, 120, 84, 0.05));
      box-shadow: var(--shadow);
    }}

    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -60px -80px auto;
      width: 220px;
      height: 220px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(168, 67, 47, 0.18), transparent 68%);
      pointer-events: none;
    }}

    .hero-top {{
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: flex-start;
      flex-wrap: wrap;
    }}

    .eyebrow {{
      display: inline-flex;
      gap: 10px;
      align-items: center;
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    .eyebrow::before {{
      content: "";
      width: 28px;
      height: 1px;
      background: rgba(31, 26, 22, 0.24);
    }}

    h1 {{
      margin: 14px 0 8px;
      font-size: clamp(30px, 5vw, 52px);
      line-height: 0.96;
      letter-spacing: -0.04em;
    }}

    .subhead {{
      max-width: 820px;
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.6;
    }}

    .hero-metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(140px, 1fr));
      gap: 12px;
      min-width: min(100%, 420px);
    }}

    .metric {{
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.52);
      border: 1px solid rgba(88, 62, 38, 0.12);
      backdrop-filter: blur(8px);
    }}

    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .metric-value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.04em;
    }}

    .layout {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 20px;
      margin-top: 22px;
      align-items: start;
    }}

    .panel {{
      border: 1px solid var(--panel-border);
      border-radius: 26px;
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}

    .panel-head {{
      padding: 20px 22px 0;
    }}

    .panel-title {{
      margin: 0;
      font-size: 13px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    .panel-caption {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.02em;
      opacity: 0.9;
    }}

    .task-list {{
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .task-button {{
      width: 100%;
      border: 1px solid transparent;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.44);
      padding: 16px;
      text-align: left;
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
    }}

    .task-button:hover {{
      transform: translateY(-1px);
      border-color: rgba(127, 36, 20, 0.18);
      background: rgba(255, 255, 255, 0.72);
    }}

    .task-button.active {{
      background: linear-gradient(135deg, rgba(168, 67, 47, 0.12), rgba(255, 255, 255, 0.84));
      border-color: rgba(127, 36, 20, 0.28);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.42);
    }}

    .task-name {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}

    .task-meta {{
      margin-top: 8px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .task-score-line {{
      margin-top: 10px;
      color: var(--accent-strong);
      font-size: 12px;
      font-family: var(--mono);
      letter-spacing: 0.01em;
    }}

    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.74);
      color: var(--muted);
      font-size: 12px;
      border: 1px solid rgba(88, 62, 38, 0.1);
    }}

    .content {{
      padding: 22px;
    }}

    .content-top {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}

    .hero-eval {{
      margin-top: 16px;
    }}

    .task-eval {{
      margin-bottom: 18px;
    }}

    .section-kicker {{
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}

    .section-title {{
      margin: 0;
      font-size: clamp(24px, 4vw, 40px);
      letter-spacing: -0.04em;
      line-height: 1;
    }}

    .section-note {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}

    .session-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}

    .session-button {{
      border: 1px solid rgba(88, 62, 38, 0.12);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.62);
      padding: 16px;
      text-align: left;
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
    }}

    .session-button:hover {{
      transform: translateY(-1px);
      border-color: rgba(127, 36, 20, 0.18);
    }}

    .session-button.active {{
      background: linear-gradient(180deg, rgba(168, 67, 47, 0.14), rgba(255, 255, 255, 0.86));
      border-color: rgba(127, 36, 20, 0.28);
    }}

    .session-name {{
      font-family: var(--mono);
      font-size: 13px;
      color: var(--accent-strong);
    }}

    .session-stats {{
      margin-top: 10px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .turns {{
      display: grid;
      gap: 16px;
    }}

    .turn-card {{
      overflow: hidden;
      border: 1px solid rgba(88, 62, 38, 0.12);
      border-radius: 22px;
      background: var(--panel-strong);
      box-shadow: 0 18px 32px rgba(72, 45, 20, 0.08);
    }}

    .turn-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      flex-wrap: wrap;
      padding: 18px 20px;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.84), rgba(244, 235, 224, 0.92));
      border-bottom: 1px solid rgba(88, 62, 38, 0.08);
    }}

    .turn-name {{
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}

    .turn-path {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
      font-family: var(--mono);
    }}

    .turn-stack {{
      display: grid;
      gap: 14px;
      padding: 18px 20px 20px;
    }}

    .fold {{
      min-width: 0;
      border-radius: 18px;
      background: rgba(249, 244, 238, 0.82);
      border: 1px solid rgba(88, 62, 38, 0.08);
      overflow: hidden;
      transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }}

    .fold[open] {{
      background: rgba(255, 252, 248, 0.95);
      border-color: rgba(127, 36, 20, 0.18);
      box-shadow: 0 14px 28px rgba(72, 45, 20, 0.08);
    }}

    .fold-summary {{
      list-style: none;
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 16px 18px;
      cursor: pointer;
      user-select: none;
      transition: background 140ms ease;
    }}

    .fold-summary:hover {{
      background: rgba(168, 67, 47, 0.06);
    }}

    .fold-summary::-webkit-details-marker {{
      display: none;
    }}

    .fold-title {{
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      font-weight: 700;
    }}

    .fold-meta {{
      margin-left: auto;
      max-width: min(56%, 640px);
      color: var(--accent-strong);
      font-size: 12px;
      text-align: right;
      line-height: 1.5;
    }}

    .fold-caret {{
      flex: 0 0 auto;
      width: 12px;
      height: 12px;
      border-right: 2px solid rgba(127, 36, 20, 0.72);
      border-bottom: 2px solid rgba(127, 36, 20, 0.72);
      transform: rotate(45deg);
      transition: transform 160ms ease, opacity 160ms ease;
      opacity: 0.76;
    }}

    .fold[open] .fold-caret {{
      transform: rotate(225deg);
      opacity: 1;
    }}

    .fold-content {{
      padding: 0 18px 18px;
      border-top: 1px solid rgba(88, 62, 38, 0.08);
    }}

    pre {{
      margin: 0;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font: 12px/1.6 var(--mono);
      color: #2a241f;
    }}

    .step-list {{
      display: grid;
      gap: 10px;
      padding-top: 12px;
    }}

    .step-fold {{
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.78);
      border-color: rgba(88, 62, 38, 0.08);
    }}

    .step-fold .fold-summary {{
      padding: 14px 16px;
    }}

    .step-fold .fold-content {{
      padding: 0 16px 16px;
    }}

    .code-group {{
      display: grid;
      gap: 10px;
      padding-top: 12px;
    }}

    .code-block {{
      padding: 12px;
      border-radius: 14px;
      background: rgba(247, 241, 234, 0.88);
      border: 1px solid rgba(88, 62, 38, 0.08);
    }}

    .code-label {{
      margin: 0 0 8px;
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .call-list {{
      display: grid;
      gap: 10px;
    }}

    .call-card {{
      padding: 12px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(88, 62, 38, 0.08);
    }}

    .fold-meta-rich {{
      max-width: none;
      min-width: max-content;
      display: flex;
      flex: 0 0 auto;
      justify-content: flex-end;
      text-align: right;
      overflow-x: auto;
      overflow-y: hidden;
    }}

    .intent-meta-blocks {{
      display: inline-flex;
      flex-direction: row;
      gap: 8px;
      align-items: center;
      min-width: 0;
      flex: 0 0 auto;
      width: max-content;
    }}

    .intent-meta-row {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      justify-content: flex-end;
      flex-wrap: nowrap;
      white-space: nowrap;
      min-width: max-content;
      width: max-content;
    }}

    .intent-meta-key {{
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
      flex: 0 0 auto;
    }}

    .intent-meta-values {{
      display: inline-flex;
      justify-content: flex-end;
      gap: 0;
      text-align: right;
      min-width: 0;
      white-space: nowrap;
      flex: 0 0 auto;
      width: max-content;
    }}

    .intent-meta-row,
    .intent-meta-row * {{
      white-space: nowrap !important;
      word-break: keep-all;
    }}

    .intent-pill {{
      padding: 4px 8px;
      background: rgba(168, 67, 47, 0.08);
      border-color: rgba(127, 36, 20, 0.2);
      color: var(--accent-strong);
      font-family: var(--mono);
      font-size: 11px;
      display: inline-flex;
      white-space: nowrap;
    }}

    .intent-meta-chip {{
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
    }}

    .intent-chip-key {{
      font-family: var(--sans);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    .intent-chip-sep {{
      color: rgba(127, 36, 20, 0.45);
      font-size: 10px;
      line-height: 1;
    }}

    .intent-chip-value {{
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--accent-strong);
    }}

    .intent-empty {{
      color: var(--muted);
      font-style: italic;
      font-size: 12px;
    }}

    .call-head {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }}

    .call-name {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}

    .call-id {{
      color: var(--muted);
      font-size: 11px;
      font-family: var(--mono);
    }}

    .inline-empty {{
      padding-top: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }}

    .checklist-matrix-wrap {{
      overflow-x: auto;
      padding-top: 12px;
    }}

    .checklist-matrix {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(88, 62, 38, 0.12);
      border-radius: 12px;
      overflow: hidden;
    }}

    .checklist-matrix th,
    .checklist-matrix td {{
      border: 1px solid rgba(88, 62, 38, 0.08);
      padding: 8px 10px;
      text-align: center;
      white-space: nowrap;
      font-family: var(--mono);
    }}

    .checklist-matrix thead th {{
      background: rgba(168, 67, 47, 0.08);
      color: var(--accent-strong);
      font-weight: 700;
    }}

    .checklist-matrix .turn-col {{
      text-align: left;
      font-weight: 700;
      color: var(--accent-strong);
      background: rgba(255, 255, 255, 0.8);
    }}

    .checklist-matrix .overall-row td {{
      font-weight: 700;
      background: rgba(168, 67, 47, 0.06);
    }}

    .check-cell {{
      font-size: 15px;
      font-weight: 700;
      line-height: 1;
    }}

    .check-cell.yes {{
      color: #2f7a3c;
    }}

    .check-cell.no {{
      color: #9b3b2f;
    }}

    .empty {{
      padding: 42px 24px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed rgba(88, 62, 38, 0.18);
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.42);
    }}

    @media (max-width: 1080px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}

      .hero-metrics {{
        grid-template-columns: repeat(3, minmax(100px, 1fr));
      }}
    }}

    @media (max-width: 760px) {{
      .shell {{
        padding: 16px;
      }}

      .hero,
      .content {{
        padding: 18px;
      }}

      .turn-stack {{
        padding: 16px;
      }}

      .fold-summary {{
        align-items: flex-start;
      }}

      .fold-meta {{
        max-width: none;
      }}

      .hero-metrics {{
        grid-template-columns: 1fr;
      }}

      .fold-meta-rich {{
        max-width: none;
        min-width: max-content;
        justify-content: flex-end;
      }}

      .intent-meta-blocks {{
        align-items: center;
      }}

      .intent-meta-row {{
        justify-content: flex-end;
      }}

      .intent-meta-values {{
        justify-content: flex-end;
        text-align: right;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-top">
        <div>
          <div class="eyebrow">Trace Viewer</div>
          <h1>{model_id} / {user_id}</h1>
        </div>
        <div class="hero-metrics">
          <div class="metric">
            <div class="metric-label">Tasks</div>
            <div class="metric-value" id="metric-task-count">0</div>
          </div>
          <div class="metric">
            <div class="metric-label">Sessions</div>
            <div class="metric-value" id="metric-session-count">0</div>
          </div>
          <div class="metric">
            <div class="metric-label">Turns</div>
            <div class="metric-value" id="metric-turn-count">0</div>
          </div>
        </div>
      </div>
      <div id="user-eval" class="hero-eval"></div>
    </section>

    <div class="layout">
      <aside class="panel">
        <div class="panel-head">
          <p class="panel-title">Task Navigator</p>
          <p class="panel-caption">C = Checklist · P = Proactiveness · IP = Independent Proactiveness</p>
        </div>
        <div id="task-list" class="task-list"></div>
      </aside>

      <section class="panel content">
        <div class="content-top">
          <div>
            <p class="section-kicker">Current Task</p>
            <h2 id="task-title" class="section-title">暂无 task</h2>
            <p id="task-note" class="section-note">未找到 trace turns。</p>
          </div>
        </div>

        <div id="task-eval" class="task-eval"></div>
        <div id="session-strip" class="session-strip"></div>
        <div id="turns" class="turns"></div>
      </section>
    </div>
  </div>

  <script id="trace-data" type="application/json">{data_json}</script>
  <script>
    (() => {{
      const DATA = JSON.parse(document.getElementById("trace-data").textContent);
      const taskList = document.getElementById("task-list");
      const taskTitle = document.getElementById("task-title");
      const taskNote = document.getElementById("task-note");
      const userEvalRoot = document.getElementById("user-eval");
      const taskEvalRoot = document.getElementById("task-eval");
      const sessionStrip = document.getElementById("session-strip");
      const turnsRoot = document.getElementById("turns");

      document.getElementById("metric-task-count").textContent = String(DATA.taskCount);
      document.getElementById("metric-session-count").textContent = String(
        DATA.tasks.reduce((sum, task) => sum + task.sessionCount, 0)
      );
      document.getElementById("metric-turn-count").textContent = String(
        DATA.tasks.reduce((sum, task) => sum + task.turnCount, 0)
      );

      const state = {{
        taskId: DATA.tasks[0] ? DATA.tasks[0].taskId : null,
        sessionId: DATA.tasks[0] && DATA.tasks[0].sessions[0] ? DATA.tasks[0].sessions[0].sessionId : null,
      }};

      function escapeHtml(value) {{
        const div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
      }}

      function formatTime(ts) {{
        if (!ts) return "unknown";
        return new Date(ts * 1000).toLocaleString("zh-CN");
      }}

      function findTask(taskId) {{
        return DATA.tasks.find((task) => task.taskId === taskId) || null;
      }}

      function findSession(task, sessionId) {{
        if (!task) return null;
        return task.sessions.find((session) => session.sessionId === sessionId) || null;
      }}

      function summarizeToolCalls(toolCalls) {{
        if (!Array.isArray(toolCalls) || toolCalls.length === 0) {{
          return "No tool calls";
        }}
        const counts = new Map();
        toolCalls.forEach((call) => {{
          const name = call && typeof call === "object" ? (call.name || "unknown") : "unknown";
          counts.set(name, (counts.get(name) || 0) + 1);
        }});
        return Array.from(counts.entries())
          .map(([name, count]) => count === 1 ? name : `${{name}} ×${{count}}`)
          .join(" · ");
      }}

      function renderFold(title, meta, content, extraClass = "", defaultOpen = false, metaIsHtml = false) {{
        const metaHtml = !meta
          ? ""
          : metaIsHtml
            ? `<span class="fold-meta fold-meta-rich">${{meta}}</span>`
            : `<span class="fold-meta">${{escapeHtml(meta)}}</span>`;
        const className = ["fold", extraClass].filter(Boolean).join(" ");
        const openAttr = defaultOpen ? " open" : "";
        return `
          <details class="${{className}}"${{openAttr}}>
            <summary class="fold-summary">
              <span class="fold-title">${{escapeHtml(title)}}</span>
              ${{metaHtml}}
              <span class="fold-caret" aria-hidden="true"></span>
            </summary>
            <div class="fold-content">${{content}}</div>
          </details>
        `;
      }}

      function renderCodeBlock(label, value) {{
        return `
          <div class="code-block">
            <h4 class="code-label">${{escapeHtml(label)}}</h4>
            <pre>${{escapeHtml(value == null ? "" : String(value))}}</pre>
          </div>
        `;
      }}

      function renderJsonBlock(label, value) {{
        return renderCodeBlock(label, JSON.stringify(value || {{}}, null, 2));
      }}

      function renderToolCallCards(toolCalls) {{
        if (!Array.isArray(toolCalls) || toolCalls.length === 0) {{
          return '<div class="inline-empty">No tool calls for this iteration.</div>';
        }}
        return `
          <div class="call-list">
            ${{
              toolCalls.map((call) => `
                <div class="call-card">
                  <div class="call-head">
                    <div class="call-name">${{escapeHtml(call.name || "unknown")}}</div>
                    <div class="call-id">${{escapeHtml(call.id || "")}}</div>
                  </div>
                  ${{renderJsonBlock("Arguments", call.arguments || {{}})}}
                </div>
              `).join("")
            }}
          </div>
        `;
      }}

      function formatScoreText(value) {{
        if (typeof value === "number" && Number.isFinite(value)) {{
          return value.toFixed(2);
        }}
        if (typeof value === "string" && value.trim()) {{
          return value;
        }}
        return "none";
      }}

      function renderScoreMetaChip(label, valueText) {{
        const safeLabel = escapeHtml(label || "-");
        const safeValue = escapeHtml(valueText || "none");
        return `
          <span class="pill intent-pill intent-meta-chip">
            <span class="intent-chip-key">${{safeLabel}}</span>
            <span class="intent-chip-sep">:</span>
            <span class="intent-chip-value">${{safeValue}}</span>
          </span>
        `;
      }}

      function renderScoreMetaBlocks(rows) {{
        const safeRows = Array.isArray(rows) ? rows : [];
        if (safeRows.length === 0) return "";
        return `
          <span class="intent-meta-blocks">
            ${{
              safeRows.map((row) => `
                <span class="intent-meta-row">
                  ${{renderScoreMetaChip(row.label || "-", row.valueText || "none")}}
                </span>
              `).join("")
            }}
          </span>
        `;
      }}

      function renderChecklistDetailCards(details) {{
        if (!Array.isArray(details) || details.length === 0) {{
          return '<div class="inline-empty">No checklist details.</div>';
        }}
        return `
          <div class="call-list">
            ${{
              details.map((item) => `
                <div class="call-card">
                  <div class="call-head">
                    <div class="call-name">c${{escapeHtml(item.index ?? "?")}} · ${{escapeHtml(item.score || "-")}}</div>
                    <div class="call-id">w=${{escapeHtml(item.weight ?? "-")}} · weighted=${{escapeHtml(item.weighted_value ?? "-")}}</div>
                  </div>
                  <pre>${{escapeHtml(item.criterion || "")}}</pre>
                </div>
              `).join("")
            }}
          </div>
        `;
      }}

      function renderChecklistLlmEvaluation(llmEvaluation) {{
        const payload = llmEvaluation && typeof llmEvaluation === "object" ? llmEvaluation : {{}};
        const prompt = payload.prompt || "";
        const rawResponses = Array.isArray(payload.raw_responses) ? payload.raw_responses : [];
        const responsesContent = rawResponses.length === 0
          ? '<div class="inline-empty">No raw responses.</div>'
          : `
              <div class="call-list">
                ${{
                  rawResponses.map((response, index) => `
                    <div class="call-card">
                      <div class="call-head">
                        <div class="call-name">Response ${{escapeHtml(index + 1)}}</div>
                        <div class="call-id">${{escapeHtml(String(response || "").length)}} chars</div>
                      </div>
                      <pre>${{escapeHtml(response || "")}}</pre>
                    </div>
                  `).join("")
                }}
              </div>
            `;
        return `
          <div class="step-list">
            ${{renderFold("Prompt", `${{String(prompt).length}} chars`, `<pre>${{escapeHtml(prompt)}}</pre>`, "step-fold")}}
            ${{renderFold("Response", `${{rawResponses.length}} items`, responsesContent, "step-fold")}}
          </div>
        `;
      }}

      function renderChecklistToolsEvaluation(toolsEvaluation) {{
        const payload = toolsEvaluation && typeof toolsEvaluation === "object" ? toolsEvaluation : {{}};
        const scriptPath = String(payload.script_path || "").trim();
        const scriptCode = String(payload.script_code || "");
        const rawOutput = Object.prototype.hasOwnProperty.call(payload, "raw_output") ? payload.raw_output : null;
        const errorText = String(payload.error || "").trim();

        if (!scriptPath && !scriptCode && rawOutput == null && !errorText) {{
          return '<div class="inline-empty">No tools raw evaluation.</div>';
        }}

        const outputDictText = (() => {{
          try {{
            return JSON.stringify(rawOutput, null, 2);
          }} catch (_error) {{
            return String(rawOutput == null ? "" : rawOutput);
          }}
        }})();

        const outputMeta = rawOutput == null ? "none" : `${{outputDictText.length}} chars`;
        const errorBlock = !errorText
          ? ""
          : renderFold("Error", "", `<pre>${{escapeHtml(errorText)}}</pre>`, "step-fold");

        return `
          <div class="step-list">
            ${{renderFold("Code", scriptPath || "", `<pre>${{escapeHtml(scriptCode)}}</pre>`, "step-fold")}}
            ${{renderFold("Output Dict", outputMeta, `<pre>${{escapeHtml(outputDictText)}}</pre>`, "step-fold")}}
            ${{errorBlock}}
          </div>
        `;
      }}

      function isChecklistYes(value) {{
        const normalized = String(value || "").trim().toUpperCase();
        return normalized === "YES" || value === 1 || value === true;
      }}

      function renderChecklistSymbol(value) {{
        const isYes = isChecklistYes(value);
        return `<span class="check-cell ${{isYes ? "yes" : "no"}}">${{isYes ? "✓" : "✗"}}</span>`;
      }}

      function normalizeChecklistTurnEvaluations(value) {{
        if (!Array.isArray(value)) {{
          return [];
        }}
        return value
          .filter((item) => item && typeof item === "object")
          .map((item) => {{
            const turnIndex = Number(item.turn_index);
            return {{
              turn_index: Number.isInteger(turnIndex) && turnIndex > 0 ? turnIndex : null,
              criterion_scores: Array.isArray(item.criterion_scores) ? item.criterion_scores : [],
              llm_evaluation: item.llm_evaluation && typeof item.llm_evaluation === "object" ? item.llm_evaluation : {{}},
              tools_evaluation: item.tools_evaluation && typeof item.tools_evaluation === "object" ? item.tools_evaluation : {{}},
            }};
          }})
          .filter((item) => item.turn_index !== null)
          .sort((a, b) => a.turn_index - b.turn_index);
      }}

      function renderChecklistTurnMatrix(criteria, turnEvaluations) {{
        const safeCriteria = Array.isArray(criteria) ? criteria : [];
        const safeTurns = normalizeChecklistTurnEvaluations(turnEvaluations);
        if (safeCriteria.length === 0 || safeTurns.length === 0) {{
          return '<div class="inline-empty">No turn-level checklist matrix.</div>';
        }}

        const headerCells = safeCriteria.map((item) => {{
          const idx = Number(item && item.index);
          const text = Number.isInteger(idx) && idx > 0 ? `c${{idx}}` : "c?";
          return `<th>${{escapeHtml(text)}}</th>`;
        }}).join("");

        const overallByIndex = new Map();
        safeTurns.forEach((turn) => {{
          turn.criterion_scores.forEach((scoreItem) => {{
            const idx = Number(scoreItem && scoreItem.index);
            if (!Number.isInteger(idx) || idx < 1) return;
            const scoreValue = scoreItem && (scoreItem.score ?? scoreItem.value);
            if (isChecklistYes(scoreValue)) {{
              overallByIndex.set(idx, true);
              return;
            }}
            if (!overallByIndex.has(idx)) {{
              overallByIndex.set(idx, false);
            }}
          }});
        }});

        const bodyRows = safeTurns.map((turn) => {{
          const scoresByIndex = new Map();
          turn.criterion_scores.forEach((scoreItem) => {{
            const idx = Number(scoreItem && scoreItem.index);
            if (!Number.isInteger(idx) || idx < 1) return;
            const scoreValue = scoreItem && (scoreItem.score ?? scoreItem.value);
            scoresByIndex.set(idx, scoreValue);
          }});
          const cells = safeCriteria.map((criterion) => {{
            const idx = Number(criterion && criterion.index);
            const score = Number.isInteger(idx) ? scoresByIndex.get(idx) : null;
            return `<td>${{renderChecklistSymbol(score)}}</td>`;
          }}).join("");
          return `<tr><td class="turn-col">${{escapeHtml(`t${{turn.turn_index}}`)}}</td>${{cells}}</tr>`;
        }}).join("");

        const overallCells = safeCriteria.map((criterion) => {{
          const idx = Number(criterion && criterion.index);
          const score = Number.isInteger(idx) ? overallByIndex.get(idx) : null;
          return `<td>${{renderChecklistSymbol(score)}}</td>`;
        }}).join("");

        const overallRow = `<tr class="overall-row"><td class="turn-col">Overall</td>${{overallCells}}</tr>`;

        return `
          <div class="checklist-matrix-wrap">
            <table class="checklist-matrix">
              <thead>
                <tr>
                  <th class="turn-col">Turn</th>
                  ${{headerCells}}
                </tr>
              </thead>
              <tbody>
                ${{bodyRows}}
                ${{overallRow}}
              </tbody>
            </table>
          </div>
        `;
      }}

      function renderTaskEvaluation(task) {{
        const evaluation = task && task.evaluation && typeof task.evaluation === "object" ? task.evaluation : {{}};
        const checklistScore = formatScoreText(evaluation.checklistScoreText);
        const proactivenessScore = formatScoreText(evaluation.proactivenessScoreText);
        const independentProactivenessScore = formatScoreText(evaluation.independentProactivenessScoreText);
        const scoreBlocks = renderScoreMetaBlocks([
          {{ label: "Checklist", valueText: checklistScore }},
          {{ label: "Proactiveness", valueText: proactivenessScore }},
          {{ label: "INDEPENDENT PROACTIVENESS", valueText: independentProactivenessScore }},
        ]);
        const checklistCriteria = Array.isArray(evaluation.checklistCriteria) ? evaluation.checklistCriteria : [];
        const checklistTurns = normalizeChecklistTurnEvaluations(evaluation.checklistTurnEvaluations);
        const content = `
          <div class="step-list">
            ${{renderFold(
              "Checklist Turn Outcomes",
              `${{checklistTurns.length}} turns · ${{checklistCriteria.length}} criteria`,
              `${{renderChecklistTurnMatrix(checklistCriteria, checklistTurns)}}`,
              "step-fold",
              true
            )}}
          </div>
        `;
        return renderFold(
          "Task Evaluation Scores",
          scoreBlocks,
          content,
          "",
          true,
          true
        );
      }}

      function renderTurnChecklistEvaluation(checklistEvaluation) {{
        const payload = checklistEvaluation && typeof checklistEvaluation === "object" ? checklistEvaluation : {{}};
        const details = Array.isArray(payload.criterion_scores) ? payload.criterion_scores : [];
        const llmEvaluation = payload.llm_evaluation && typeof payload.llm_evaluation === "object" ? payload.llm_evaluation : {{}};
        const toolsEvaluation = payload.tools_evaluation && typeof payload.tools_evaluation === "object" ? payload.tools_evaluation : {{}};
        const content = `
          <div class="step-list">
            ${{renderFold(
              "Checklist Details",
              `${{details.length}} items`,
              `${{renderChecklistDetailCards(details)}}`,
              "step-fold"
            )}}
            ${{renderFold(
              "Checklist LLM Raw Evaluation",
              "",
              `${{renderChecklistLlmEvaluation(llmEvaluation)}}`,
              "step-fold"
            )}}
            ${{renderFold(
              "Checklist Tools Raw Evaluation",
              "",
              `${{renderChecklistToolsEvaluation(toolsEvaluation)}}`,
              "step-fold"
            )}}
          </div>
        `;
        return renderFold("Checklist Evaluation", `${{details.length}} criteria`, content);
      }}

      function renderUserEvaluation() {{
        const evaluation = DATA.userEvaluation && typeof DATA.userEvaluation === "object" ? DATA.userEvaluation : {{}};
        const checklistScore = formatScoreText(evaluation.checklistScoreText);
        const proactivenessScore = formatScoreText(evaluation.proactivenessScoreText);
        userEvalRoot.innerHTML = `
          <div class="task-meta">
            ${{renderScoreMetaBlocks([
              {{ label: "Checklist", valueText: checklistScore }},
              {{ label: "Proactiveness", valueText: proactivenessScore }},
            ])}}
          </div>
        `;
      }}

      function renderTasks() {{
        if (DATA.tasks.length === 0) {{
          taskList.innerHTML = '<div class="empty">暂无 task trace</div>';
          return;
        }}
        taskList.innerHTML = DATA.tasks.map((task) => `
          <button class="task-button ${{task.taskId === state.taskId ? "active" : ""}}" data-task-id="${{escapeHtml(task.taskId)}}">
            <div class="task-name">${{escapeHtml(task.taskId)}}</div>
            <div class="task-meta">
              <span class="pill">${{task.sessionCount}} sessions</span>
              <span class="pill">${{task.turnCount}} turns</span>
            </div>
            <div class="task-score-line">
              ${{renderScoreMetaBlocks([
                {{ label: "C", valueText: formatScoreText(task.evaluation && task.evaluation.checklistScoreText) }},
                {{ label: "P", valueText: formatScoreText(task.evaluation && task.evaluation.proactivenessScoreText) }},
                {{ label: "IP", valueText: formatScoreText(task.evaluation && task.evaluation.independentProactivenessScoreText) }},
              ])}}
            </div>
          </button>
        `).join("");
        taskList.querySelectorAll(".task-button").forEach((button) => {{
          button.addEventListener("click", () => {{
            state.taskId = button.dataset.taskId;
            const task = findTask(state.taskId);
            state.sessionId = task && task.sessions[0] ? task.sessions[0].sessionId : null;
            render();
          }});
        }});
      }}

      function renderSessions(task) {{
        if (!task || task.sessions.length === 0) {{
          sessionStrip.innerHTML = '<div class="empty">当前 task 没有 session。</div>';
          return;
        }}
        sessionStrip.innerHTML = task.sessions.map((session) => `
          <button class="session-button ${{session.sessionId === state.sessionId ? "active" : ""}}" data-session-id="${{escapeHtml(session.sessionId)}}">
            <div class="session-name">${{escapeHtml(session.sessionId)}}</div>
            <div class="session-stats">
              <span class="pill">${{session.turnCount}} turns</span>
              <span class="pill">${{formatTime(session.latest)}}</span>
            </div>
          </button>
        `).join("");
        sessionStrip.querySelectorAll(".session-button").forEach((button) => {{
          button.addEventListener("click", () => {{
            state.sessionId = button.dataset.sessionId;
            render();
          }});
        }});
      }}

      function renderToolSteps(toolSteps) {{
        const steps = Array.isArray(toolSteps) ? toolSteps : [];
        const content = steps.length === 0
          ? '<div class="inline-empty">No tool steps recorded for this turn.</div>'
          : `
              <div class="step-list">
                ${{
                  steps.map((step, index) => renderFold(
                    step.name || `Tool ${{index + 1}}`,
                    `Step ${{index + 1}}`,
                    `
                      <div class="code-group">
                        ${{renderJsonBlock("Arguments", step.arguments || {{}})}}
                        ${{renderCodeBlock(
                          "Result",
                          typeof step.result === "string"
                            ? step.result
                            : JSON.stringify(step.result || {{}}, null, 2)
                        )}}
                      </div>
                    `,
                    "step-fold"
                  )).join("")
                }}
              </div>
            `;
        return renderFold("Tool Steps", `${{steps.length}} steps`, content);
      }}

      function renderLlmSteps(llmSteps) {{
        const steps = Array.isArray(llmSteps) ? llmSteps : [];
        const content = steps.length === 0
          ? '<div class="inline-empty">No LLM steps recorded for this turn.</div>'
          : `
              <div class="step-list">
                ${{
                  steps.map((step) => renderFold(
                    `Iteration ${{step.iteration ?? "?"}}`,
                    summarizeToolCalls(step.tool_calls),
                    `
                      <div class="code-group">
                        ${{renderCodeBlock("Reasoning", step.reasoning_content || "")}}
                        ${{renderToolCallCards(step.tool_calls)}}
                        ${{renderCodeBlock("Response", step.response_content || "")}}
                      </div>
                    `,
                    "step-fold"
                  )).join("")
                }}
              </div>
            `;
        return renderFold("LLM Steps", `${{steps.length}} iterations`, content);
      }}

      function renderSteps(llmSteps, toolSteps) {{
        const llm = Array.isArray(llmSteps) ? llmSteps : [];
        const tools = Array.isArray(toolSteps) ? toolSteps : [];
        const content = `
          <div class="step-list">
            ${{renderLlmSteps(llm)}}
            ${{renderToolSteps(tools)}}
          </div>
        `;
        return renderFold("Steps", `${{llm.length}} llm · ${{tools.length}} tools`, content);
      }}

      function normalizeIndexes(value) {{
        if (!Array.isArray(value)) {{
          return [];
        }}
        return value
          .map((item) => Number(item))
          .filter((item, index, arr) => Number.isInteger(item) && item > 0 && arr.indexOf(item) === index);
      }}

      function renderNumberText(value) {{
        const number = Number(value);
        if (!Number.isFinite(number)) {{
          return "0";
        }}
        return String(number);
      }}

      function renderIndexListText(value) {{
        const indexes = normalizeIndexes(value);
        if (indexes.length === 0) {{
          return "none";
        }}
        return indexes.join(" ");
      }}

      function renderIntentMetaChip(label, valueText) {{
        const safeLabel = escapeHtml(label || "-");
        const safeValue = escapeHtml(valueText || "none");
        return `
          <span class="pill intent-pill intent-meta-chip">
            <span class="intent-chip-key">${{safeLabel}}</span>
            <span class="intent-chip-sep">·</span>
            <span class="intent-chip-value">${{safeValue}}</span>
          </span>
        `;
      }}

      function renderIntentSummaryBlocks(rows) {{
        const safeRows = Array.isArray(rows) ? rows : [];
        if (safeRows.length === 0) return "";
        return `
          <span class="intent-meta-blocks">
            ${{
              safeRows.map((row) => `
                <span class="intent-meta-row">
                  ${{renderIntentMetaChip(row.label || "-", row.valueText || "none")}}
                </span>
              `).join("")
            }}
          </span>
        `;
      }}

      function renderIntentCards(intents) {{
        if (!Array.isArray(intents) || intents.length === 0) {{
          return '<div class="inline-empty">No intents in this list.</div>';
        }}
        return `
          <div class="call-list">
            ${{
              intents.map((item) => `
                <div class="call-card">
                  <div class="call-head">
                    <div class="call-name">idx ${{escapeHtml(item.idx ?? "?")}}</div>
                    <div class="call-id">${{escapeHtml(item.style || "")}}</div>
                  </div>
                  <pre>${{escapeHtml(item.content || "")}}</pre>
                </div>
              `).join("")
            }}
          </div>
        `;
      }}

      function renderIntentSatisfaction(phase) {{
        const payload = phase || {{}};
        if (!payload.executed) {{
          return renderFold(
            "Intent Satisfaction",
            "Not executed",
            `<div class="inline-empty">${{escapeHtml(payload.reason || "Not executed")}}</div>`,
            "step-fold"
          );
        }}
        const newlyInferred = normalizeIndexes(payload.newly_inferred_indexes);
        const notProvided = normalizeIndexes(payload.not_provided_indexes);
        const provided = normalizeIndexes(payload.provided_indexes);
        const details = payload.details || {{}};
        const meta = renderIntentSummaryBlocks([
          {{ label: "newly_inferred", valueText: renderIndexListText(newlyInferred) }},
          {{ label: "not_provided", valueText: renderIndexListText(notProvided) }},
          {{ label: "provided", valueText: renderIndexListText(provided) }},
        ]);
        const content = `
          <div class="step-list">
            ${{renderFold("newly_inferred intents", `${{(details.newly_inferred || []).length}} intents`, renderIntentCards(details.newly_inferred || []), "step-fold")}}
            ${{renderFold("not_provided intents", `${{(details.not_provided || []).length}} intents`, renderIntentCards(details.not_provided || []), "step-fold")}}
            ${{renderFold("provided intents", `${{(details.provided || []).length}} intents`, renderIntentCards(details.provided || []), "step-fold")}}
          </div>
        `;
        return renderFold("Intent Satisfaction", meta, content, "step-fold", false, true);
      }}

      function renderTargetedFollowup(phase) {{
        const payload = phase || {{}};
        if (!payload.executed) {{
          return renderFold(
            "Targeted Followup",
            "Not executed",
            `<div class="inline-empty">${{escapeHtml(payload.reason || "Not executed")}}</div>`,
            "step-fold"
          );
        }}
        const matched = normalizeIndexes(payload.matched_indexes);
        const summary = payload.summary || {{}};
        const total = Number(summary.total_candidates || 0);
        const meta = renderIntentSummaryBlocks([
          {{ label: "matched_indexes", valueText: renderIndexListText(matched) }},
          {{ label: "total_candidates", valueText: renderNumberText(total) }},
        ]);
        const content = `
          <div class="step-list">
            ${{renderFold("matched intents", `${{(payload.matched_intents || []).length}} intents`, renderIntentCards(payload.matched_intents || []), "step-fold")}}
          </div>
        `;
        return renderFold("Targeted Followup", meta, content, "step-fold", false, true);
      }}

      function renderNewlyProvided(phase) {{
        const payload = phase || {{}};
        if (!payload.executed) {{
          return renderFold(
            "Newly Provided",
            "Not executed",
            `<div class="inline-empty">${{escapeHtml(payload.reason || "Not executed")}}</div>`,
            "step-fold"
          );
        }}
        const updated = normalizeIndexes(payload.updated_indexes);
        const meta = renderIntentSummaryBlocks([
          {{ label: "updated_indexes", valueText: renderIndexListText(updated) }},
        ]);
        const content = `
          <div class="step-list">
            ${{renderFold("updated intents", `${{(payload.intents || []).length}} intents`, renderIntentCards(payload.intents || []), "step-fold")}}
          </div>
        `;
        return renderFold("Newly Provided", meta, content, "step-fold", false, true);
      }}

      function renderIntentProcess(intentProcess) {{
        const payload = intentProcess || {{}};
        const content = `
          <div class="step-list">
            ${{renderIntentSatisfaction(payload.intent_satisfaction)}}
            ${{renderTargetedFollowup(payload.targeted_followup)}}
            ${{renderNewlyProvided(payload.newly_provided)}}
          </div>
        `;
        return renderFold("Intent Process", "3 phases", content);
      }}

      function renderTurns(session) {{
        if (!session || session.turns.length === 0) {{
          turnsRoot.innerHTML = '<div class="empty">当前 session 没有 turn。</div>';
          return;
        }}

        turnsRoot.innerHTML = session.turns.map((turn) => {{
          const data = turn.data || {{}};
          const meta = turn.meta || {{}};
          return `
            <article class="turn-card">
              <div class="turn-head">
                <div>
                  <h3 class="turn-name">${{escapeHtml(turn.name)}}</h3>
                  <div class="turn-path">${{escapeHtml(turn.rel_path)}}</div>
                </div>
                <div class="task-meta">
                  <span class="pill">${{formatTime(turn.mtime)}}</span>
                  <span class="pill">${{escapeHtml(meta.llm_steps || 0)}} LLM</span>
                  <span class="pill">${{escapeHtml(meta.tool_steps || 0)}} tools</span>
                </div>
              </div>
              <div class="turn-stack">
                ${{renderFold("Input", `${{(data.input || "").length}} chars`, `<pre>${{escapeHtml(data.input || "")}}</pre>`, "", true)}}
                ${{renderFold("Output", `${{(data.output || "").length}} chars`, `<pre>${{escapeHtml(data.output || "")}}</pre>`)}}
                ${{renderSteps(data.llm_steps, data.tool_steps)}}
                ${{renderIntentProcess(turn.intent_process)}}
                ${{renderTurnChecklistEvaluation(turn.checklist_evaluation)}}
              </div>
            </article>
          `;
        }}).join("");
      }}

      function render() {{
        renderUserEvaluation();
        renderTasks();
        const task = findTask(state.taskId);
        if (!task) {{
          taskTitle.textContent = "暂无 task";
          taskNote.textContent = "未找到 trace turns。";
          taskEvalRoot.innerHTML = "";
          sessionStrip.innerHTML = "";
          turnsRoot.innerHTML = '<div class="empty">暂无 trace 日志</div>';
          return;
        }}

        if (!findSession(task, state.sessionId) && task.sessions[0]) {{
          state.sessionId = task.sessions[0].sessionId;
        }}

        const session = findSession(task, state.sessionId);
        taskTitle.textContent = task.taskId;
        taskNote.textContent = `${{task.sessionCount}} sessions · ${{task.turnCount}} turns · latest ${{formatTime(task.latest)}}`;
        taskEvalRoot.innerHTML = renderTaskEvaluation(task);
        renderSessions(task);
        renderTurns(session);
      }}

      render();
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Trace log 可视化：按 model_id / user_id 聚合生成 HTML，支持 task 与 session 两级切换。"
    )
    parser.add_argument("--logs-dir", type=Path, default=LOGS_DIR, help="日志目录")
    parser.add_argument("-o", "--output", type=Path, default=None, help="输出目录")
    parser.add_argument("--output-file", type=Path, default=None, help="直接指定输出 HTML 路径")
    parser.add_argument(
        "--open-model-id",
        type=str,
        default=None,
        help="自动打开指定 model_id 的首个 HTML",
    )
    parser.add_argument(
        "--default-model-id",
        type=str,
        default=None,
        help="当日志布局不包含 model_id 时使用",
    )
    parser.add_argument(
        "--default-user-id",
        type=str,
        default=None,
        help="当日志布局不包含 user_id 时使用",
    )
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--quiet", action="store_true", help="不打印生成结果")
    args = parser.parse_args()

    scanned = scan_logs(
        args.logs_dir,
        default_model_id=args.default_model_id,
        default_user_id=args.default_user_id,
    )
    if not scanned:
        if not args.quiet:
            print("未找到 turn_*.json，目录:", args.logs_dir)
        return

    pages: list[tuple[str, str, Path]] = []
    for model_id in sorted(scanned):
        for user_id in sorted(scanned[model_id]):
            pages.append((model_id, user_id, Path()))

    if args.output_file is not None and len(pages) != 1:
        raise ValueError("--output-file only supports generating exactly one model/user page")

    output_dir = args.output or args.logs_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[tuple[str, str, Path]] = []
    for model_id, user_id, _ in pages:
        html = build_html(
            model_id,
            user_id,
            scanned[model_id][user_id],
            logs_dir=args.logs_dir,
        )
        out_path = args.output_file or (output_dir / f"{model_id}-{user_id}.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        generated.append((model_id, user_id, out_path))
        if not args.quiet:
            print(
                "已生成:",
                out_path,
                "| model:",
                model_id,
                "| user:",
                user_id,
                "| tasks:",
                len(scanned[model_id][user_id]),
            )

    if not args.no_open and generated:
        target = generated[0][2]
        if args.open_model_id:
            for model_id, _, out_path in generated:
                if model_id == args.open_model_id:
                    target = out_path
                    break
        webbrowser.open(f"file://{target.resolve()}")


if __name__ == "__main__":
    main()
