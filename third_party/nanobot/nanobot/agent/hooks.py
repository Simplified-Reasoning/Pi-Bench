from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import json
from datetime import datetime
from pathlib import Path

from loguru import logger


@dataclass
class TurnStartRecord:
    """本轮开始时的记录（仅输入与上下文）。"""
    session_key: str
    channel: str
    chat_id: str
    input: str  # 用户本轮完整输入
    sender_id: str = ""


@dataclass
class LLMStep:
    """单次 LLM 调用的请求与响应。"""
    iteration: int
    request_messages: list[dict[str, Any]]  # 发给模型的完整 messages
    response_content: str  # 模型返回的 content（含 think 等）
    response_content_stripped: str | None  # 去掉 <think> 后的内容
    tool_calls: list[dict[str, Any]]  # [{"id", "name", "arguments"}, ...]
    reasoning_content: str | None = None


@dataclass
class LLMRequestRecord:
    """单次 LLM 请求（调用前）。用于 on_llm_request。"""
    iteration: int
    request_messages: list[dict[str, Any]]
    model: str
    temperature: float
    max_tokens: int


@dataclass
class ToolCallRecord:
    """单次工具调用（执行前）。用于 on_tool_call。"""
    iteration: int
    tool_call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResultRecord:
    """单次工具调用结果（执行后）。用于 on_tool_result。"""
    iteration: int
    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    result: str


@dataclass
class ToolStep:
    """单次工具调用的入参和结果（用于 TurnRecord.tool_steps）。"""
    name: str
    arguments: dict[str, Any]
    result: str  # 完整工具返回


@dataclass
class TurnRecord:
    """一轮对话的完整运行记录（输入、输出、中间步骤）。"""
    session_key: str
    channel: str
    chat_id: str
    input: str  # 用户本轮完整输入
    sender_id: str = ""
    model: str = ""
    session_started_at: str = ""

    # 完整消息列表（本轮结束后的 messages，含 history + 本轮的 assistant/tool）
    messages: list[dict[str, Any]] = field(default_factory=list)

    # 步骤序列：交替的 LLM 与 Tool 步骤，按时间顺序
    llm_steps: list[LLMStep] = field(default_factory=list)
    tool_steps: list[ToolStep] = field(default_factory=list)

    # 本轮最终回复（纯文本，已 strip think）
    output: str | None = None

    iterations: int = 0
    tools_used: list[str] = field(default_factory=list)  # 工具名列表

    # 若处理过程中抛错，记录在此
    error: str | None = None

    def to_dict(self, compact: bool = False) -> dict[str, Any]:
        """可序列化为 JSON 的字典（便于持久化或上报）。

        compact=False：包含完整 messages；llm_steps 不含 request_messages，仅含 request_message_count 避免重复。
        compact=True：不包含 messages，仅含 message_count，进一步减少与 llm_steps/tool_steps 的重复。
        """
        payload: dict[str, Any] = {
            "session_key":
            self.session_key,
            "session_started_at":
            self.session_started_at,
            "channel":
            self.channel,
            "chat_id":
            self.chat_id,
            "input":
            self.input,
            "sender_id":
            self.sender_id,
            "model":
            self.model,
            "llm_steps": [{
                "iteration": s.iteration,
                "request_message_count": len(s.request_messages),
                "response_content": s.response_content,
                "response_content_stripped": s.response_content_stripped,
                "tool_calls": s.tool_calls,
                "reasoning_content": s.reasoning_content,
            } for s in self.llm_steps],
            "tool_steps": [{
                "name": s.name,
                "arguments": s.arguments,
                "result": s.result
            } for s in self.tool_steps],
            "output":
            self.output,
            "iterations":
            self.iterations,
            "tools_used":
            self.tools_used,
            "error":
            self.error,
        }
        if compact:
            payload["message_count"] = len(self.messages)
        else:
            payload["messages"] = self.messages
        return payload


# ---------------------------------------------------------------------------
# Hook 协议
# ---------------------------------------------------------------------------


@runtime_checkable
class AgentHook(Protocol):
    """Agent 运行过程的钩子接口。实现需要的方法即可，未实现的方法不会被调用。"""

    async def on_turn_start(self, record: TurnStartRecord) -> None:
        """本轮开始（收到用户输入、即将进入 agent 循环）."""
        ...

    async def on_llm_request(self, record: LLMRequestRecord) -> None:
        """单步开始：即将调用 LLM（请求体：messages、model 等）。"""
        ...

    async def on_llm_response(self, record: LLMStep) -> None:
        """单步 LLM 返回：已拿到响应（content、tool_calls 等）。"""
        ...

    async def on_tool_call(self, record: ToolCallRecord) -> None:
        """即将执行某次工具调用（name、arguments）。"""
        ...

    async def on_tool_result(self, record: ToolResultRecord) -> None:
        """某次工具调用已返回（name、arguments、result）。"""
        ...

    async def on_turn_end(self, record: TurnRecord) -> None:
        """本轮结束（完整记录：输入、消息、每步 LLM/工具、最终回复）。"""
        ...

    async def on_error(self, channel: str, chat_id: str, error: str) -> None:
        """处理消息时发生异常."""
        ...


class LogHook(AgentHook):
    """将运行过程输出到 loguru 的 Hook。可配置日志级别与是否输出详细内容。"""

    def __init__(
        self,
        level: str = "INFO",
        log_turn: bool = True,
        log_llm: bool = True,
        log_tool: bool = True,
        content_max_len: int = 200,
    ):
        """
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR）
            log_turn: 是否记录 turn_start / turn_end
            log_llm: 是否记录 llm_request / llm_response
            log_tool: 是否记录 tool_call / tool_result
            content_max_len: 日志中 content/result 等字符串的最大长度，超出截断
        """
        self._level = level.upper()
        self._log_turn = log_turn
        self._log_llm = log_llm
        self._log_tool = log_tool
        self._content_max_len = content_max_len

    def _truncate(self, s: str) -> str:
        if not s or len(s) <= self._content_max_len:
            return s or ""
        return s[:self._content_max_len] + "…"

    def _log(self, msg: str, *args: object, **kwargs: object) -> None:
        getattr(logger, self._level.lower())(msg, *args, **kwargs)

    async def on_turn_start(self, record: TurnStartRecord) -> None:
        if not self._log_turn:
            return
        self._log(
            "turn_start session={} channel={} sender_id={}, chat_id={} input={}",
            record.session_key,
            record.channel,
            record.sender_id,
            record.chat_id,
            self._truncate(record.input),
        )

    async def on_llm_request(self, record: LLMRequestRecord) -> None:
        if not self._log_llm:
            return
        self._log(
            "llm_request step={} model={} messages={}",
            record.iteration,
            record.model,
            len(record.request_messages),
        )

    async def on_llm_response(self, record: LLMStep) -> None:
        if not self._log_llm:
            return
        tool_names = [t.get("name", "") for t in record.tool_calls]
        self._log(
            "llm_response step={} content_len={} tool_calls={}",
            record.iteration,
            len(record.response_content or ""),
            tool_names,
        )
        if record.response_content_stripped:
            self._log(
                "  content: {}",
                self._truncate(record.response_content_stripped),
            )

    async def on_tool_call(self, record: ToolCallRecord) -> None:
        if not self._log_tool:
            return
        self._log(
            "tool_call step={} name={} arguments={}",
            record.iteration,
            record.name,
            record.arguments,
        )

    async def on_tool_result(self, record: ToolResultRecord) -> None:
        if not self._log_tool:
            return
        self._log(
            "tool_result step={} name={} result_len={}",
            record.iteration,
            record.name,
            len(record.result),
        )
        if record.result:
            self._log("  result: {}", self._truncate(record.result))

    async def on_turn_end(self, record: TurnRecord) -> None:
        if not self._log_turn:
            return
        self._log(
            "turn_end session={} sender_id={} chat_id={} iterations={} tools_used={} output_len={}",
            record.session_key,
            record.sender_id,
            record.chat_id,
            record.iterations,
            record.tools_used,
            len(record.output or ""),
        )
        if record.output:
            self._log("  output: {}", self._truncate(record.output))

    async def on_error(self, channel: str, chat_id: str, error: str) -> None:
        logger.error("hook_error channel={} chat_id={} error={}", channel,
                     chat_id, error)


class JsonStorageHook(AgentHook):
    """将每轮完整记录以 JSON 写入文件的 Hook；按 model/sender/chat 分子目录存储。"""

    def __init__(
        self,
        storage_dir: str | Path,
        filename_pattern: str = "turn_{timestamp}.json",
        indent: int = 2,
        ensure_ascii: bool = False,
    ):
        """
        Args:
            storage_dir: 存储根目录，不存在时会创建；每个 sender/chat 在其下占子目录
            filename_pattern: 单轮文件名格式，支持 {timestamp}、{session_key}（冒号会替换为 _）
            indent: JSON 缩进，0 表示紧凑
            ensure_ascii: 是否转义非 ASCII 字符
        """
        self._dir = Path(storage_dir).expanduser()
        self._pattern = filename_pattern
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    @staticmethod
    def _format_dir_timestamp(ts: datetime | None) -> str:
        return (ts or datetime.now()).strftime("%Y%m%d_%H%M%S")

    def _path_for_turn(self, record: TurnRecord) -> Path:
        """按 model/sender/chat/session 分子目录存储 turn 文件。"""

        safe_model = (record.model or "unknown_model").replace("/", "_")
        safe_sender = (record.sender_id or "unknown_sender").replace("/", "_")
        safe_chat = (record.chat_id or "unknown_chat").replace("/", "_")
        session_started_at = record.session_started_at or self._format_dir_timestamp(None)
        target_dir = self._dir / safe_model / safe_sender / safe_chat / session_started_at
        target_dir.mkdir(parents=True, exist_ok=True)
        ts = self._format_dir_timestamp(datetime.now())
        safe_key = (record.session_key or "unknown").replace(":", "_")
        name = self._pattern.format(timestamp=ts, session_key=safe_key)
        return target_dir / name

    async def on_turn_end(self, record: TurnRecord) -> None:
        path = self._path_for_turn(record)
        data = record.to_dict(compact=False)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data,
                          f,
                          ensure_ascii=self._ensure_ascii,
                          indent=self._indent if self._indent else None)
        except OSError as e:
            logger.warning("JsonStorageHook failed to write {}: {}", path, e)


async def run_hooks_async(
    hooks: list[AgentHook] | None,
    method: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """异步调用所有 hooks 的 method；未实现的方法跳过，单 hook 异常不影响其他。"""
    if not hooks:
        return
    for h in hooks:
        fn = getattr(h, method, None)
        if fn is None or not callable(fn):
            continue
        try:
            result = fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.warning("Hook {}.{} raised: {}",
                           type(h).__name__, method, e)
