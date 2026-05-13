from __future__ import annotations

CLARIFY_FOLLOWUP_STYLE = "Clarify"
OPTIONS_FOLLOWUP_STYLE = "Options"
TARGETED_FOLLOWUP_STYLES = (
    CLARIFY_FOLLOWUP_STYLE,
    OPTIONS_FOLLOWUP_STYLE,
)


def normalize_targeted_followup_style(value: str) -> str:
    normalized = str(value or "").strip().lower()
    for style in TARGETED_FOLLOWUP_STYLES:
        if normalized == style.lower():
            return style
    raise ValueError(f"invalid targeted followup style: {value!r}")
