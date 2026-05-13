from __future__ import annotations

from typing import Any


CHECKS = {
    "project_created": 0,
    "section_created": 0,
    "three_tasks_created": 0,
    "priority_task_assigned_to_self": 0,
    "priority_task_updated_with_checkpoint": 0,
    "label_created_and_bound": 0,
    "comment_posts_escalation_rule": 0,
    "comment_was_reviewed": 0,
    "full_cleanup_completed": 0,
}

PROJECT_NAME = "Temporary Launch Rehearsal Board - Beacon"
SECTION_NAME = "Tonight Rehearsal"
LABEL_NAME = "launch-blocker"
PRIORITY_TASK_TITLE = "Walk through Beacon share slides"
DEVICE_TASK_TITLE = "Check demo device charging and screen recording"
BADGE_TASK_TITLE = "Confirm guest badge pickup and sign-in sheet"
SELF_EMAIL = "stmcco@gmail.com"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    create_project = None
    create_section = None
    create_label = None
    create_tasks: list[dict[str, Any]] = []
    assign_calls: list[dict[str, Any]] = []
    update_calls: list[dict[str, Any]] = []
    add_label_calls: list[dict[str, Any]] = []
    post_comment_calls: list[dict[str, Any]] = []
    show_comment_calls: list[dict[str, Any]] = []
    remove_label_calls: list[dict[str, Any]] = []
    delete_comment_calls: list[dict[str, Any]] = []
    delete_task_calls: list[dict[str, Any]] = []
    delete_label = None
    delete_section = None
    delete_project = None

    login_email = SELF_EMAIL

    project_id = None
    section_id = None
    label_id = None
    created_task_ids: set[Any] = set()
    task_id_by_title: dict[str, Any] = {}

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        call = item.get("call") or {}
        result_payload = (item.get("result") or {}).get("response") or {}
        if name == "todoist__login":
            username = _text(call.get("username"))
            if username:
                login_email = username
        elif name == "todoist__create_project":
            create_project = item
            project_id = result_payload.get("project_id")
        elif name == "todoist__create_section":
            create_section = item
            section_id = result_payload.get("section_id")
        elif name == "todoist__create_label":
            create_label = item
            label_id = result_payload.get("label_id")
        elif name == "todoist__create_task":
            create_tasks.append(item)
            task_id = result_payload.get("task_id")
            title = _text(call.get("title"))
            if task_id is not None:
                created_task_ids.add(task_id)
            if title and task_id is not None:
                task_id_by_title[title] = task_id
        elif name == "todoist__assign_or_unassign_task":
            assign_calls.append(item)
        elif name == "todoist__update_task":
            update_calls.append(item)
        elif name == "todoist__add_label_to_task":
            add_label_calls.append(item)
        elif name == "todoist__post_task_comment":
            post_comment_calls.append(item)
        elif name == "todoist__show_task_comments":
            show_comment_calls.append(item)
        elif name == "todoist__remove_label_from_task":
            remove_label_calls.append(item)
        elif name == "todoist__delete_task_comment":
            delete_comment_calls.append(item)
        elif name == "todoist__delete_task":
            delete_task_calls.append(item)
        elif name == "todoist__delete_label":
            delete_label = item
        elif name == "todoist__delete_section":
            delete_section = item
        elif name == "todoist__delete_project":
            delete_project = item

    if isinstance(create_project, dict) and _text((create_project.get("call") or {}).get("name")) == PROJECT_NAME:
        result["project_created"] = 1

    if (
        isinstance(create_section, dict)
        and _text((create_section.get("call") or {}).get("name")) == SECTION_NAME
        and (create_section.get("call") or {}).get("project_id") == project_id
    ):
        result["section_created"] = 1

    matched_titles: set[str] = set()
    for item in create_tasks:
        call = item.get("call") or {}
        title = _text(call.get("title"))
        description = _text(call.get("description"))
        lowered = description.lower()
        if call.get("project_id") != project_id or call.get("section_id") != section_id:
            continue
        if title == PRIORITY_TASK_TITLE and "slides" in lowered:
            matched_titles.add(title)
        elif title == DEVICE_TASK_TITLE and "charging" in lowered and "record" in lowered:
            matched_titles.add(title)
        elif title == BADGE_TASK_TITLE and "badge" in lowered and "sign-in" in lowered:
            matched_titles.add(title)
    if matched_titles == {PRIORITY_TASK_TITLE, DEVICE_TASK_TITLE, BADGE_TASK_TITLE}:
        result["three_tasks_created"] = 1

    priority_task_id = task_id_by_title.get(PRIORITY_TASK_TITLE)
    for item in assign_calls:
        call = item.get("call") or {}
        if call.get("task_id") == priority_task_id and _text(call.get("assignee_email")) == login_email:
            result["priority_task_assigned_to_self"] = 1
            break

    for item in update_calls:
        call = item.get("call") or {}
        description = _text(call.get("description"))
        if call.get("task_id") == priority_task_id and "2026-04-29 17:45" in description and "2026-04-29 18:30" in description:
            result["priority_task_updated_with_checkpoint"] = 1
            break

    for item in add_label_calls:
        call = item.get("call") or {}
        if call.get("task_id") == priority_task_id and call.get("label_id") == label_id and isinstance(create_label, dict):
            if _text((create_label.get("call") or {}).get("name")) == LABEL_NAME:
                result["label_created_and_bound"] = 1
                break

    comment_id = None
    for item in post_comment_calls:
        call = item.get("call") or {}
        content = _text(call.get("content"))
        comment_id = (((item.get("result") or {}).get("response") or {}).get("task_comment_id"))
        lowered = content.lower()
        if call.get("task_id") == priority_task_id and "2026-04-29 18:30" in content and "organizer" in lowered:
            result["comment_posts_escalation_rule"] = 1
            break

    for item in show_comment_calls:
        call = item.get("call") or {}
        if call.get("task_id") == priority_task_id:
            result["comment_was_reviewed"] = 1
            break

    removed_label_ok = False
    if priority_task_id is not None and label_id is not None:
        for item in remove_label_calls:
            call = item.get("call") or {}
            if call.get("task_id") == priority_task_id and call.get("label_id") == label_id:
                removed_label_ok = True
                break

    deleted_task_ids = {
        (item.get("call") or {}).get("task_id")
        for item in delete_task_calls
        if isinstance(item, dict)
    }
    deleted_comment_ok = False
    if comment_id is not None:
        for item in delete_comment_calls:
            if (item.get("call") or {}).get("task_comment_id") == comment_id:
                deleted_comment_ok = True
                break

    if (
        created_task_ids
        and deleted_task_ids == created_task_ids
        and removed_label_ok
        and deleted_comment_ok
        and isinstance(delete_label, dict)
        and (delete_label.get("call") or {}).get("label_id") == label_id
        and isinstance(delete_section, dict)
        and (delete_section.get("call") or {}).get("section_id") == section_id
        and isinstance(delete_project, dict)
        and (delete_project.get("call") or {}).get("project_id") == project_id
    ):
        result["full_cleanup_completed"] = 1

    return result
