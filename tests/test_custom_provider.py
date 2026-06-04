from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


NANOBOT_ROOT = Path(__file__).resolve().parents[1] / "third_party" / "nanobot"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_custom_provider():
    nanobot_pkg = types.ModuleType("nanobot")
    nanobot_pkg.__path__ = [str(NANOBOT_ROOT / "nanobot")]  # type: ignore[attr-defined]
    sys.modules.setdefault("nanobot", nanobot_pkg)
    providers_pkg = types.ModuleType("nanobot.providers")
    providers_pkg.__path__ = [str(NANOBOT_ROOT / "nanobot/providers")]  # type: ignore[attr-defined]
    sys.modules.setdefault("nanobot.providers", providers_pkg)

    _load_module("nanobot.providers.base", NANOBOT_ROOT / "nanobot/providers/base.py")
    custom = _load_module("nanobot.providers.custom_provider", NANOBOT_ROOT / "nanobot/providers/custom_provider.py")
    return custom.CustomProvider


CustomProvider = _load_custom_provider()


def test_custom_provider_strips_tool_message_name() -> None:
    messages = [
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]},
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "web_fetch",
            "content": "done",
        },
    ]

    sanitized = CustomProvider._sanitize_request_messages(messages)

    assert sanitized[1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "done",
    }
    assert messages[1]["name"] == "web_fetch"


def test_custom_provider_keeps_non_tool_message_name() -> None:
    messages = [{"role": "user", "name": "alice", "content": "hello"}]

    assert CustomProvider._sanitize_request_messages(messages) == messages
