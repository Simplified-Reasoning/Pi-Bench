from __future__ import annotations

from typing import Any


CHECKLIST_LOGIN = "uses Splitwise login flow and reuses returned access token"
CHECKLIST_GROUP = "creates or binds a group before expense recording"
CHECKLIST_RECORD = "records a dinner-related expense"
CHECKLIST_SHOW = "checks group expenses after recording"
CHECKLIST_LIFECYCLE = "updates and later deletes the same expense"


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_LOGIN: 0,
        CHECKLIST_GROUP: 0,
        CHECKLIST_RECORD: 0,
        CHECKLIST_SHOW: 0,
        CHECKLIST_LIFECYCLE: 0,
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


def _response_value(item: dict[str, Any]) -> Any:
    result = item.get("result")
    if isinstance(result, dict):
        return result.get("response")
    return None


def _group_matches(group: dict[str, Any], name: str | None, member_emails: set[str]) -> bool:
    if name and str(group.get("name") or "") != name:
        return False
    if not member_emails:
        return True
    members = group.get("members")
    if not isinstance(members, list):
        return False
    seen = {
        str(member.get("email") or "").lower()
        for member in members
        if isinstance(member, dict)
    }
    return member_emails.issubset(seen)


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    scores = _default_scores()
    if not isinstance(tools_history, list) or not tools_history:
        return scores

    login_token: Any = None
    group_id: Any = None
    pending_group_name: str | None = None
    pending_member_emails: set[str] = set()
    expense_id: Any = None
    recorded = False
    showed = False
    updated = False
    deleted = False

    for item in tools_history:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("tool_name") or "").strip()
        call = item.get("call")
        call = call if isinstance(call, dict) else {}
        response = _response_block(item)
        response_value = _response_value(item)

        if _tool_matches(tool_name, "splitwise__login"):
            login_token = response.get("access_token")
            if login_token:
                scores[CHECKLIST_LOGIN] = 1

        elif _tool_matches(tool_name, "splitwise__create_group"):
            if not login_token or call.get("access_token") == login_token:
                pending_group_name = str(call.get("name") or "") or pending_group_name
                member_emails = call.get("member_emails")
                if isinstance(member_emails, list):
                    pending_member_emails = {
                        str(email).lower()
                        for email in member_emails
                        if isinstance(email, str) and email
                    }
                group_id = response.get("group_id")
                if group_id is not None:
                    scores[CHECKLIST_GROUP] = 1

        elif _tool_matches(tool_name, "splitwise__show_groups"):
            if not login_token or call.get("access_token") == login_token:
                if group_id is None and isinstance(response_value, list):
                    for group in response_value:
                        if isinstance(group, dict) and _group_matches(group, pending_group_name, pending_member_emails):
                            group_id = group.get("group_id")
                            break
                if group_id is not None:
                    scores[CHECKLIST_GROUP] = 1

        elif _tool_matches(tool_name, "splitwise__record_expense"):
            description = str(call.get("description") or "").lower()
            group_matches = group_id is None or call.get("group_id") == group_id
            if "dinner" in description and (not login_token or call.get("access_token") == login_token) and group_matches:
                expense_id = response.get("expense_id")
                recorded = True

        elif _tool_matches(tool_name, "splitwise__show_group_expenses"):
            if group_id is not None and call.get("group_id") == group_id:
                showed = True

        elif _tool_matches(tool_name, "splitwise__update_expense"):
            if expense_id is not None and call.get("expense_id") == expense_id:
                updated = True

        elif _tool_matches(tool_name, "splitwise__delete_expense"):
            if expense_id is not None and call.get("expense_id") == expense_id:
                deleted = True

    if recorded:
        scores[CHECKLIST_RECORD] = 1
    if recorded and showed:
        scores[CHECKLIST_SHOW] = 1
    if updated and deleted:
        scores[CHECKLIST_LIFECYCLE] = 1
    return scores
