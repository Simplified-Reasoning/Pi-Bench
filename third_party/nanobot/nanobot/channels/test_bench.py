"""测试用 channel：连接本地测试服务，通过 HTTP 长轮询收消息、POST 发消息。"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import TestChannelConfig


class TestChannel(BaseChannel):
    """
    测试用 channel，与本地测试服务交互。

    协议约定（测试服务需实现）：
    - 收消息：GET {base_url}/poll?timeout={poll_timeout}
      长轮询，返回 JSON:
      { "messages": [ { "sender_id", "chat_id", "content", "media"?, "meta"?: {} } ] }
    - 发消息：POST {base_url}/send
      body JSON: { "chat_id", "content", "media"?, "meta"?: {} }

    可通过 name 参数复用为多个连接（如 test / test_bench），
    分别连不同 base_url。
    """

    name = "test"

    def __init__(
        self,
        config: TestChannelConfig,
        bus: MessageBus,
        *,
        name: str | None = None,
    ):
        super().__init__(config, bus)
        self.config: TestChannelConfig = config
        self._http: httpx.AsyncClient | None = None
        if name is not None:
            self.name = name

    def _base(self) -> str:
        return self.config.base_url.rstrip("/")

    async def start(self) -> None:
        """启动 channel：创建 HTTP 客户端并开始长轮询循环。"""
        self._running = True
        self._http = httpx.AsyncClient(
            timeout=float(self.config.poll_timeout + 5),
            trust_env=False,  # 不走系统代理，避免 localhost 被代理成 503
        )
        logger.info(
            "Test channel started, polling {} (timeout={}s)",
            self._base(),
            self.config.poll_timeout,
        )
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Test channel poll error: {}", e)
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """停止 channel 并释放资源。"""
        self._running = False
        if self._http:
            await self._http.aclose()
            self._http = None
        logger.info("Test channel stopped")

    async def _poll_once(self) -> None:
        """执行一次长轮询，将收到的消息交给 bus。"""
        try:
            if not self._http:
                return
            url = f"{self._base()}/poll"
            params = {"timeout": self.config.poll_timeout}
            response = await self._http.get(url, params=params)
            if not response.is_success:
                # logger.warning(
                #     "Test channel /poll returned {}: {}",
                #     response.status_code,
                #     response.text[:200],
                # )
                return
            data = response.json() if response.content else {}
            if not isinstance(data, dict):
                return
            messages = data.get("messages")
            if not isinstance(messages, list):
                return
            for item in messages:
                if not isinstance(item, dict):
                    continue
                sender_id = str(item.get("sender_id", ""))
                chat_id = str(item.get("chat_id", ""))
                content = str(item.get("content", ""))
                media = item.get("media")
                if isinstance(media, list):
                    media = [str(x) for x in media]
                else:
                    media = []
                meta = item.get("meta")
                if not isinstance(meta, dict):
                    meta = {}
                meta["source"] = "test_channel"
                if not sender_id and not content:
                    continue
                await self._handle_message(
                    sender_id=sender_id or "anonymous",
                    chat_id=chat_id or "default",
                    content=content or "[empty message]",
                    media=media or None,
                    metadata=meta,
                )
        finally:
            if self._running:
                await asyncio.sleep(1)

    async def send(self, msg: OutboundMessage) -> None:

        if not self._http:
            logger.warning("Test channel HTTP client not running")
            return
        url = f"{self._base()}/send"
        payload: dict[str, Any] = {
            "chat_id": msg.chat_id,
            "content": msg.content or "",
            "media": msg.media or [],
            "meta": msg.metadata or {},
        }
        try:
            response = await self._http.post(url, json=payload)
            if not response.is_success:
                logger.warning(
                    "Test channel /send returned {}: {}",
                    response.status_code,
                    response.text[:200],
                )
        except Exception as e:
            logger.error("Test channel send error: {}", e)
