# from __future__ import annotations

# import re
# from typing import Any


# CRITERION_ALL_17 = "All 17 target co-authors should be emailed."

# TARGETS = {
#     "ad.blackburn@gmail.com": "Adam Blackburn <ad.blackburn@gmail.com> should be emailed.",
#     "mar_blac@gmail.com": "Martin Blackburn <mar_blac@gmail.com> should be emailed.",
#     "jar_calhoun@gmail.com": "Jared Calhoun <jar_calhoun@gmail.com> should be emailed.",
#     "allison-calhoun@gmail.com": "Allison Calhoun <allison-calhoun@gmail.com> should be emailed.",
#     "brandon-webe@gmail.com": "Brandon Weber <brandon-webe@gmail.com> should be emailed.",
#     "tra_weber@gmail.com": "Tracy Weber <tra_weber@gmail.com> should be emailed.",
#     "brenda.webe@gmail.com": "Brenda Smith <brenda.webe@gmail.com> should be emailed.",
#     "joseph.webe@gmail.com": "Joseph Weber <joseph.webe@gmail.com> should be emailed.",
#     "as_moore@gmail.com": "Ashley Moore <as_moore@gmail.com> should be emailed.",
#     "gl.moore@gmail.com": "Glen Moore <gl.moore@gmail.com> should be emailed.",
#     "joyce-weav@gmail.com": "Joyce Weaver <joyce-weav@gmail.com> should be emailed.",
#     "je.simpson@gmail.com": "Jeffery Simpson <je.simpson@gmail.com> should be emailed.",
#     "jasonsimp@gmail.com": "Jason Simpson <jasonsimp@gmail.com> should be emailed.",
#     "lindseysimpson@gmail.com": "Lindsey Simpson <lindseysimpson@gmail.com> should be emailed.",
#     "ca-smit@gmail.com": "Catherine Smith <ca-smit@gmail.com> should be emailed.",
#     "ma_smith@gmail.com": "Marcus Smith <ma_smith@gmail.com> should be emailed.",
#     "cod.smith@gmail.com": "Cody Smith <cod.smith@gmail.com> should be emailed.",
# }


# def _default_scores() -> dict[str, int]:
#     result = {CRITERION_ALL_17: 0}
#     for criterion in TARGETS.values():
#         result[criterion] = 0
#     return result


# def _normalize_tool_name(name: str) -> str:
#     return (name or "").strip().lower()


# def _is_send_email_tool(tool_name: str) -> bool:
#     name = _normalize_tool_name(tool_name)
#     return (
#         name == "mcp_appworld_gmail__send_email"
#         or name.endswith("gmail__send_email")
#         or name == "mcp_appworld_gmail_send_email"
#         or name.endswith("gmail_send_email")
#     )


# def _split_emails(value: str) -> list[str]:
#     parts = re.split(r"[;,]", value)
#     return [p.strip().lower() for p in parts if p.strip()]


# def _extract_recipients(call_payload: dict[str, Any]) -> set[str]:
#     recipients: set[str] = set()

#     # 你要求优先看 email_addresses
#     candidate_keys = [
#         "email_addresses",
#         "recipient_emails",
#         "to",
#         "email_address",
#         "recipient_email",
#         "email",
#     ]

#     for key in candidate_keys:
#         if key not in call_payload:
#             continue

#         value = call_payload.get(key)

#         if isinstance(value, str):
#             for email in _split_emails(value):
#                 recipients.add(email)
#         elif isinstance(value, list):
#             for item in value:
#                 if isinstance(item, str):
#                     for email in _split_emails(item):
#                         recipients.add(email)

#     return recipients


# def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
#     result = _default_scores()

#     if not isinstance(tools_history, list) or not tools_history:
#         return result

#     sent_recipients: set[str] = set()

#     for item in tools_history:
#         if not isinstance(item, dict):
#             continue

#         tool_name = str(item.get("tool_name") or "")
#         if not _is_send_email_tool(tool_name):
#             continue

#         call_payload = item.get("call")
#         if not isinstance(call_payload, dict):
#             continue

#         sent_recipients.update(_extract_recipients(call_payload))

#     target_set = set(TARGETS.keys())

#     # 只要求 17 个目标人都发到了，不限制是否额外发给别人
#     if target_set.issubset(sent_recipients):
#         result[CRITERION_ALL_17] = 1

#     for email, criterion in TARGETS.items():
#         if email in sent_recipients:
#             result[criterion] = 1

#     return result

from __future__ import annotations

import re
from typing import Any


CRITERION_ALL_17 = "All 17 target co-authors should be emailed."

TARGETS = {
    "ad.blackburn@gmail.com",
    "mar_blac@gmail.com",
    "jar_calhoun@gmail.com",
    "allison-calhoun@gmail.com",
    "brandon-webe@gmail.com",
    "tra_weber@gmail.com",
    "brenda.webe@gmail.com",
    "joseph.webe@gmail.com",
    "as_moore@gmail.com",
    "gl.moore@gmail.com",
    "joyce-weav@gmail.com",
    "je.simpson@gmail.com",
    "jasonsimp@gmail.com",
    "lindseysimpson@gmail.com",
    "ca-smit@gmail.com",
    "ma_smith@gmail.com",
    "cod.smith@gmail.com",
}


def _default_scores() -> dict[str, int]:
    return {CRITERION_ALL_17: 0}


def _normalize_tool_name(name: str) -> str:
    return (name or "").strip().lower()


def _is_send_email_tool(tool_name: str) -> bool:
    name = _normalize_tool_name(tool_name)
    return (
        name == "mcp_appworld_gmail__send_email"
        or name.endswith("gmail__send_email")
        or name == "mcp_appworld_gmail_send_email"
        or name.endswith("gmail_send_email")
    )


def _split_emails(value: str) -> list[str]:
    parts = re.split(r"[;,]", value)
    return [p.strip().lower() for p in parts if p.strip()]


def _extract_recipients(call_payload: dict[str, Any]) -> set[str]:
    recipients: set[str] = set()

    candidate_keys = [
        "email_addresses",
        "recipient_emails",
        "to",
        "email_address",
        "recipient_email",
        "email",
    ]

    for key in candidate_keys:
        if key not in call_payload:
            continue

        value = call_payload.get(key)

        if isinstance(value, str):
            recipients.update(_split_emails(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    recipients.update(_split_emails(item))

    return recipients


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = _default_scores()

    if not isinstance(tools_history, list) or not tools_history:
        return result

    sent_recipients: set[str] = set()

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or "")
        if not _is_send_email_tool(tool_name):
            continue

        call_payload = item.get("call")
        if not isinstance(call_payload, dict):
            continue

        sent_recipients.update(_extract_recipients(call_payload))

    if TARGETS.issubset(sent_recipients):
        result[CRITERION_ALL_17] = 1

    return result