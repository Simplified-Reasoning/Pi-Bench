import asyncio
from abc import ABC, abstractmethod
from collections import deque

from .reset_policy import ResetResponsePolicy
from ..utils import get_logger


class BaseChannel(ABC):
    LOG_COMPONENT: str | None = None

    def __init__(self, config: dict):
        self.config = config
        self.reset_timeout = float(config.get("reset_timeout", 10.0))
        if self.reset_timeout <= 0:
            raise ValueError("reset_timeout must be > 0")
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._prefetched_replies: deque[str] = deque()
        self._reset_response_policies = self.build_reset_response_policies()
        self.logger = get_logger(self._resolve_log_component()).profile("agent_io")

    def _resolve_log_component(self) -> str:
        if self.LOG_COMPONENT:
            return self.LOG_COMPONENT
        name = self.__class__.__name__
        if name.endswith("Channel"):
            name = name[: -len("Channel")]
        return f"Channel.{name}"

    async def _recv(self, message: str) -> None:
        """收到 Agent 回复，入队并打 log。"""
        # INFO 级别只记录长度，避免与终端输出重复；内容放在 DEBUG。

        self.logger.info("[recv] Agent 回复 ({} chars)", len(message))
        self.logger.debug(
            "[recv] 内容: {}",
            message[:200] + ("…" if len(message) > 200 else ""),
        )
        await self._queue.put(message)

    def _take_prefetched_reply(self) -> str | None:
        if not self._prefetched_replies:
            return None
        reply = self._prefetched_replies.popleft()
        self.logger.debug("[recv] 已交付预取回复 ({} chars)", len(reply))
        return reply

    async def _take_queue_reply(self, timeout: float | None) -> str:
        try:
            reply = await asyncio.wait_for(self._queue.get(), timeout)
            self.logger.debug("[recv] 已交付一条回复 ({} chars)", len(reply))
            return reply
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Agent reply timed out")

    def _match_reset_policy(self, reply: str) -> ResetResponsePolicy | None:
        for policy in self._reset_response_policies:
            if policy.can_absorb(reply):
                return policy
        return None

    async def wait_for_reply(self, timeout: float | None = 60.0) -> str:
        prefetched = self._take_prefetched_reply()
        if prefetched is not None:
            return prefetched
        return await self._take_queue_reply(timeout)

    def flush(self) -> None:
        self._prefetched_replies.clear()
        while not self._queue.empty():
            self._queue.get_nowait()

    def reset_command(self) -> str:
        return "/new"

    def set_runtime_identity(self, *, sender_id: str, chat_id: str) -> None:
        """Update runtime sender/chat identity for channels that need it."""
        return None

    def build_reset_response_policies(self) -> list[ResetResponsePolicy]:
        return []

    async def absorb_reset_responses(self) -> None:
        if not self._reset_response_policies:
            return

        for policy in self._reset_response_policies:
            policy.reset()

        # Reset only consumes one incoming response.
        try:
            reply = await self._take_queue_reply(timeout=self.reset_timeout)
        except asyncio.TimeoutError:
            self.logger.warning("[reset] no acknowledgement received within {:.1f}s", self.reset_timeout)
            return
        policy = self._match_reset_policy(reply)
        if policy is not None:
            self.logger.info(
                "[reset] absorb begin response: {} by {}",
                reply[:120],
                policy.describe(),
            )
            return
        self._prefetched_replies.appendleft(reply)

    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        ...

    @abstractmethod
    async def send(self, message: str) -> None:
        ...

    async def reset(self) -> None:
        self.flush()
        await self.send(self.reset_command())
        await self.absorb_reset_responses()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_):
        await self.disconnect()
