import asyncio
from typing import List, Optional

from .base import BaseChannel

DEFAULT_REPLIES = [
    "<thought>I'll check the CSV file first, then write data.json.</thought>\n"
    "Sure, I'll start converting the data now.",
    "I've created data.json with all the records. The conversion is done.",
]


class MockChannel(BaseChannel):
    LOG_COMPONENT = "Channel.Mock"

    def __init__(self, config: dict, replies: Optional[List[str]] = None):
        super().__init__(config)
        self._replies = replies or DEFAULT_REPLIES
        self._reply_idx = 0
        self._sent: List[str] = []

    async def connect(self) -> None:
        self.logger.info("Connected")

    async def disconnect(self) -> None:
        self.logger.info("Disconnected")

    async def send(self, message: str) -> None:
        self.logger.info("[send] → {}", message)
        self._sent.append(message)

        if message == "/new":
            return

        if self._reply_idx < len(self._replies):
            reply = self._replies[self._reply_idx]
            self._reply_idx += 1
        else:
            reply = "Task completed."

        await asyncio.sleep(0.05)
        await self._recv(reply)

    async def reset(self) -> None:
        self.flush()
        self._reply_idx = 0
        self._sent.clear()
        await self.send("/new")
