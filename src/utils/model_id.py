from __future__ import annotations


def safe_model_id(model_id: str) -> str:
    return str(model_id).strip().replace("/", "_")
