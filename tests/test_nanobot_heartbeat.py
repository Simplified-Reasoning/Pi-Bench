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


def _load_nanobot_heartbeat_modules():
    nanobot_pkg = types.ModuleType("nanobot")
    nanobot_pkg.__path__ = [str(NANOBOT_ROOT / "nanobot")]  # type: ignore[attr-defined]
    sys.modules.setdefault("nanobot", nanobot_pkg)
    providers_pkg = types.ModuleType("nanobot.providers")
    providers_pkg.__path__ = [str(NANOBOT_ROOT / "nanobot/providers")]  # type: ignore[attr-defined]
    sys.modules.setdefault("nanobot.providers", providers_pkg)

    base = _load_module("nanobot.providers.base", NANOBOT_ROOT / "nanobot/providers/base.py")
    heartbeat = _load_module("nanobot.heartbeat.service", NANOBOT_ROOT / "nanobot/heartbeat/service.py")
    return heartbeat.HeartbeatService, base.LLMGenerationConfig, base.LLMResponse, base.ToolCallRequest


HeartbeatService, LLMGenerationConfig, LLMResponse, ToolCallRequest = _load_nanobot_heartbeat_modules()


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
                    name="heartbeat",
                    arguments={"action": "skip", "tasks": ""},
                )
            ],
        )


def test_heartbeat_decision_forwards_model_generation_config(tmp_path: Path) -> None:
    provider = RecordingProvider()
    heartbeat = HeartbeatService(
        workspace=tmp_path,
        provider=provider,  # type: ignore[arg-type]
        model="kimi-k2.6",
        generation_config=LLMGenerationConfig(
            temperature=1.0,
            max_tokens=16384,
            reasoning_effort="medium",
        ),
    )

    action, tasks = asyncio.run(heartbeat._decide("# Heartbeat\n\nNo active tasks."))

    assert (action, tasks) == ("skip", "")
    assert provider.calls[0]["model"] == "kimi-k2.6"
    assert provider.calls[0]["temperature"] == 1.0
    assert provider.calls[0]["max_tokens"] == 16384
    assert provider.calls[0]["reasoning_effort"] == "medium"


def test_heartbeat_decision_accepts_string_tool_arguments(tmp_path: Path) -> None:
    class StringArgumentsProvider(RecordingProvider):
        async def chat(self, **kwargs: Any) -> LLMResponse:
            self.calls.append(kwargs)
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_1",
                        name="heartbeat",
                        arguments='{"action": "run", "tasks": "check pending filings"}',  # type: ignore[arg-type]
                    )
                ],
            )

    heartbeat = HeartbeatService(
        workspace=tmp_path,
        provider=StringArgumentsProvider(),  # type: ignore[arg-type]
        model="kimi-k2.6",
    )

    assert asyncio.run(heartbeat._decide("# Heartbeat\n\n- check pending filings")) == (
        "run",
        "check pending filings",
    )
