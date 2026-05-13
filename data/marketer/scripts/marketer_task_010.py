from typing import Any

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # 初始化评分结果
    scores = {
        "sent_email": 0,
        "searched_denise_maldonado": 0
    }
    
    # 检查是否有符合条件的工具调用
    for tool_call in tools_history:
        # 检查是否是发送邮件的工具调用
        tool_name = tool_call.get("name") or tool_call.get("tool_name")
        if tool_name in ["mcp_appworld_gmail__send_email", "mcp_appworld_gmail__send_email_from_draft", "gmail__send_email", "gmail__send_email_from_draft"]:
            scores["sent_email"] = 1
        
        # 检查是否是搜索用户的工具调用
        elif tool_name in ["mcp_appworld_gmail__search_users", "gmail__search_users"]:
            arguments = tool_call.get("arguments", {}) or tool_call.get("call", {})
            query = arguments.get("query")
            if query == "Denise Maldonado":
                scores["searched_denise_maldonado"] = 1
    
    return scores