from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import List, Dict, Any
from ..utils import get_logger

logger = get_logger("Bench.LLMClient")
_RETRY_DELAYS_SECONDS = (1.0, 4.0, 16.0, 64.0, 128.0, 256.0, 512.0)


def _retry_delay_seconds(retry_number: int) -> float:
    if retry_number < 1:
        raise ValueError("retry_number must be >= 1")
    return _RETRY_DELAYS_SECONDS[min(retry_number - 1, len(_RETRY_DELAYS_SECONDS) - 1)]


class Budget:
    def __init__(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0, user_turns: int = 0):
        self.input_tokens = int(input_tokens)
        self.output_tokens = int(output_tokens)
        self.total_tokens = int(total_tokens)
        self.user_turns = int(user_turns)

    def add(self, other: "Budget"):
        self.input_tokens += int(other.input_tokens)
        self.output_tokens += int(other.output_tokens)
        self.total_tokens += int(other.total_tokens)
        self.user_turns += int(other.user_turns)

    def add_user_turn(self, count: int = 1):
        self.user_turns += int(count)

    def used(self, user_turn_cost: int) -> int:
        return self.output_tokens + (self.user_turns * int(user_turn_cost))

    def exceeded(self, token_budget: int, user_turn_cost: int) -> bool:
        token_budget = int(token_budget)
        return token_budget > 0 and self.used(user_turn_cost) >= token_budget

    def snapshot(self, token_budget: int, user_turn_cost: int) -> Dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "user_turns": self.user_turns,
            "token_budget": int(token_budget),
            "user_turn_cost": int(user_turn_cost),
            "used": self.used(user_turn_cost),
        }


class LLMResponse:
    def __init__(self, content: str, input_tokens: int, output_tokens: int, total_tokens: int):
        self.content = content
        self.budget = Budget(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )


class LLMResponseError(ValueError):
    """Raised when the provider returns a syntactically invalid chat response."""


class LLMClient:
    """Minimal OpenAI-compatible async client with retry/backoff."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str | None = None,
        temperature: float,
        max_retries: int = 16,
        backoff_base: float = 1.0,
        backoff_factor: float = 2.0,
        retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
        request_timeout: float = 60.0,
        max_concurrency: int = 1,
        extra_kwargs: Dict[str, Any] | None = None,
        **payload_kwargs: Any,
    ):
        self.api_key = str(api_key or "").strip()
        if not self.api_key:
            raise RuntimeError("LLM api_key is required")
        self.base_url = str(base_url).strip().rstrip("/")
        if not self.base_url:
            raise ValueError("base_url is required")
        self.model = str(model).strip()
        if not self.model:
            raise ValueError("model is required")
        self.default_temperature = float(temperature)
        self.max_retries = int(max_retries)
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        self.backoff_base = float(backoff_base)
        if self.backoff_base <= 0:
            raise ValueError("backoff_base must be > 0")
        self.backoff_factor = float(backoff_factor)
        if self.backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")
        self.retry_statuses = tuple(int(status) for status in retry_statuses)
        self.request_timeout = float(request_timeout)
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be > 0")
        self.max_concurrency = int(max_concurrency)
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self.payload_kwargs: Dict[str, Any] = {}
        self.payload_kwargs.update(payload_kwargs)
        if extra_kwargs is not None:
            if not isinstance(extra_kwargs, dict):
                raise ValueError("extra_kwargs must be a mapping")
            self.payload_kwargs.update(extra_kwargs)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float | None = None,
        **request_kwargs: Any,
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.default_temperature if temperature is None else float(temperature),
        }
        payload.update(self.payload_kwargs)
        payload.update(request_kwargs)
        # Keep core fields under explicit control.
        payload["model"] = self.model
        payload["messages"] = messages
        payload["temperature"] = self.default_temperature if temperature is None else float(temperature)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return await self._chat_with_retries(url=url, payload=payload, headers=headers)

    async def _chat_with_retries(
        self,
        *,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> LLMResponse:
        attempt = 0
        while True:
            attempt += 1
            try:
                data = await self._post_json_async(url, payload, headers)
                return self._parse_chat_response(data)
            except LLMResponseError:
                logger.exception("LLM response parsing failed: url={}", url)
                raise
            except urllib.error.HTTPError as exc:
                if not self._should_retry_http_error(exc):
                    raise
                self._log_retry(attempt=attempt, url=url, exc=exc)
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self._retry_delay_seconds(attempt))
            except Exception as exc:
                self._log_retry(attempt=attempt, url=url, exc=exc)
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self._retry_delay_seconds(attempt))

    def _log_retry(self, *, attempt: int, url: str, exc: Exception) -> None:
        logger.warning(
            "LLM request failed: attempt={}/{} type={} url={} error={}",
            attempt,
            self.max_retries,
            type(exc).__name__,
            url,
            str(exc) or "(no detail)",
        )

    def _should_retry_http_error(self, exc: urllib.error.HTTPError) -> bool:
        return int(getattr(exc, "code", 0) or 0) in self.retry_statuses

    def _retry_delay_seconds(self, attempt: int) -> float:
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        configured = self.backoff_base * (self.backoff_factor ** (attempt - 1))
        legacy_cap = _retry_delay_seconds(attempt)
        return min(configured, legacy_cap)

    def _parse_chat_response(self, data: Dict[str, Any]) -> LLMResponse:
        if not isinstance(data, dict):
            raise LLMResponseError("LLM response must be a JSON object")
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMResponseError("LLM response missing choices[0]")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMResponseError("LLM response choices[0] must be an object")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMResponseError("LLM response choices[0].message must be an object")
        content = message.get("content")
        if content is None:
            raise LLMResponseError("LLM response choices[0].message.content is required")
        if not isinstance(content, str):
            raise LLMResponseError("LLM response choices[0].message.content must be a string")
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            raise LLMResponseError("LLM response usage must be an object when present")
        return LLMResponse(
            content=content,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        )

    async def _post_json_async(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        async with self._semaphore:
            return await asyncio.to_thread(self._post_json, url, payload, headers)

    def _post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                raw = resp.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise LLMResponseError("LLM response body is not valid JSON") from exc
            if not isinstance(data, dict):
                raise LLMResponseError("LLM response body must be a JSON object")
            return data
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                raw = exc.read()
                detail = raw.decode("utf-8", errors="ignore")[:300]
            except Exception:
                detail = ""
            logger.error(
                "LLM HTTPError: status={} url={} detail={}",
                getattr(exc, "code", "unknown"),
                url,
                detail or "(no body)",
            )
            raise
