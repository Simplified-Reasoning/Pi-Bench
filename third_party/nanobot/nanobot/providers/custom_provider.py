"""Direct OpenAI-compatible provider — bypasses LiteLLM."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import json_repair
from loguru import logger
from openai import AsyncOpenAI

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest

_BEDROCK_INT_MIN = -(2**31)
_BEDROCK_INT_MAX = 2**31 - 1
_MAX_ATTEMPTS = 16
_PARSE_FAILURE_LOG_DIR = Path.home() / ".nanobot" / "logs" / "custom_provider"


def _sanitize_tool_schema_for_bedrock(obj: Any) -> Any:
    """Remove oversized integer constraints in tool schemas."""
    if isinstance(obj, dict):
        result: dict[str, Any] = {}
        had_large_int_constraint = False
        for k, v in obj.items():
            if k in (
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "default",
            ):
                if isinstance(v, int) and not isinstance(v, bool):
                    if v < _BEDROCK_INT_MIN or v > _BEDROCK_INT_MAX:
                        had_large_int_constraint = True
                        continue
            if k == "enum" and isinstance(v, list):
                enum_values = []
                for item in v:
                    if isinstance(item, int) and not isinstance(item, bool):
                        if item < _BEDROCK_INT_MIN or item > _BEDROCK_INT_MAX:
                            enum_values.append(str(item))
                        else:
                            enum_values.append(item)
                    else:
                        enum_values.append(
                            _sanitize_tool_schema_for_bedrock(item))
                if enum_values:
                    result[k] = enum_values
                continue
            result[k] = _sanitize_tool_schema_for_bedrock(v)

        if had_large_int_constraint and result.get("type") == "integer":
            result = dict(result)
            result["type"] = "string"
            desc = result.get("description", "")
            if (isinstance(desc, str) and desc
                    and "pass as string" not in desc.lower()):
                result["description"] = (desc +
                                         " (large integers: pass as string)")
        return result
    if isinstance(obj, list):
        return [_sanitize_tool_schema_for_bedrock(v) for v in obj]
    if isinstance(obj, int) and not isinstance(obj, bool):
        if obj < _BEDROCK_INT_MIN or obj > _BEDROCK_INT_MAX:
            return str(obj)
    return obj


def _to_minimal_openai_parameters(schema: Any) -> dict[str, Any]:
    """Convert schema to a minimal OpenAI-compatible parameters schema."""
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}

    def _clean(node: Any) -> Any:
        if isinstance(node, dict):
            # Keep a conservative subset to avoid backend validation failures.
            kept: dict[str, Any] = {}
            node_type = node.get("type")
            if isinstance(node_type, str):
                kept["type"] = node_type

            props = node.get("properties")
            if isinstance(props, dict):
                kept["properties"] = {
                    k: _clean(v)
                    for k, v in props.items() if isinstance(k, str)
                }

            required = node.get("required")
            if isinstance(required, list):
                kept["required"] = [x for x in required if isinstance(x, str)]

            items = node.get("items")
            if items is not None:
                kept["items"] = _clean(items)

            enum = node.get("enum")
            if isinstance(enum, list) and enum:
                kept["enum"] = enum

            keys = (
                "description",
                "minimum",
                "maximum",
                "exclusiveMinimum",
                "exclusiveMaximum",
            )
            for key in keys:
                if key in node and key != "description":
                    kept[key] = node[key]
                elif (key == "description"
                      and isinstance(node.get("description"), str)):
                    kept[key] = node["description"]

            if "type" not in kept:
                # Drop unsupported unions/keywords by falling back to string.
                kept["type"] = "string"
            return kept
        if isinstance(node, list):
            return [_clean(v) for v in node]
        return node

    cleaned = _clean(schema)
    if not isinstance(cleaned, dict):
        return {"type": "object", "properties": {}}
    if cleaned.get("type") != "object":
        return {"type": "object", "properties": {}}
    if "properties" not in cleaned:
        cleaned["properties"] = {}
    return cleaned


class CustomProvider(LLMProvider):

    def __init__(
        self,
        api_key: str = "no-key",
        api_base: str = "http://localhost:8000/v1",
        default_model: str = "default",
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
        )
        self._max_attempts = _MAX_ATTEMPTS

    @staticmethod
    def _retry_delay_seconds(retry_index: int) -> int:
        """Return delay seconds before the next retry (1-based retry index)."""
        if retry_index <= 1:
            return 1
        if retry_index == 2:
            return 4
        if retry_index == 3:
            return 16
        if retry_index == 4:
            return 64
        if retry_index == 5:
            return 128
        if retry_index == 6:
            return 256
        return 512

    @staticmethod
    def _extract_status_code(error: Exception) -> int | None:
        status = getattr(error, "status_code", None)
        if isinstance(status, int):
            return status
        response = getattr(error, "response", None)
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return response_status
        return None

    @classmethod
    def _is_retryable_error(cls, error: Exception) -> bool:
        status = cls._extract_status_code(error)
        if status is not None:
            if status in {408, 429} or status >= 500:
                return True
            if 400 <= status < 500:
                return False

        if isinstance(error, (httpx.TimeoutException, httpx.TransportError, TimeoutError, ConnectionError)):
            return True

        error_type = error.__class__.__name__.lower()
        if "timeout" in error_type or "connection" in error_type:
            return True

        text = str(error).lower()
        transient_markers = (
            "timeout",
            "timed out",
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "bad gateway",
            "gateway timeout",
            "connection reset",
            "connection refused",
        )
        return any(marker in text for marker in transient_markers)

    @staticmethod
    def _response_debug_payload(response: Any) -> Any:
        if hasattr(response, "model_dump"):
            try:
                return response.model_dump(mode="json")
            except TypeError:
                return response.model_dump()

        if isinstance(response, dict):
            return response

        payload: dict[str, Any] = {
            "type": f"{type(response).__module__}.{type(response).__name__}"
        }
        for key in ("id", "model", "object", "created", "choices", "usage", "error", "router_detail"):
            if hasattr(response, key):
                payload[key] = getattr(response, key)
        if len(payload) > 1:
            return payload
        return repr(response)

    @classmethod
    def _response_debug_preview(cls, response: Any, max_chars: int = 4000) -> str:
        try:
            text = json.dumps(
                cls._response_debug_payload(response),
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            text = repr(response)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...[truncated]"

    def _save_parse_failure_payload(
        self,
        response: Any,
        error: Exception,
        attempt: int,
    ) -> Path | None:
        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attempt": attempt,
            "model": self.default_model,
            "api_base": self.api_base,
            "error": repr(error),
            "response": self._response_debug_payload(response),
        }
        try:
            _PARSE_FAILURE_LOG_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            path = _PARSE_FAILURE_LOG_DIR / f"parse_failure_{ts}_attempt_{attempt}.json"
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            return path
        except Exception as save_error:
            logger.warning("Failed to save custom provider parse payload: {}", repr(save_error))
            return None

    @staticmethod
    def _first_choice(response: Any) -> Any:
        choices = response.get("choices") if isinstance(response, dict) else getattr(response, "choices", None)
        if choices is None:
            raise ValueError("Custom provider returned invalid response: choices is None")
        if not isinstance(choices, list):
            raise ValueError(
                f"Custom provider returned invalid response: choices must be a list, got {type(choices).__name__}"
            )
        if not choices:
            raise ValueError("Custom provider returned invalid response: choices is empty")
        return choices[0]

    async def _chat_with_retry(self, kwargs: dict[str, Any]) -> LLMResponse:
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await self._client.chat.completions.create(**kwargs)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                if attempt >= self._max_attempts or not self._is_retryable_error(error):
                    raise
                delay_s = self._retry_delay_seconds(attempt)
                logger.warning(
                    "Custom provider request failed (attempt {}/{}): {}. Retrying in {}s",
                    attempt,
                    self._max_attempts,
                    repr(error),
                    delay_s,
                )
                await asyncio.sleep(delay_s)
                continue

            try:
                return self._parse(response)
            except Exception as error:
                payload_path = self._save_parse_failure_payload(response, error, attempt)
                payload_preview = self._response_debug_preview(response)
                if attempt >= self._max_attempts:
                    logger.error(
                        "Custom provider response parse failed (attempt {}/{}): {}. Debug payload saved to {}. Response preview: {}",
                        attempt,
                        self._max_attempts,
                        repr(error),
                        payload_path or "[save failed]",
                        payload_preview,
                    )
                    raise
                delay_s = self._retry_delay_seconds(attempt)
                logger.warning(
                    "Custom provider response parse failed (attempt {}/{}): {}. Debug payload saved to {}. Response preview: {}. Retrying in {}s",
                    attempt,
                    self._max_attempts,
                    repr(error),
                    payload_path or "[save failed]",
                    payload_preview,
                    delay_s,
                )
                await asyncio.sleep(delay_s)

        raise RuntimeError("unreachable")

    async def chat(self,
                   messages: list[dict[str, Any]],
                   tools: list[dict[str, Any]] | None = None,
                   model: str | None = None,
                   max_tokens: int = 4096,
                   temperature: float = 0.7,
                   reasoning_effort: str | None = None) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": self._sanitize_empty_content(messages),
            "max_tokens": max(1, max_tokens),
            "temperature": temperature,
        }
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        if tools:
            tools_sanitized = _sanitize_tool_schema_for_bedrock(tools)
            # Bedrock-compatible gateways may accept only a minimal schema subset.
            tools_minimal = []
            for tool in tools_sanitized:
                if not isinstance(tool, dict):
                    continue
                fn = tool.get("function")
                if not isinstance(fn, dict):
                    tools_minimal.append(tool)
                    continue
                fn = dict(fn)
                fn["parameters"] = _to_minimal_openai_parameters(
                    fn.get("parameters"))
                tool_copy = dict(tool)
                tool_copy["function"] = fn
                tools_minimal.append(tool_copy)
            kwargs.update(
                tools=tools_minimal,
                tool_choice="auto",
            )
        try:
            return await self._chat_with_retry(kwargs)
        except Exception as e:
            # Print full error payload to avoid outer-log truncation.
            print("[custom_provider] full exception:", repr(e))
            body = getattr(e, "body", None)
            if body is not None:
                print("[custom_provider] error body:", body)
            return LLMResponse(content=f"Error: {e}", finish_reason="error")

    def _parse(self, response: Any) -> LLMResponse:
        choice = self._first_choice(response)
        msg = choice.message
        tool_calls = [
            ToolCallRequest(id=tc.id,
                            name=tc.function.name,
                            arguments=json_repair.loads(tc.function.arguments)
                            if isinstance(tc.function.arguments, str) else
                            tc.function.arguments)
            for tc in (msg.tool_calls or [])
        ]
        u = response.usage
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage={
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
                "total_tokens": u.total_tokens
            } if u else {},
            reasoning_content=getattr(msg, "reasoning_content", None) or None,
        )

    def get_default_model(self) -> str:
        return self.default_model
