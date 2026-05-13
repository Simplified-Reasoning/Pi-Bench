from __future__ import annotations

from typing import Any


CHECKLIST_LOGIN = "uses Gmail login flow and reuses returned access token"
CHECKLIST_SEND = "sends a new email to stmcco@gmail.com with subject Instrument booking follow-up via mcp_appworld_gmail__send_email"
CHECKLIST_BODY = "email body includes the brief-derived instrument booking details"
CHECKLIST_CONFIRM = "executes a post-send confirmation step such as show_outbox_threads or show_thread"
CHECKLIST_NO_DRAFT_ONLY = "does not rely solely on draft-only flow"


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_LOGIN: 0,
        CHECKLIST_SEND: 0,
        CHECKLIST_BODY: 0,
        CHECKLIST_CONFIRM: 0,
        CHECKLIST_NO_DRAFT_ONLY: 0,
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


def _contains_recipient(email_addresses: Any, expected: str) -> bool:
    if isinstance(email_addresses, str):
        return expected.lower() in email_addresses.lower()
    if isinstance(email_addresses, list):
        return any(isinstance(value, str) and value.lower() == expected.lower() for value in email_addresses)
    return False


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    scores = _default_scores()
    if not isinstance(tools_history, list) or not tools_history:
        return scores

    login_token: Any = None
    saw_send = False
    saw_confirm = False
    saw_draft_only_flow = False

    for item in tools_history:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("tool_name") or "").strip()
        call = item.get("call")
        call = call if isinstance(call, dict) else {}
        response = _response_block(item)

        if _tool_matches(tool_name, "gmail__login"):
            login_token = response.get("access_token")
            if login_token:
                scores[CHECKLIST_LOGIN] = 1

        elif _tool_matches(tool_name, "gmail__send_email"):
            subject = call.get("subject")
            body = str(call.get("body") or "")
            normalized_body = body.lower().replace("–", "-").replace("—", "-")
            recipient_ok = _contains_recipient(call.get("email_addresses"), "stmcco@gmail.com")
            if subject == "Instrument booking follow-up" and (
                not login_token or call.get("access_token") == login_token
            ) and recipient_ok:
                scores[CHECKLIST_SEND] = 1
                saw_send = True
            mentions_time = (
                ("tuesday" in normalized_body or "周二" in body)
                and ("thursday" in normalized_body or "周四" in body)
                and (
                    "afternoon" in normalized_body
                    or "下午" in body
                    or (("2-5" in normalized_body or "2 to 5" in normalized_body)
                        and ("1-4" in normalized_body or "1 to 4" in normalized_body))
                )
            )
            mentions_request = (
                "next week" in normalized_body
                or "下周" in body
                or "available instrument time" in normalized_body
                or "空余机时" in body
            )
            mentions_slot = "lc-ms" in normalized_body and (
                "4-hour" in normalized_body
                or "4 hour" in normalized_body
                or "four-hour" in normalized_body
                or "four hour" in normalized_body
            )
            mentions_prep = "sample prep" in normalized_body and "30" in normalized_body
            if mentions_time and mentions_request and mentions_slot and mentions_prep:
                scores[CHECKLIST_BODY] = 1

        elif _tool_matches(tool_name, "gmail__show_outbox_threads") or _tool_matches(tool_name, "gmail__show_thread"):
            if saw_send and (not login_token or call.get("access_token") == login_token):
                saw_confirm = True

        elif _tool_matches(tool_name, "gmail__create_draft") or _tool_matches(tool_name, "gmail__update_draft") or _tool_matches(tool_name, "gmail__send_email_from_draft"):
            saw_draft_only_flow = True

    if saw_confirm:
        scores[CHECKLIST_CONFIRM] = 1
    if scores[CHECKLIST_SEND] == 1:
        scores[CHECKLIST_NO_DRAFT_ONLY] = 1
    elif saw_draft_only_flow:
        scores[CHECKLIST_NO_DRAFT_ONLY] = 0
    return scores
