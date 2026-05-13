from __future__ import annotations

from typing import Any


CHECKS = {
    "sms_sent_to_correct_number": 0,
    "sms_mentions_matter": 0,
    "sms_mentions_handover_slot": 0,
    "sms_lists_required_materials": 0,
    "sms_requests_reply_deadline": 0,
    "sms_requests_risk_flag": 0,
    "sms_is_scan_friendly": 0,
    "todoist_temp_project_created": 0,
    "todoist_cleanup_completed": 0,
}

PROJECT_NAME = "Temporary Court Handover Reminder Board"
CONTACT_NUMBER = "2873148336"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _contains_handover_slot(text: str) -> bool:
    lowered = text.lower()
    return "11:30" in lowered and "east gate of jiangzhou intermediate people's court" in lowered


def _contains_matter_reference(text: str) -> bool:
    lowered = text.lower()
    return "yuehai" in lowered and any(token in lowered for token in ("handover", "packet", "court-side"))


def _contains_required_materials(text: str) -> bool:
    lowered = text.lower()
    return all(
        phrase in lowered
        for phrase in (
            "original notarized power of attorney",
            "two stamped copies of the evidence list",
            "one copy of the hearing notice",
        )
    )


def _contains_reply_deadline(text: str) -> bool:
    lowered = text.lower()
    return "before 8:00 p.m. today" in lowered or "before 8pm today" in lowered or "8:00 p.m. today" in lowered


def _contains_risk_flag(text: str) -> bool:
    lowered = text.lower()
    has_not_ready = any(token in lowered for token in ("not ready", "document", "materials"))
    has_change = any(token in lowered for token in ("location needs to change", "time or location", "pickup time", "pickup point"))
    has_flag = "flag" in lowered
    return has_flag and has_not_ready and has_change


def _is_scan_friendly(text: str) -> bool:
    if any(token in text for token in ("\n", "1.", "2.", "3.", ";")):
        return True
    lowered = text.lower()
    return lowered.count(". ") >= 2


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    sms_messages: list[str] = []
    create_project = None
    create_tasks: list[dict[str, Any]] = []
    delete_project = None
    created_project_id = None

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        if name == "phone__send_text_message":
            call = item.get("call") or {}
            if _text(call.get("phone_number")) == CONTACT_NUMBER:
                result["sms_sent_to_correct_number"] = 1
                sms_messages.append(_text(call.get("message")))
        elif name == "todoist__create_project":
            create_project = item
            created_project_id = ((item.get("result") or {}).get("response") or {}).get("project_id")
        elif name == "todoist__create_task":
            create_tasks.append(item)
        elif name == "todoist__delete_project":
            delete_project = item

    combined_sms = "\n".join(message for message in sms_messages if message)
    if _contains_matter_reference(combined_sms):
        result["sms_mentions_matter"] = 1
    if _contains_handover_slot(combined_sms):
        result["sms_mentions_handover_slot"] = 1
    if _contains_required_materials(combined_sms):
        result["sms_lists_required_materials"] = 1
    if _contains_reply_deadline(combined_sms):
        result["sms_requests_reply_deadline"] = 1
    if _contains_risk_flag(combined_sms):
        result["sms_requests_risk_flag"] = 1
    for message in sms_messages:
        if (
            _contains_handover_slot(message)
            and _contains_required_materials(message)
            and _contains_reply_deadline(message)
            and _contains_risk_flag(message)
            and _is_scan_friendly(message)
        ):
            result["sms_is_scan_friendly"] = 1
            break

    if isinstance(create_project, dict) and _text((create_project.get("call") or {}).get("name")) == PROJECT_NAME:
        result["todoist_temp_project_created"] = 1

    if isinstance(delete_project, dict) and (delete_project.get("call") or {}).get("project_id") == created_project_id:
        result["todoist_cleanup_completed"] = 1

    return result
