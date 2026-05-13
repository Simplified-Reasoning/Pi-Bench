from typing import Any

def score(tools_history: list[dict[str, Any]]) -> int:
    # 初始化评分结果
    scores = {
        "all_subtasks_created": 0
    }
    
    # 跟踪每个子任务的完成情况
    subtasks = {
        "reading": False,
        "physical recovery": False,
        "journaling": False,
        "sleep": False
    }
    
    # 检查是否有符合条件的工具调用
    for tool_call in tools_history:
        # 检查是否是创建项目的工具调用
        tool_name = tool_call.get("name") or tool_call.get("tool_name")
        # 检查是否是创建子任务的工具调用
        if tool_name in ["mcp_appworld_todoist__create_sub_task", "todoist__create_sub_task"]:
            arguments = tool_call.get("arguments", {}) or tool_call.get("call", {})
            title = arguments.get("title", "").lower()
            
            if "reading" in title:
                subtasks["reading"] = True
            if "physical recovery" in title:
                subtasks["physical recovery"] = True
            if "journaling" in title:
                subtasks["journaling"] = True
            if "sleep" in title:
                subtasks["sleep"] = True
    
    # 检查是否所有子任务都已创建
    if all(subtasks.values()):
        scores["all_subtasks_created"] = 1
    
    return scores