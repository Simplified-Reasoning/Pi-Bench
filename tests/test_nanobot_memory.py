from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any


NANOBOT_ROOT = Path(__file__).resolve().parents[1] / "third_party" / "nanobot"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_nanobot_memory_modules():
    nanobot_pkg = types.ModuleType("nanobot")
    nanobot_pkg.__path__ = [str(NANOBOT_ROOT / "nanobot")]  # type: ignore[attr-defined]
    sys.modules.setdefault("nanobot", nanobot_pkg)
    for package in ("agent", "providers", "session", "utils"):
        pkg = types.ModuleType(f"nanobot.{package}")
        pkg.__path__ = [str(NANOBOT_ROOT / "nanobot" / package)]  # type: ignore[attr-defined]
        sys.modules.setdefault(f"nanobot.{package}", pkg)

    _load_module("nanobot.utils.helpers", NANOBOT_ROOT / "nanobot/utils/helpers.py")
    base = _load_module("nanobot.providers.base", NANOBOT_ROOT / "nanobot/providers/base.py")
    session = _load_module("nanobot.session.manager", NANOBOT_ROOT / "nanobot/session/manager.py")
    memory = _load_module("nanobot.agent.memory", NANOBOT_ROOT / "nanobot/agent/memory.py")
    return memory.MemoryStore, base.LLMGenerationConfig, base.LLMResponse, base.ToolCallRequest, session.Session


MemoryStore, LLMGenerationConfig, LLMResponse, ToolCallRequest, Session = _load_nanobot_memory_modules()


class RecordingProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def chat(self, **kwargs: Any) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_1",
                    name="save_memory",
                    arguments={
                        "history_entry": "[2026-05-29 17:00] Consolidated.",
                        "memory_update": "# Memory\nNo durable facts.",
                    },
                )
            ],
        )


def test_memory_consolidation_forwards_model_generation_config(tmp_path: Path) -> None:
    session = Session(key="test:chat")
    session.messages = [
        {"role": "user", "content": "hello", "timestamp": "2026-05-29T17:00:00"},
        {"role": "assistant", "content": "hi", "timestamp": "2026-05-29T17:00:01"},
    ]
    provider = RecordingProvider()

    ok = asyncio.run(
        MemoryStore(tmp_path).consolidate(
            session,
            provider,  # type: ignore[arg-type]
            "kimi-k2.6",
            archive_all=True,
            generation_config=LLMGenerationConfig(
                temperature=1.0,
                max_tokens=16384,
                reasoning_effort="medium",
            ),
        )
    )

    assert ok
    assert provider.calls[0]["model"] == "kimi-k2.6"
    assert provider.calls[0]["temperature"] == 1.0
    assert provider.calls[0]["max_tokens"] == 16384
    assert provider.calls[0]["reasoning_effort"] == "medium"
