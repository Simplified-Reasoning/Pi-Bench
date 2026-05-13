from __future__ import annotations

from typing import Any


CHECKS = {
    "gmail_draft_workflow_completed": 0,
    "sent_to_real_recipient": 0,
    "subject_exact_match": 0,
    "body_is_matter_specific": 0,
    "body_covers_three_confirmation_items": 0,
    "body_sets_deadline": 0,
    "body_mentions_badge_fallback": 0,
    "body_requests_immediate_risk_flag": 0,
    "body_uses_scan_friendly_structure": 0,
    "outbox_and_thread_verified": 0,
}

SUBJECT = "Pre-Event Confirmation | Nanshan Client Product Demo | Wednesday Setup"
RECIPIENT = "la-mcco@gmail.com"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _id_text(value: Any) -> str:
    return str(value) if isinstance(value, (int, str)) else ""


def _count_numbered_items(body: str) -> int:
    count = 0
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if len(line) > 2 and line[0].isdigit() and line[1] in {".", ")"}:
            count += 1
    return count


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)
    create_draft = None
    update_draft = None
    send_from_draft = None
    show_outbox = None
    show_thread = None

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        if name == "gmail__create_draft":
            create_draft = item
        elif name == "gmail__update_draft":
            update_draft = item
        elif name == "gmail__send_email_from_draft":
            send_from_draft = item
        elif name == "gmail__show_outbox_threads":
            show_outbox = item
        elif name == "gmail__show_thread":
            show_thread = item

    draft_id = _id_text((((create_draft or {}).get("result") or {}).get("response") or {}).get("draft_id"))
    updated_draft_id = _id_text(((update_draft or {}).get("call") or {}).get("draft_id"))
    sent_draft_id = _id_text(((send_from_draft or {}).get("call") or {}).get("draft_id"))
    if create_draft and update_draft and send_from_draft:
        if draft_id and draft_id == updated_draft_id == sent_draft_id:
            result["gmail_draft_workflow_completed"] = 1
        elif updated_draft_id and updated_draft_id == sent_draft_id:
            result["gmail_draft_workflow_completed"] = 1

    final_subject = ""
    final_body = ""
    final_recipients: list[str] = []
    if isinstance(update_draft, dict):
        call = update_draft.get("call") or {}
        final_subject = _text(call.get("subject"))
        final_body = _text(call.get("body"))
        emails = call.get("email_addresses") or []
        if isinstance(emails, list):
            final_recipients = [str(email) for email in emails]
    elif isinstance(create_draft, dict):
        call = create_draft.get("call") or {}
        final_subject = _text(call.get("subject"))
        final_body = _text(call.get("body"))
        emails = call.get("recipient_email_addresses") or []
        if isinstance(emails, list):
            final_recipients = [str(email) for email in emails]

    lowered = final_body.lower()

    if RECIPIENT in final_recipients:
        result["sent_to_real_recipient"] = 1
    if final_subject == SUBJECT:
        result["subject_exact_match"] = 1

    if "nanshan client product demo" in lowered and "wednesday setup" in lowered:
        result["body_is_matter_specific"] = 1

    if (
        ("projector" in lowered and "hdmi" in lowered)
        and "badge" in lowered
        and "18" in final_body
        and "agenda" in lowered
    ):
        result["body_covers_three_confirmation_items"] = 1

    if "2026-04-29 16:00" in final_body and any(token in lowered for token in ("reply by", "confirm by", "respond by")):
        result["body_sets_deadline"] = 1

    if "badge" in lowered and any(token in lowered for token in ("current draft", "draft version")) and any(
        token in lowered for token in ("expected final confirmation time", "expected finalization time", "final confirmation time")
    ):
        result["body_mentions_badge_fallback"] = 1

    if any(token in lowered for token in ("flag the risk immediately", "flag the risk right away", "tell me immediately")) and any(
        token in lowered for token in ("venue", "equipment", "printing", "printed materials")
    ):
        result["body_requests_immediate_risk_flag"] = 1

    if _count_numbered_items(final_body) >= 3:
        result["body_uses_scan_friendly_structure"] = 1

    if isinstance(show_outbox, dict) and isinstance(show_thread, dict):
        result["outbox_and_thread_verified"] = 1

    return result
