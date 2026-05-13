from __future__ import annotations

from typing import Any


CHECKLIST_USED_ADD_TO_CART = "used amazon__add_product_to_cart"
CHECKLIST_USED_SHOW_CART = "used amazon__show_cart"
CHECKLIST_TARGET_PRODUCT_IN_CART = "target product 1578 is in cart"
CHECKLIST_TARGET_QUANTITY_ONE = "target product quantity == 1"


TARGET_PRODUCT_ID = 1578


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_USED_ADD_TO_CART: 0,
        CHECKLIST_USED_SHOW_CART: 0,
        CHECKLIST_TARGET_PRODUCT_IN_CART: 0,
        CHECKLIST_TARGET_QUANTITY_ONE: 0,
    }


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = _default_scores()

    if not isinstance(tools_history, list) or not tools_history:
        return result

    last_show_cart: dict[str, Any] | None = None

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or "").strip()

        if tool_name == "mcp_appworld_amazon__add_product_to_cart":
            call_payload = item.get("call")
            if isinstance(call_payload, dict) and call_payload.get("product_id") == TARGET_PRODUCT_ID:
                result[CHECKLIST_USED_ADD_TO_CART] = 1

        if tool_name == "mcp_appworld_amazon__show_cart":
            last_show_cart = item

    if not isinstance(last_show_cart, dict):
        return result

    result[CHECKLIST_USED_SHOW_CART] = 1

    response_payload = last_show_cart.get("result")
    cart_items: list[dict[str, Any]] = []

    if isinstance(response_payload, dict):
        response_block = response_payload.get("response")
        if isinstance(response_block, dict):
            raw_items = response_block.get("cart_items")
            if isinstance(raw_items, list):
                cart_items = [item for item in raw_items if isinstance(item, dict)]

    target_item: dict[str, Any] | None = None
    for item in cart_items:
        if item.get("product_id") == TARGET_PRODUCT_ID:
            target_item = item
            break

    if not isinstance(target_item, dict):
        return result

    result[CHECKLIST_TARGET_PRODUCT_IN_CART] = 1

    if target_item.get("quantity") == 1:
        result[CHECKLIST_TARGET_QUANTITY_ONE] = 1

    return result