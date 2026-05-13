from __future__ import annotations

from typing import Any


CRITERION_REVIEW_POSTED = (
    "Successfully used spotify__review_song to post a review for Heartstrings Symphony."
)
CRITERION_FOLLOWED_ARTIST = (
    "Successfully used spotify__follow_artist to follow Ava Morgan."
)
CRITERION_LIKED_SONG = (
    "Successfully used spotify__like_song to like Heartstrings Symphony."
)

TARGET_SONG_ID = 54
TARGET_ARTIST_ID = 5


def _default_scores() -> dict[str, int]:
    return {
        CRITERION_REVIEW_POSTED: 0,
        CRITERION_FOLLOWED_ARTIST: 0,
        CRITERION_LIKED_SONG: 0,
    }


def _tool_name_matches(tool_name: str, suffix: str) -> bool:
    tool_name = (tool_name or "").strip().lower()
    suffix = suffix.lower()
    return tool_name == suffix or tool_name.endswith(suffix)


def _call_succeeded(result_payload: Any) -> bool:
    if not isinstance(result_payload, dict):
        return False

    if result_payload.get("is_error") is True:
        return False

    response = result_payload.get("response")
    if response is None:
        return False

    if isinstance(response, dict) and response.get("is_error") is True:
        return False

    return True


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = _default_scores()

    if not isinstance(tools_history, list) or not tools_history:
        return result

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or "")
        call_payload = item.get("call")
        result_payload = item.get("result")

        if not isinstance(call_payload, dict):
            call_payload = {}

        # 1) 评论歌曲 Heartstrings Symphony（song_id = 54）
        if _tool_name_matches(tool_name, "spotify__review_song"):
            song_id = call_payload.get("song_id")
            if song_id == TARGET_SONG_ID and _call_succeeded(result_payload):
                result[CRITERION_REVIEW_POSTED] = 1

        # 2) 关注歌手 Ava Morgan（artist_id = 5）
        if _tool_name_matches(tool_name, "spotify__follow_artist"):
            artist_id = call_payload.get("artist_id")
            if artist_id == TARGET_ARTIST_ID and _call_succeeded(result_payload):
                result[CRITERION_FOLLOWED_ARTIST] = 1

        # 3) 点赞歌曲 Heartstrings Symphony（song_id = 54）
        if _tool_name_matches(tool_name, "spotify__like_song"):
            song_id = call_payload.get("song_id")
            if song_id == TARGET_SONG_ID and _call_succeeded(result_payload):
                result[CRITERION_LIKED_SONG] = 1

    return result