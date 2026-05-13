from __future__ import annotations

from typing import Any


CHECKS = {
    "email_sent": 0,
    "subject_matches_internal_review_queue": 0,
    "body_states_two_live_items": 0,
    "body_sets_deadline_and_blocker_flag": 0,
    "body_provides_courier_fallback": 0,
    "body_uses_separated_two_item_structure": 0,
    "triage_sequence_completed": 0,
    "todoist_reminder_has_checkpoint_and_cleanup": 0,
}

LABEL_NAME = "needs-supervisor-review"
SUBJECT = "Internal Follow-up | Xinhe Supply Chain Arbitration | Supervisor Review Queue"


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


def _recipient_list(call: dict[str, Any]) -> list[str]:
    raw = call.get("email_addresses")
    if raw is None:
        raw = call.get("recipient_email_addresses")
    if isinstance(raw, list):
        return [str(item).strip().lower() for item in raw]
    if isinstance(raw, str):
        return [raw.strip().lower()]
    return []


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _contains_two_item_statement(text: str) -> bool:
    return (
        ("xinhe supply chain arbitration" in text or "xinhe supervisor review queue" in text)
        and _contains_any(text, ("two live items", "two pending items", "two open items"))
        and "arbitration-clause scan" in text
        and "courier receipt" in text
    )


def _contains_deadline_and_flag(text: str) -> bool:
    has_deadline = _contains_any(text, ("4:00 p.m. tomorrow", "4:00 pm tomorrow", "4 pm tomorrow"))
    has_flag = "flag" in text and _contains_any(text, ("blocker", "timing risk", "delay", "slip"))
    return has_deadline and has_flag


def _contains_fallback(text: str) -> bool:
    return (
        "courier receipt" in text
        and _contains_any(text, ("waybill", "tracking screenshot", "tracking"))
        and _contains_any(text, ("expected arrival", "arrival timing", "eta", "expected delivery"))
    )


def _contains_separated_structure(body: str) -> bool:
    lines = [line.strip().lower() for line in body.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    has_arb = any("arbitration-clause scan" in line for line in lines)
    has_courier = any("courier receipt" in line for line in lines)
    has_separators = any(line.startswith(("1.", "1)", "2.", "2)", "-", "*")) for line in lines)
    return has_arb and has_courier and has_separators


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    label = None
    unread = None
    read = None
    create_task = None
    delete_task = None
    sent_thread_id = None
    created_task_id = None
    subject = ""
    body_parts: list[str] = []
    draft_ids_created: set[Any] = set()
    draft_ids_sent: set[Any] = set()

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        call = item.get("call") or {}
        if not isinstance(call, dict):
            call = {}
        if name == "gmail__send_email":
            result["email_sent"] = 1
            subject = _text(call.get("subject")) or subject
            body_parts.append(_text(call.get("body")))
            sent_thread_id = _response(item).get("sent_email_thread_id", sent_thread_id)
        elif name == "gmail__create_draft":
            if "la-mcco@gmail.com" in _recipient_list(call):
                result["email_sent"] = 1
            body_parts.append(_text(call.get("body")))
            thread_id = call.get("belongs_to_email_thread_id")
            if thread_id is not None:
                sent_thread_id = thread_id
            draft_id = _response(item).get("draft_id")
            if draft_id is not None:
                draft_ids_created.add(draft_id)
        elif name == "gmail__send_email_from_draft":
            draft_id = call.get("draft_id")
            if draft_id is not None:
                draft_ids_sent.add(draft_id)
            response = _response(item)
            if response.get("sent_email_id") is not None:
                result["email_sent"] = 1
            sent_thread_id = response.get("sent_email_thread_id", sent_thread_id)
        elif name == "gmail__label_thread":
            label = item
        elif name == "gmail__mark_thread_unread":
            unread = item
        elif name == "gmail__mark_thread_read":
            read = item
        elif name == "todoist__create_task":
            create_task = item
            created_task_id = ((item.get("result") or {}).get("response") or {}).get("task_id")
        elif name == "todoist__delete_task":
            delete_task = item

    body = "\n".join(body_parts)
    body_lower = body.lower()
    if subject == SUBJECT:
        result["subject_matches_internal_review_queue"] = 1
    if _contains_two_item_statement(body_lower):
        result["body_states_two_live_items"] = 1
    if _contains_deadline_and_flag(body_lower):
        result["body_sets_deadline_and_blocker_flag"] = 1
    if _contains_fallback(body_lower):
        result["body_provides_courier_fallback"] = 1
    if _contains_separated_structure(body):
        result["body_uses_separated_two_item_structure"] = 1

    if draft_ids_created and draft_ids_sent.isdisjoint(draft_ids_created):
        result["email_sent"] = 0

    if label and unread and read and sent_thread_id is not None:
        label_call = label.get("call") or {}
        unread_call = unread.get("call") or {}
        read_call = read.get("call") or {}
        if (
            _text(label_call.get("label")) == LABEL_NAME
            and label_call.get("email_thread_id") == sent_thread_id
            and unread_call.get("email_thread_id") == sent_thread_id
            and read_call.get("email_thread_id") == sent_thread_id
        ):
            result["triage_sequence_completed"] = 1

    if isinstance(create_task, dict) and delete_task:
        call = create_task.get("call") or {}
        content = f"{_text(call.get('title'))} {_text(call.get('description'))}".lower()
        has_checkpoint = "xinhe" in content and _contains_any(
            content, ("3:30 p.m. tomorrow", "3:30 pm tomorrow", "checkpoint", "follow-up checkpoint")
        )
        if has_checkpoint and (delete_task.get("call") or {}).get("task_id") == created_task_id:
            result["todoist_reminder_has_checkpoint_and_cleanup"] = 1

    return result
