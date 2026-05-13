from __future__ import annotations

from typing import Any


CHECKS = {
    "used_amazon_search_products": 0,
    "used_amazon_add_to_cart": 0,
    "used_amazon_show_cart": 0,
    "target_product_in_cart": 0,
    "target_quantity_is_one": 0,
}

TARGET_PRODUCT_ID = 3


def _tool_name_matches(name: str, suffix: str) -> bool:
    tool_name = (name or "").strip().lower()
    suffix = suffix.lower()
    return tool_name == suffix or tool_name.endswith(suffix)


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    if not isinstance(tools_history, list) or not tools_history:
        return result

    last_show_cart: dict[str, Any] | None = None

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or "")
        call_payload = item.get("call") or {}

        if _tool_name_matches(tool_name, "amazon__search_products"):
            result["used_amazon_search_products"] = 1

        if _tool_name_matches(tool_name, "amazon__add_product_to_cart"):
            if isinstance(call_payload, dict) and call_payload.get("product_id") == TARGET_PRODUCT_ID:
                result["used_amazon_add_to_cart"] = 1

        if _tool_name_matches(tool_name, "amazon__show_cart"):
            last_show_cart = item

    if not isinstance(last_show_cart, dict):
        return result

    result["used_amazon_show_cart"] = 1
    response_payload = last_show_cart.get("result") or {}
    response_block = response_payload.get("response") or {}
    cart_items = response_block.get("cart_items") or []
    if not isinstance(cart_items, list):
        return result

    for item in cart_items:
        if not isinstance(item, dict):
            continue
        if item.get("product_id") == TARGET_PRODUCT_ID:
            result["target_product_in_cart"] = 1
            if item.get("quantity") == 1:
                result["target_quantity_is_one"] = 1
            break

    return result
