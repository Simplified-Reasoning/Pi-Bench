"""
Test channel：连接 nanobot 的 test_server，通过 HTTP 与 nanobot 对话。

协议（与 nanobot test_server.py 一致）：
- POST /inject  注入用户消息 -> nanobot 通过 /poll 拉取并处理
- GET /sent?after=N[&chat_id=xxx]  轮询 agent 回复列表（按 chat_id 隔离任务回复）；
  若 meta._progress=True 则暂存 content，
  等收到非 progress 的条目时合并后一次 recv，供 wait_for_reply 使用。

前置：1) 启动 nanobot test_server  2) 启动 nanobot 并启用 test channel 连同一 server
"""
import asyncio
from typing import Callable, Optional

import httpx

from .base import BaseChannel
from .reset_policy import ExactMatchResetPolicy, RegexResetPolicy


class TestChannel(BaseChannel):
    """通过 nanobot test_server 与 nanobot agent 对话的 channel。"""
    LOG_COMPONENT = "Channel.Test"
    RESET_ACK_MESSAGE = "New session started"

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = (config.get("base_url")
                         or "http://localhost:9999").rstrip("/")
        self.sender_id = ""
        self.chat_id = ""
        self.poll_interval = float(config.get("poll_interval", 1.0))
        self._progress_callback: Optional[Callable[[str], None]] = config.get(
            "progress_callback")
        self._http: Optional[httpx.AsyncClient] = None
        self._last_sent_index: int = -1
        self._poll_task: Optional[asyncio.Task] = None
        self._running = False
        self._progress_buffer: list[str] = []
        self._last_identity: tuple[str, str] = ("", "")

    def set_runtime_identity(self, *, sender_id: str, chat_id: str) -> None:
        next_sender, next_chat = self._normalize_identity(sender_id, chat_id)
        next_identity = (next_sender, next_chat)
        if next_identity != self._last_identity:
            self._progress_buffer.clear()
            self._last_identity = next_identity
            self.logger.info(
                "runtime identity switched sender_id={} chat_id={}",
                next_sender or "-",
                next_chat or "-",
            )
        self.sender_id = next_sender
        self.chat_id = next_chat

    @staticmethod
    def _normalize_identity(sender_id: str, chat_id: str) -> tuple[str, str]:
        return str(sender_id or "").strip(), str(chat_id or "").strip()

    async def connect(self) -> None:
        self._http = httpx.AsyncClient(
            timeout=30.0,
            trust_env=False,
        )
        self._running = True

        try:
            r = await self._http.get(f"{self.base_url}/sent",
                                     params={"after": -1})
            if r.is_success and r.json():
                self._last_sent_index = r.json().get("count", 0) - 1
        except Exception as e:
            self.logger.warning("获取 sent 初始状态失败: {}", e)
        self._poll_task = asyncio.create_task(self._poll_sent_loop())
        self.logger.info("已连接 {}", self.base_url)

    async def disconnect(self) -> None:
        self._running = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        self._progress_buffer.clear()
        if self._http:
            await self._http.aclose()
            self._http = None
        self.logger.info("已断开")

    async def _poll_sent_loop(self) -> None:
        """轮询 /sent，将新回复推入 _queue。"""
        while self._running and self._http:
            try:
                r = await self._http.get(
                    f"{self.base_url}/sent",
                    params=self._build_sent_params(),
                )
                if not r.is_success:
                    await asyncio.sleep(self.poll_interval)
                    continue
                data = r.json() or {}
                sent = data.get("sent") or []
                count = data.get("count", 0)
                for item in sent:
                    await self._handle_sent_item(item)
                self._last_sent_index = count - 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.debug("poll sent error: {}", e)
            await asyncio.sleep(self.poll_interval)

    def _build_sent_params(self) -> dict:
        params = {"after": self._last_sent_index}
        if self.chat_id:
            params["chat_id"] = self.chat_id
        return params

    def _is_runtime_target(self, item: dict) -> bool:
        item_chat = str(item.get("chat_id", "")).strip()
        if self.chat_id and item_chat and item_chat != self.chat_id:
            self.logger.debug(
                "drop reply by chat_id mismatch expected={} actual={}",
                self.chat_id,
                item_chat,
            )
            return False
        return True

    async def _handle_sent_item(self, item: dict) -> None:
        if not isinstance(item, dict):
            return
        if not self._is_runtime_target(item):
            return
        content = str(item.get("content", ""))
        meta = item.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        if meta.get("_progress") is True:
            self._handle_progress_content(content)
            return
        await self._handle_final_content(content)

    def _handle_progress_content(self, content: str) -> None:
        if not content:
            return
        self._progress_buffer.append(content)
        if self._progress_callback:
            self._progress_callback(content)
            return
        self.logger.info("[thinking] {}", content.rstrip())

    async def _handle_final_content(self, content: str) -> None:
        if not self._progress_buffer and not content:
            return
        full = "".join(self._progress_buffer) + content
        self._progress_buffer.clear()
        if full:
            await self._recv(full)

    async def send(self, message: str) -> None:
        if not self._http:
            self.logger.warning("未连接，无法发送")
            return
        sender_id = self.sender_id or "unknown_user"
        chat_id = self.chat_id or "unknown_task"
        payload = {
            "sender_id": sender_id,
            "chat_id": chat_id,
            "content": message,
            "media": [],
            "meta": {},
        }
        try:
            r = await self._http.post(f"{self.base_url}/inject", json=payload)
            if not r.is_success:
                self.logger.warning("inject 失败 {}: {}", r.status_code, r.text[:200])
            else:
                self.logger.info(
                    "[send] → {}",
                    message[:200] + ("…" if len(message) > 200 else ""),
                )
        except Exception as e:
            self.logger.error("inject 错误: {}", e)

    def build_reset_response_policies(self):
        policies = [
            ExactMatchResetPolicy(
                target=self.RESET_ACK_MESSAGE,
                max_absorb=int(self.config.get("reset_ack_max_absorb", 1)),
            ),
            RegexResetPolicy(
                pattern=r"(?i)\bnew session started\b[.!]?",
                max_absorb=1,
            ),
        ]
        for message in self.config.get("reset_ack_messages", []):
            policies.append(ExactMatchResetPolicy(target=str(message), max_absorb=1))
        for pattern in self.config.get("reset_ack_regexes", []):
            policies.append(RegexResetPolicy(pattern=str(pattern), max_absorb=1))
        return policies

    def flush(self) -> None:
        super().flush()
        self._progress_buffer.clear()
