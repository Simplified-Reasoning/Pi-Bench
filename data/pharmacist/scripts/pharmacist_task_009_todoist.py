from __future__ import annotations

from typing import Any


CHECKLIST_LOGIN = "uses Todoist login flow and reuses returned access token"
CHECKLIST_PROJECT = "creates a new project before section or task creation"
CHECKLIST_SECTION = "creates a Follow-up section inside the new project"
CHECKLIST_HIERARCHY = "creates a parent task and then a sub task in the proper hierarchy"
CHECKLIST_VERIFY = "executes both show_sections and show_sub_tasks after writes"


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_LOGIN: 0,
        CHECKLIST_PROJECT: 0,
        CHECKLIST_SECTION: 0,
        CHECKLIST_HIERARCHY: 0,
        CHECKLIST_VERIFY: 0,
    }


def _tool_matches(name: str, expected: str) -> bool:
    return name == expected or name == f"mcp_appworld_{expected}"


def _response_block(item: dict[str, Any]) -> dict[str, Any]:
    result = item.get("result")
    if isinstance(result, dict):
        response = result.get("response")
        if isinstance(response, dict):
            return response
    return {}


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    scores = _default_scores()
    if not isinstance(tools_history, list) or not tools_history:
        return scores

    login_token: Any = None
    project_id: Any = None
    task_id: Any = None
    section_ok = False
    sub_task_ok = False
    showed_sections = False
    showed_sub_tasks = False

    for item in tools_history:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("tool_name") or "").strip()
        call = item.get("call")
        call = call if isinstance(call, dict) else {}
        response = _response_block(item)

        if _tool_matches(tool_name, "todoist__login"):
            login_token = response.get("access_token")
            if login_token:
                scores[CHECKLIST_LOGIN] = 1

        elif _tool_matches(tool_name, "todoist__create_project"):
            if not login_token or call.get("access_token") == login_token:
                project_id = response.get("project_id")
                if project_id is not None:
                    scores[CHECKLIST_PROJECT] = 1

        elif _tool_matches(tool_name, "todoist__create_section"):
            if project_id is not None and call.get("project_id") == project_id:
                name = str(call.get("name") or "")
                if "follow-up" in name.lower() or "follow up" in name.lower():
                    section_ok = True

        elif _tool_matches(tool_name, "todoist__create_task"):
            if project_id is not None and call.get("project_id") == project_id:
                task_id = response.get("task_id")

        elif _tool_matches(tool_name, "todoist__create_sub_task"):
            if task_id is not None and call.get("task_id") == task_id:
                sub_task_ok = True

        elif _tool_matches(tool_name, "todoist__show_sections"):
            if project_id is not None and call.get("project_id") == project_id:
                showed_sections = True

        elif _tool_matches(tool_name, "todoist__show_sub_tasks"):
            if task_id is not None and call.get("task_id") == task_id:
                showed_sub_tasks = True

    if section_ok:
        scores[CHECKLIST_SECTION] = 1
    if task_id is not None and sub_task_ok:
        scores[CHECKLIST_HIERARCHY] = 1
    if showed_sections and showed_sub_tasks:
        scores[CHECKLIST_VERIFY] = 1
    return scores
