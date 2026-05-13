from __future__ import annotations

from typing import Any


CHECKS = {
    "safe_exact_title_preclean": 0,
    "rough_to_final_note_workflow": 0,
    "final_note_has_required_headings": 0,
    "final_note_has_trip_timing": 0,
    "final_note_lists_required_items": 0,
    "final_note_mentions_weather_risks": 0,
    "final_note_mentions_food_cooler": 0,
    "final_note_has_pending_confirmations": 0,
    "final_note_has_friday_2100_deadline": 0,
}

NOTE_TITLE = "Weekend Camping Departure Memo - Qingyuan Reservoir"
REQUIRED_HEADINGS = (
    "Meet-up and Travel",
    "Must-Bring Items",
    "Weather and Risk Notes",
    "Pre-Departure Confirmations",
)
REQUIRED_ITEMS = (
    "headlamp",
    "light rain jacket",
    "2L",
    "ID card",
    "power bank",
)
PENDING_ITEMS = (
    "carpool",
    "ice",
    "stove fuel",
)


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _id_text(value: Any) -> str:
    return str(value) if isinstance(value, (int, str)) else ""


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    search = None
    delete_calls: list[dict[str, Any]] = []
    create_note = None
    add_note = None
    update_note = None
    show_note = None

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        if name == "simple_note__search_notes":
            search = item
        elif name == "simple_note__delete_note":
            delete_calls.append(item)
        elif name == "simple_note__create_note":
            create_note = item
        elif name == "simple_note__add_content_to_note":
            add_note = item
        elif name == "simple_note__update_note":
            update_note = item
        elif name == "simple_note__show_note":
            show_note = item

    exact_match_note_ids: set[Any] = set()
    if isinstance(search, dict):
        if _text((search.get("call") or {}).get("query")) == NOTE_TITLE:
            response = (search.get("result") or {}).get("response") or []
            if isinstance(response, list):
                for note in response:
                    if isinstance(note, dict) and _text(note.get("title")) == NOTE_TITLE:
                        exact_match_note_ids.add(note.get("note_id"))

    deleted_note_ids = {
        (item.get("call") or {}).get("note_id")
        for item in delete_calls
        if isinstance(item, dict)
    }
    if search:
        if exact_match_note_ids:
            if deleted_note_ids == exact_match_note_ids:
                result["safe_exact_title_preclean"] = 1
        elif not deleted_note_ids:
            result["safe_exact_title_preclean"] = 1

    created_note_id = _id_text((((create_note or {}).get("result") or {}).get("response") or {}).get("note_id"))
    added_note_id = _id_text(((add_note or {}).get("call") or {}).get("note_id"))
    updated_note_id = _id_text(((update_note or {}).get("call") or {}).get("note_id"))
    if create_note and add_note and update_note and created_note_id and created_note_id == added_note_id == updated_note_id:
        if _text((create_note.get("call") or {}).get("title")) == NOTE_TITLE:
            result["rough_to_final_note_workflow"] = 1

    final_title = ""
    final_content = ""
    if isinstance(show_note, dict):
        response = (show_note.get("result") or {}).get("response") or {}
        final_title = _text(response.get("title"))
        final_content = _text(response.get("content"))
    elif isinstance(update_note, dict):
        final_title = _text((create_note or {}).get("call", {}).get("title"))
        final_content = _text((update_note.get("call") or {}).get("content"))

    lowered = final_content.lower()

    if final_title == NOTE_TITLE and all(heading in final_content for heading in REQUIRED_HEADINGS):
        result["final_note_has_required_headings"] = 1

    if "Saturday 07:20" in final_content and "North Parking Lot" in final_content and "90" in final_content:
        result["final_note_has_trip_timing"] = 1

    if all(item.lower() in lowered for item in ["headlamp", "light rain jacket", "2l", "id card", "power bank"]):
        result["final_note_lists_required_items"] = 1

    if (
        any(token in lowered for token in ("after dark", "once it gets dark"))
        and any(token in lowered for token in ("windy", "cooler", "temperature drops"))
        and "18:00" in final_content
        and any(token in lowered for token in ("light rain", "rain"))
    ):
        result["final_note_mentions_weather_risks"] = 1

    if "cooler" in lowered and any(token in lowered for token in ("first", "before anything else", "go into the cooler first")):
        result["final_note_mentions_food_cooler"] = 1

    if all(item in lowered for item in PENDING_ITEMS):
        result["final_note_has_pending_confirmations"] = 1

    if "Friday 21:00" in final_content and any(token in lowered for token in ("confirm by", "completed by", "locked by")):
        result["final_note_has_friday_2100_deadline"] = 1

    return result
