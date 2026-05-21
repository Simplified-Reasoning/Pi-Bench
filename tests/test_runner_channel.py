from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from src.channels.base import BaseChannel
from src.runner.runner import BenchmarkRunner


class DummyChannel(BaseChannel):
    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config or {"reset_timeout": 0.01})
        self.sent: list[str] = []
        self.reset_count = 0

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def reset(self) -> None:
        self.reset_count += 1
        await super().reset()


class EmptyUserAgent:
    profile = SimpleNamespace(user_id="user_001")
    episode = SimpleNamespace(task_order=[])

    def start_next_task(self):
        return None


class BrokenUserAgent:
    profile = SimpleNamespace(user_id="user_001")
    episode = SimpleNamespace(task_order=["missing_task"])

    def start_next_task(self):
        raise KeyError("Unknown task_id: missing_task")


def test_channel_reset_timeout_does_not_hang_without_ack() -> None:
    channel = DummyChannel({"reset_timeout": 0.01})

    asyncio.run(channel.reset())

    assert channel.sent == ["/new"]


def test_runner_completes_cleanly_when_no_tasks_remain() -> None:
    runner = BenchmarkRunner(channel=DummyChannel(), user_agent=EmptyUserAgent())

    result = asyncio.run(runner.run())

    assert result.status == "COMPLETED"
    assert result.tasks == []


def test_runner_does_not_treat_task_data_errors_as_exhaustion() -> None:
    runner = BenchmarkRunner(channel=DummyChannel(), user_agent=BrokenUserAgent())

    with pytest.raises(KeyError, match="missing_task"):
        asyncio.run(runner.run())
