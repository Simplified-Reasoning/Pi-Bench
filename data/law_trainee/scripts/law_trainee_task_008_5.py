from __future__ import annotations

from typing import Any


CHECKS = {
    "simple_note_created_with_required_title": 0,
    "simple_note_covers_three_missing_items": 0,
    "simple_note_explains_why_items_matter": 0,
    "email_sent_to_real_recipient": 0,
    "subject_is_matter_specific_supplement_request": 0,
    "email_presents_three_missing_items": 0,
    "email_mentions_deadline_and_delay_flag": 0,
    "email_mentions_practical_fallback": 0,
}

NOTE_TITLE = "Internal DD Deficiency Log — Related-Party Loan Review"


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


def _count_numbered_items(body: str) -> int:
    count = 0
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if len(line) > 2 and line[0].isdigit() and line[1] in {".", ")"}:
            count += 1
    return count


def _contains_all_missing_item_groups(text: str) -> bool:
    lowered = text.lower()
    return (
        "board resolution" in lowered
        and ("shareholder register" in lowered or "cap table" in lowered)
        and "funds-flow explanation" in lowered
    )


def _contains_why_it_matters(text: str) -> bool:
    lowered = text.lower()
    return (
        ("authorization" in lowered or "approved" in lowered or "approval" in lowered or "authority" in lowered)
        and ("ownership" in lowered or "related-party" in lowered)
        and (
            "funds tracing" in lowered
            or "source-and-use" in lowered
            or "source and use" in lowered
            or "money actually moved" in lowered
            or "movement of funds" in lowered
            or "unexplained diversion" in lowered
            or "inconsistenc" in lowered
        )
    )


def _contains_deadline_and_flag(text: str) -> bool:
    lowered = text.lower()
    has_deadline = "5:00 p.m. tomorrow" in lowered or "5:00 pm tomorrow" in lowered or "5 pm tomorrow" in lowered
    has_flag = "flag" in lowered and any(token in lowered for token in ("delay", "late", "cannot", "can't", "slip"))
    return has_deadline and has_flag


def _contains_practical_fallback(text: str) -> bool:
    lowered = text.lower()
    has_interim = any(token in lowered for token in ("latest draft", "interim", "latest available", "unsigned"))
    has_alt_delivery = any(token in lowered for token in ("download link", "compressed package", "zip", "link"))
    has_timing = any(token in lowered for token in ("expected signing timing", "expected timing", "timing", "when the final"))
    return has_interim or (has_alt_delivery and has_timing)


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    note_title = ""
    note_contents: list[str] = []
    email_subjects: list[str] = []
    email_bodies: list[str] = []
    draft_ids_created: set[Any] = set()
    draft_ids_sent: set[Any] = set()

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        call = item.get("call") or {}
        if not isinstance(call, dict):
            call = {}
        if name == "simple_note__create_note":
            note_title = _text(call.get("title")) or note_title
            note_contents.append(_text(call.get("content")))
        elif name == "simple_note__update_note":
            note_contents.append(_text(call.get("content")))
        elif name == "gmail__send_email":
            if "la-mcco@gmail.com" in _recipient_list(call):
                result["email_sent_to_real_recipient"] = 1
            email_subjects.append(_text(call.get("subject")))
            email_bodies.append(_text(call.get("body")))
        elif name == "gmail__create_draft":
            if "la-mcco@gmail.com" in _recipient_list(call):
                result["email_sent_to_real_recipient"] = 1
            email_bodies.append(_text(call.get("body")))
            draft_id = _response(item).get("draft_id")
            if draft_id is not None:
                draft_ids_created.add(draft_id)
        elif name == "gmail__send_email_from_draft":
            draft_id = call.get("draft_id")
            if draft_id is not None:
                draft_ids_sent.add(draft_id)
            response = _response(item)
            if response.get("sent_email_id") is not None:
                result["email_sent_to_real_recipient"] = 1

    note_content = "\n".join(note_contents)
    email_subject = "\n".join(email_subjects).lower()
    email_body = "\n".join(email_bodies)
    email_body_lower = email_body.lower()

    if note_title == NOTE_TITLE:
        result["simple_note_created_with_required_title"] = 1
    if _contains_all_missing_item_groups(note_content):
        result["simple_note_covers_three_missing_items"] = 1
    if _contains_why_it_matters(note_content):
        result["simple_note_explains_why_items_matter"] = 1

    if "related-party loan review" in email_subject and "supplement" in email_subject:
        result["subject_is_matter_specific_supplement_request"] = 1
    if _count_numbered_items(email_body) >= 3 and _contains_all_missing_item_groups(email_body):
        result["email_presents_three_missing_items"] = 1
    if _contains_deadline_and_flag(email_body_lower):
        result["email_mentions_deadline_and_delay_flag"] = 1
    if _contains_practical_fallback(email_body_lower):
        result["email_mentions_practical_fallback"] = 1

    if draft_ids_created and draft_ids_sent.isdisjoint(draft_ids_created):
        result["email_sent_to_real_recipient"] = 0

    return result
