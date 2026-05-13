from __future__ import annotations

from typing import Any


CHECKLIST_LOGIN = "uses Amazon login flow and reuses returned access token"
CHECKLIST_SEARCH = "executes Amazon product search before wish list write"
CHECKLIST_ADD = "adds exactly one product to the wish list"
CHECKLIST_VERIFY = "verifies the write by checking the wish list afterward"
CHECKLIST_NO_ORDER = "does not add product to cart or place an order"


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_LOGIN: 0,
        CHECKLIST_SEARCH: 0,
        CHECKLIST_ADD: 0,
        CHECKLIST_VERIFY: 0,
        CHECKLIST_NO_ORDER: 0,
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


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    scores = _default_scores()
    if not isinstance(tools_history, list) or not tools_history:
        return scores

    login_token: Any = None
    search_seen = False
    add_count = 0
    verify_seen = False
    forbidden_seen = False

    for item in tools_history:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("tool_name") or "").strip()
        call = item.get("call")
        call = call if isinstance(call, dict) else {}
        response = _response_block(item)

        if _tool_matches(tool_name, "amazon__login"):
            login_token = response.get("access_token")
            if login_token:
                scores[CHECKLIST_LOGIN] = 1

        elif _tool_matches(tool_name, "amazon__search_products"):
            search_seen = True

        elif _tool_matches(tool_name, "amazon__add_product_to_wish_list"):
            if search_seen and (not login_token or call.get("access_token") == login_token):
                add_count += 1

        elif _tool_matches(tool_name, "amazon__show_wish_list"):
            if add_count == 1 and (not login_token or call.get("access_token") == login_token):
                verify_seen = True

        elif _tool_matches(tool_name, "amazon__add_product_to_cart") or _tool_matches(tool_name, "amazon__place_order"):
            forbidden_seen = True

    if search_seen:
        scores[CHECKLIST_SEARCH] = 1
    if add_count == 1:
        scores[CHECKLIST_ADD] = 1
    if verify_seen:
        scores[CHECKLIST_VERIFY] = 1
    if not forbidden_seen:
        scores[CHECKLIST_NO_ORDER] = 1
    return scores
