from __future__ import annotations

from typing import Any


CHECKLIST_LOGIN = "uses file system login flow and reuses returned access token"
CHECKLIST_CREATE = "creates directories and files before copy/move operations"
CHECKLIST_FILE_FLOW = "executes both file copy and file move"
CHECKLIST_DIR_FLOW = "executes both directory copy and directory move"
CHECKLIST_VALID = "follows a valid create-then-transform workflow on matching paths"


def _default_scores() -> dict[str, int]:
    return {
        CHECKLIST_LOGIN: 0,
        CHECKLIST_CREATE: 0,
        CHECKLIST_FILE_FLOW: 0,
        CHECKLIST_DIR_FLOW: 0,
        CHECKLIST_VALID: 0,
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
    created_dirs: set[str] = set()
    created_files: set[str] = set()
    file_copy_ok = False
    file_move_ok = False
    dir_copy_ok = False
    dir_move_ok = False

    for item in tools_history:
        if not isinstance(item, dict):
            continue
        tool_name = str(item.get("tool_name") or "").strip()
        call = item.get("call")
        call = call if isinstance(call, dict) else {}
        response = _response_block(item)

        if _tool_matches(tool_name, "file_system__login"):
            login_token = response.get("access_token")
            if login_token:
                scores[CHECKLIST_LOGIN] = 1

        elif _tool_matches(tool_name, "file_system__create_directory"):
            path = call.get("directory_path")
            if isinstance(path, str) and path:
                created_dirs.add(path)

        elif _tool_matches(tool_name, "file_system__create_file"):
            path = call.get("file_path")
            if isinstance(path, str) and path:
                created_files.add(path)

        elif _tool_matches(tool_name, "file_system__copy_file"):
            src = call.get("source_file_path")
            if isinstance(src, str) and src in created_files:
                file_copy_ok = True

        elif _tool_matches(tool_name, "file_system__move_file"):
            src = call.get("source_file_path")
            if isinstance(src, str) and (src in created_files):
                file_move_ok = True

        elif _tool_matches(tool_name, "file_system__copy_directory"):
            src = call.get("source_directory_path")
            if isinstance(src, str) and src in created_dirs:
                dir_copy_ok = True

        elif _tool_matches(tool_name, "file_system__move_directory"):
            src = call.get("source_directory_path")
            if isinstance(src, str) and src in created_dirs:
                dir_move_ok = True

    if created_dirs and created_files:
        scores[CHECKLIST_CREATE] = 1
    if file_copy_ok and file_move_ok:
        scores[CHECKLIST_FILE_FLOW] = 1
    if dir_copy_ok and dir_move_ok:
        scores[CHECKLIST_DIR_FLOW] = 1
    if created_dirs and created_files and file_copy_ok and file_move_ok and dir_copy_ok and dir_move_ok:
        scores[CHECKLIST_VALID] = 1
    return scores
