from __future__ import annotations

from typing import Any


CHECKS = {
    "project_created": 0,
    "tracking_item_created": 0,
    "tracking_item_covers_required_items": 0,
    "tracking_item_mentions_main_blocker_and_escalation": 0,
    "todoist_cleanup_completed": 0,
    "completion_email_sent_to_internal_recipient": 0,
    "completion_email_subject_matches": 0,
    "completion_email_confirms_cleanup": 0,
    "completion_email_mentions_live_risk": 0,
    "completion_email_mentions_tomorrow_morning_checkpoint": 0,
    "completion_email_requests_delay_flag": 0,
}

PROJECT_NAME = "Temporary Filing Follow-up Board - Yuehai"
INTERNAL_RECIPIENT = "la-mcco@gmail.com"
EMAIL_SUBJECT = "Yuehai Guarantee Dispute - Filing Rehearsal Cleanup Complete"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _response(item: dict[str, Any]) -> dict[str, Any]:
    result = item.get("result")
    if not isinstance(result, dict):
        return {}
    response = result.get("response")
    return response if isinstance(response, dict) else {}


def _to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value]
    if isinstance(value, str):
        return [value.strip().lower()]
    return []


def _contains_required_items(text: str) -> bool:
    lowered = text.lower()
    return (
        "unsigned shareholder list" in lowered
        and "signed guaranty annex comparison" in lowered
        and "courier receipt" in lowered
        and "supplemental filing package" in lowered
    )


def _contains_blocker_and_escalation(text: str) -> bool:
    lowered = text.lower()
    return (
        "unsigned shareholder list" in lowered
        and any(token in lowered for token in ("main blocker", "primary blocker", "live blocker"))
        and "partner" in lowered
        and "escalat" in lowered
        and any(token in lowered for token in ("tomorrow's internal check-in", "tomorrow internal check-in", "internal check-in"))
    )


def _contains_cleanup_confirmation(text: str) -> bool:
    lowered = text.lower()
    return (
        any(token in lowered for token in ("temporary todoist board", "temporary board", "temporary filing follow-up board"))
        and any(token in lowered for token in ("cleared", "removed", "deleted"))
    )


def _contains_live_risk(text: str) -> bool:
    lowered = text.lower()
    return (
        "unsigned shareholder list" in lowered
        and any(token in lowered for token in ("live risk", "main risk", "remaining risk"))
    )


def _contains_tomorrow_morning_checkpoint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("tomorrow morning", "next checkpoint", "checkpoint"))


def _contains_delay_flag(text: str) -> bool:
    lowered = text.lower()
    return "flag" in lowered and any(token in lowered for token in ("delay", "timing risk", "slip"))


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    project_id = None
    delete_project = None
    tracking_contents: list[str] = []
    email_subjects: list[str] = []
    email_bodies: list[str] = []
    draft_ids_created: set[Any] = set()
    draft_ids_sent: set[Any] = set()

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        tool_name = _norm(str(item.get("tool_name") or ""))
        call = item.get("call") or {}
        if not isinstance(call, dict):
            call = {}
        response = _response(item)

        if tool_name == "todoist__create_project":
            if _text(call.get("name")) == PROJECT_NAME:
                result["project_created"] = 1
                project_id = response.get("project_id", project_id)
        elif tool_name == "todoist__create_task":
            if call.get("project_id") == project_id:
                result["tracking_item_created"] = 1
                tracking_contents.append(f"{_text(call.get('title'))}\n{_text(call.get('description'))}")
        elif tool_name == "todoist__delete_project":
            delete_project = item
        elif tool_name == "gmail__send_email":
            recipients = _to_list(call.get("email_addresses"))
            if INTERNAL_RECIPIENT in recipients:
                result["completion_email_sent_to_internal_recipient"] = 1
            email_subjects.append(_text(call.get("subject")))
            email_bodies.append(_text(call.get("body")))
        elif tool_name == "gmail__create_draft":
            recipients = _to_list(call.get("recipient_email_addresses"))
            if INTERNAL_RECIPIENT in recipients:
                result["completion_email_sent_to_internal_recipient"] = 1
            email_bodies.append(_text(call.get("body")))
            draft_id = response.get("draft_id")
            if draft_id is not None:
                draft_ids_created.add(draft_id)
        elif tool_name == "gmail__send_email_from_draft":
            draft_id = call.get("draft_id")
            if draft_id is not None:
                draft_ids_sent.add(draft_id)
            if response.get("sent_email_id") is not None:
                result["completion_email_sent_to_internal_recipient"] = 1

    combined_tracking = "\n".join(tracking_contents)
    combined_email_body = "\n".join(email_bodies)
    combined_evidence = f"{combined_tracking}\n{combined_email_body}"
    if _contains_required_items(combined_evidence):
        result["tracking_item_covers_required_items"] = 1
    if _contains_blocker_and_escalation(combined_evidence):
        result["tracking_item_mentions_main_blocker_and_escalation"] = 1

    if isinstance(delete_project, dict) and (delete_project.get("call") or {}).get("project_id") == project_id:
        result["todoist_cleanup_completed"] = 1

    if EMAIL_SUBJECT in email_subjects:
        result["completion_email_subject_matches"] = 1
    if _contains_cleanup_confirmation(combined_email_body):
        result["completion_email_confirms_cleanup"] = 1
    if _contains_live_risk(combined_email_body):
        result["completion_email_mentions_live_risk"] = 1
    if _contains_tomorrow_morning_checkpoint(combined_email_body):
        result["completion_email_mentions_tomorrow_morning_checkpoint"] = 1
    if _contains_delay_flag(combined_email_body):
        result["completion_email_requests_delay_flag"] = 1

    if draft_ids_created and draft_ids_sent.isdisjoint(draft_ids_created):
        result["completion_email_sent_to_internal_recipient"] = 0

    return result
