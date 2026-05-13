from __future__ import annotations

from typing import Any


CHECKS = {
    "searched_contact_or_thread": 0,
    "opened_text_window": 0,
    "message_sent_to_target": 0,
    "message_is_matter_specific": 0,
    "message_has_time_and_place": 0,
    "message_lists_required_items": 0,
    "message_sets_reply_deadline": 0,
    "message_requests_risk_flag": 0,
    "message_mentions_photo_fallback": 0,
    "message_is_scan_friendly": 0,
}

TARGET_NUMBER = "2873148336"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    search_contacts = None
    search_texts = None
    show_window = None
    send_text = None

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        if name == "phone__search_contacts":
            search_contacts = item
        elif name == "phone__search_text_messages":
            search_texts = item
        elif name == "phone__show_text_message_window":
            show_window = item
        elif name == "phone__send_text_message":
            send_text = item

    if isinstance(search_contacts, dict) or isinstance(search_texts, dict):
        if isinstance(search_texts, dict):
            phone_number = _text((search_texts.get("call") or {}).get("phone_number"))
            if phone_number == TARGET_NUMBER:
                result["searched_contact_or_thread"] = 1
        else:
            result["searched_contact_or_thread"] = 1

    if isinstance(show_window, dict) and _text((show_window.get("call") or {}).get("phone_number")) == TARGET_NUMBER:
        result["opened_text_window"] = 1

    final_message = ""
    if isinstance(send_text, dict):
        call = send_text.get("call") or {}
        if _text(call.get("phone_number")) == TARGET_NUMBER:
            result["message_sent_to_target"] = 1
        final_message = _text(call.get("message"))

    lowered = final_message.lower()

    if "chestnut" in lowered and any(token in lowered for token in ("boarding", "handover", "drop-off")):
        result["message_is_matter_specific"] = 1

    if "07:40" in final_message and "Riverside Vet Clinic" in final_message and "west gate" in lowered:
        result["message_has_time_and_place"] = 1

    if all(token in lowered for token in ("carrier", "vaccination booklet", "meal pouch")):
        result["message_lists_required_items"] = 1

    if "21:30" in final_message and any(token in lowered for token in ("confirm by", "reply by", "let me know by")):
        result["message_sets_reply_deadline"] = 1

    if any(token in lowered for token in ("pickup timing changes", "timing changes", "schedule changes")) and any(
        token in lowered for token in ("tell me immediately", "let me know immediately", "tell me right away")
    ) and "vaccination booklet" in lowered:
        result["message_requests_risk_flag"] = 1

    if any(token in lowered for token in ("send a photo first", "photo first", "send me a photo")):
        result["message_mentions_photo_fallback"] = 1

    sentence_breaks = final_message.count("\n") + final_message.count(";") + final_message.count(".")
    if sentence_breaks >= 2:
        result["message_is_scan_friendly"] = 1

    return result
