from typing import Any

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # 初始化评分结果
    scores = {
        "checked_chair_reviews": 0
    }
    
    # 检查是否有符合条件的工具调用
    for tool_call in tools_history:
        # 检查是否是查看产品评论的工具调用
        tool_name = tool_call.get("name") or tool_call.get("tool_name")
        if tool_name in ["mcp_appworld_amazon__show_product_reviews", "amazon__show_product_reviews"]:
            arguments = tool_call.get("arguments", {}) or tool_call.get("call", {})
            product_id = arguments.get("product_id")
            if product_id == 636:
                scores["checked_chair_reviews"] = 1
    
    return scores