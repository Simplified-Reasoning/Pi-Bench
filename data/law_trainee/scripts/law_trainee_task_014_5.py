from __future__ import annotations

from typing import Any


CHECKS = {
    "final_note_created_with_required_title": 0,
    "final_note_mentions_partner_review_and_hearing_date": 0,
    "final_note_mentions_guaranty_exposure_gap": 0,
    "final_note_mentions_bank_flow_and_confirmation_points": 0,
    "todoist_project_created": 0,
    "temporary_board_or_note_three_required_work_items": 0,
    "todoist_cleanup_completed": 0,
}

NOTE_TITLE = "Partner Handover — Yuehai Guarantee Dispute Hearing Prep"
PROJECT_NAME = "Temporary Hearing Prep Board - Yuehai"


def _norm(name: str) -> str:
    return name.removeprefix("mcp_appworld_")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _matched_work_items(text: str) -> set[str]:
    matched = set()
    if "guaranty" in text and any(token in text for token in ("reconcile", "comparison", "version")):
        matched.add("guaranty")
    if "bank-flow" in text and "exhibit" in text:
        matched.add("bank_flow")
    if "preservation" in text and "speaking order" in text:
        matched.add("coordination")
    return matched


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = dict(CHECKS)

    note_title = ""
    note_contents: list[str] = []
    create_project = None
    create_tasks: list[dict[str, Any]] = []
    delete_project = None
    created_project_id = None

    for item in tools_history or []:
        if not isinstance(item, dict):
            continue
        name = _norm(str(item.get("tool_name") or ""))
        if name == "simple_note__create_note":
            call = item.get("call") or {}
            note_title = _text(call.get("title")) or note_title
            note_contents.append(_text(call.get("content")))
        elif name == "simple_note__update_note":
            call = item.get("call") or {}
            note_contents.append(_text(call.get("content")))
        elif name == "todoist__create_project":
            create_project = item
            created_project_id = ((item.get("result") or {}).get("response") or {}).get("project_id")
        elif name == "todoist__create_task":
            create_tasks.append(item)
        elif name == "todoist__delete_project":
            delete_project = item

    note_content = "\n".join(note_contents).lower()

    if note_title == NOTE_TITLE:
        result["final_note_created_with_required_title"] = 1
    if "partner review" in note_content and "18 april 2026" in note_content:
        result["final_note_mentions_partner_review_and_hearing_date"] = 1
    if "guaranty" in note_content and "exposure" in note_content and any(
        token in note_content for token in ("cannot be finalized", "cannot finalize", "reconcile", "compared")
    ):
        result["final_note_mentions_guaranty_exposure_gap"] = 1
    if (
        "bank-flow" in note_content
        and "exhibit references" in note_content
        and "preservation" in note_content
        and "speaking order" in note_content
    ):
        result["final_note_mentions_bank_flow_and_confirmation_points"] = 1

    if isinstance(create_project, dict) and _text((create_project.get("call") or {}).get("name")) == PROJECT_NAME:
        result["todoist_project_created"] = 1

    matched = _matched_work_items(note_content)
    for item in create_tasks:
        call = item.get("call") or {}
        if call.get("project_id") != created_project_id:
            continue
        combined = f"{_text(call.get('title'))} {_text(call.get('description'))}".lower()
        matched.update(_matched_work_items(combined))
    if matched == {"guaranty", "bank_flow", "coordination"}:
        result["temporary_board_or_note_three_required_work_items"] = 1

    if isinstance(delete_project, dict) and (delete_project.get("call") or {}).get("project_id") == created_project_id:
        result["todoist_cleanup_completed"] = 1

    return result
