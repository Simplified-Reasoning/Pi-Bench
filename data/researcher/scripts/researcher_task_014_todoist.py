from __future__ import annotations

import json
import re
from typing import Any


EXPECTED_FINAL_TIMES = {
    "Morning stretching": "Friday 07:30-08:00",
    "Make breakfast": "Friday 08:30-09:00",
    "Receive a package": "Friday 09:00-09:30",
    "Organize this week's weekly report": "Friday 09:30-10:15",
    "Project sync meeting": "Friday 10:30-11:30",
    "Client requirements call": "Friday 11:30-12:15",
    "Lunch": "Friday 12:15-13:00",
    "Submit reimbursement materials": "Friday 13:00-13:30",
    "Read a related paper": "Friday 13:45-14:30",
    "Reply to important emails": "Friday 14:30-14:50",
    "Code review": "Friday 15:00-16:00",
    "Team meeting rehearsal": "Friday 16:00-16:40",
    "Record expenses": "Friday 16:40-17:00",
    "Buy daily necessities": "Friday 17:00-17:40",
    "Organize the desk and files": "Friday 17:45-18:15",
}

STALE_OLD_TIMES = {
    "Receive a package": "Friday 08:45-09:15",
    "Client requirements call": "Friday 11:00-12:00",
    "Team meeting rehearsal": "Friday 15:30-16:30",
}

CHECKLIST_CREATED_ALL_15 = "all 15 tasks were created"
CHECKLIST_TITLES_HAVE_NO_TIMESTAMPS = "task titles do not contain timestamps"


def _final_time_key(title: str, expected_time: str) -> str:
    return f'final time correct for "{title}" -> {expected_time}'


def _old_removed_key(title: str, old_time: str) -> str:
    return f'old conflicting time removed for "{title}" -> {old_time}'


def _default_scores() -> dict[str, int]:
    scores = {
        CHECKLIST_CREATED_ALL_15: 0,
        CHECKLIST_TITLES_HAVE_NO_TIMESTAMPS: 0,
    }

    for title, expected_time in EXPECTED_FINAL_TIMES.items():
        scores[_final_time_key(title, expected_time)] = 0

    for title, old_time in STALE_OLD_TIMES.items():
        scores[_old_removed_key(title, old_time)] = 0

    return scores


def _tool_name_matches(tool_name: str, suffix: str) -> bool:
    tool_name = (tool_name or "").strip().lower()
    suffix = suffix.lower()
    return tool_name == suffix or tool_name.endswith(suffix)


def _canonical_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _extract_title(call_payload: dict[str, Any]) -> str:
    for key in ("title", "content", "name"):
        value = call_payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_description(call_payload: dict[str, Any]) -> str:
    value = call_payload.get("description")
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _normalize_task_id(task_id: Any) -> str | None:
    if task_id is None or isinstance(task_id, bool):
        return None
    if isinstance(task_id, str):
        normalized = task_id.strip()
        return normalized or None
    if isinstance(task_id, float) and task_id.is_integer():
        return str(int(task_id))
    return str(task_id)


def _extract_task_id_from_call(call_payload: dict[str, Any]) -> str | None:
    for key in ("task_id", "id"):
        task_id = _normalize_task_id(call_payload.get(key))
        if task_id is not None:
            return task_id
    return None


def _extract_task_id(result_payload: Any) -> Any:
    result_payload = _safe_dict(result_payload)
    response = result_payload.get("response")
    if not isinstance(response, dict):
        return None
    return _normalize_task_id(response.get("task_id"))


def _extract_show_tasks(result_payload: Any) -> list[dict[str, Any]]:
    result_payload = _safe_dict(result_payload)
    response = result_payload.get("response")
    if not isinstance(response, dict):
        return []

    tasks: list[dict[str, Any]] = []

    no_section_tasks = response.get("no_section_tasks")
    if isinstance(no_section_tasks, list):
        tasks.extend(item for item in no_section_tasks if isinstance(item, dict))

    sections = response.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_tasks = section.get("tasks")
            if isinstance(section_tasks, list):
                tasks.extend(item for item in section_tasks if isinstance(item, dict))

    return tasks


def _record_task(
    tasks_by_id: dict[str, dict[str, str]],
    title_to_ids: dict[str, list[str]],
    task_id: str,
    title: str,
    description: str,
) -> None:
    tasks_by_id[task_id] = {
        "title": title,
        "description": description,
    }
    norm_title = _canonical_text(title)
    ids = title_to_ids.setdefault(norm_title, [])
    if task_id not in ids:
        ids.append(task_id)


def _title_has_timestamp(raw_title: str) -> bool:
    pattern = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}",
        re.IGNORECASE,
    )
    return pattern.search(raw_title or "") is not None


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = _default_scores()

    if not isinstance(tools_history, list) or not tools_history:
        return result

    # task_id -> final state
    tasks_by_id: dict[str, dict[str, str]] = {}
    # normalized title -> task_ids
    title_to_ids: dict[str, list[str]] = {}

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or item.get("name") or "")
        call_payload = _safe_dict(item.get("call"))
        if not call_payload:
            call_payload = _safe_dict(item.get("arguments"))
        result_payload = _safe_dict(item.get("result"))

        # 1) create_task: 建立初始任务状态
        if _tool_name_matches(tool_name, "todoist__create_task"):
            task_id = _extract_task_id(result_payload)
            title = _extract_title(call_payload)
            description = _extract_description(call_payload)

            if task_id is None or not title:
                continue

            _record_task(tasks_by_id, title_to_ids, task_id, title, description)

        # 2) show_tasks: 用当前 Todoist 状态恢复全量任务
        elif _tool_name_matches(tool_name, "todoist__show_tasks"):
            for shown_task in _extract_show_tasks(result_payload):
                task_id = _extract_task_id_from_call(shown_task)
                title = _extract_title(shown_task)
                description = _extract_description(shown_task)
                if task_id is None or not title:
                    continue
                _record_task(tasks_by_id, title_to_ids, task_id, title, description)

        # 3) update_task: 覆盖 description
        elif _tool_name_matches(tool_name, "todoist__update_task"):
            task_id = _extract_task_id_from_call(call_payload)
            if task_id is None:
                continue
            if task_id not in tasks_by_id:
                continue

            if isinstance(call_payload.get("description"), str):
                tasks_by_id[task_id]["description"] = _extract_description(call_payload)

    # 按 title 聚合最终 description
    final_descriptions_by_title: dict[str, list[str]] = {}
    raw_titles_by_title: dict[str, list[str]] = {}

    for title in EXPECTED_FINAL_TIMES:
        norm_title = _canonical_text(title)
        ids = title_to_ids.get(norm_title, [])
        descriptions = []
        raw_titles = []

        for task_id in ids:
            task = tasks_by_id.get(task_id)
            if not task:
                continue
            descriptions.append(task.get("description", ""))
            raw_titles.append(task.get("title", ""))

        if descriptions:
            final_descriptions_by_title[title] = descriptions
            raw_titles_by_title[title] = raw_titles

    # 1) 15 个任务都创建了
    if len(final_descriptions_by_title) == len(EXPECTED_FINAL_TIMES):
        result[CHECKLIST_CREATED_ALL_15] = 1

    # 2) title 不包含时间戳
    titles_clean = True
    for raw_titles in raw_titles_by_title.values():
        for raw_title in raw_titles:
            if _title_has_timestamp(raw_title):
                titles_clean = False
                break
        if not titles_clean:
            break
    if titles_clean and result[CHECKLIST_CREATED_ALL_15] == 1:
        result[CHECKLIST_TITLES_HAVE_NO_TIMESTAMPS] = 1

    # 3) 逐条检查最终时间
    for title, expected_time in EXPECTED_FINAL_TIMES.items():
        descriptions = final_descriptions_by_title.get(title, [])
        if any(expected_time in desc for desc in descriptions):
            result[_final_time_key(title, expected_time)] = 1

    # 4) 检查旧冲突时间是否消失
    for title, old_time in STALE_OLD_TIMES.items():
        descriptions = final_descriptions_by_title.get(title, [])
        if descriptions and not any(old_time in desc for desc in descriptions):
            result[_old_removed_key(title, old_time)] = 1

    return result
