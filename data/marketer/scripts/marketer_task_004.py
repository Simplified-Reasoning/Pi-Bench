from typing import Any

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # 初始化评分结果
    scores = {
        "selected_playlist_correct": 0,
        "added_whispers_of_the_soul": 0,
        "added_a_love_that_never_was": 0,
        "added_twisted_paths": 0
    }
    
    # 检查是否有符合条件的工具调用
    for tool_call in tools_history:
        # 检查是否是 mcp_appworld_spotify__add_song_to_playlist 工具调用
        if tool_call.get("tool_name") == "mcp_appworld_spotify__add_song_to_playlist":
            # 获取工具参数
            call_args = tool_call.get("call", {})
            playlist_id = call_args.get("playlist_id")
            song_id = call_args.get("song_id")
            
            # 检查播放列表 ID 是否正确
            if playlist_id in [31, 33]:
                scores["selected_playlist_correct"] = 1
            
            # 检查是否添加了指定的歌曲
            if song_id == 77:
                scores["added_whispers_of_the_soul"] = 1
            elif song_id == 78:
                scores["added_a_love_that_never_was"] = 1
            elif song_id == 140:
                scores["added_twisted_paths"] = 1
    
    return scores