from typing import Any

def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    # Initialize scores
    scores = {
        "read_enterprise_ai_bootcamp_strategy": 0,
        "read_community_launch_rulebook": 0,
        "write_5_day_launch_sop": 0
    }
    
    # Check each tool call in history
    for tool_call in tools_history:
        # Get tool name and arguments - note: keys are 'tool_name' and 'call'
        tool_name = tool_call.get('tool_name', '')
        arguments = tool_call.get('call', {})
        
        # Check if it's a read file tool call (handle various tool names)
        if any(keyword in tool_name.lower() for keyword in ['read', 'file']):
            # Get the file path from arguments - could be 'file_path', 'path', or other keys
            file_path = ''
            if isinstance(arguments, dict):
                # Try common keys for file path
                for key in ['file_path', 'path', 'file', 'filepath']:
                    if key in arguments:
                        file_path = str(arguments[key])
                        break
            
            # Check if it's the Enterprise_AI_Bootcamp_Strategy.md file
            if 'Enterprise_AI_Bootcamp_Strategy.md' in file_path:
                scores['read_enterprise_ai_bootcamp_strategy'] = 1
            
            # Check if it's the Community_Launch_Rulebook.md file
            if 'Community_Launch_Rulebook.md' in file_path:
                scores['read_community_launch_rulebook'] = 1
        
        # Check if it's a write file tool call (handle various tool names)
        elif any(keyword in tool_name.lower() for keyword in ['write', 'file']):
            # Get the file path from arguments - could be 'file_path', 'path', or other keys
            file_path = ''
            if isinstance(arguments, dict):
                # Try common keys for file path
                for key in ['file_path', 'path', 'file', 'filepath']:
                    if key in arguments:
                        file_path = str(arguments[key])
                        break

            if '5_Day_Launch_SOP.md' in file_path:
                scores['write_5_day_launch_sop'] = 1
    
    return scores