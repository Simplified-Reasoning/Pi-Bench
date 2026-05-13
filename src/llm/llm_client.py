from __future__ import annotations

import asyncio
import os
import json
import urllib.request
import urllib.error
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


class LLMClient:
    """Minimal OpenAI-compatible async client with retry/backoff."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
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
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self.base_url = str(base_url).strip().rstrip("/")
        self.model = str(model).strip()
        self.default_temperature = float(temperature)
        self.max_retries = int(max_retries)
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses
        self.request_timeout = float(request_timeout)
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
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage") or {}
                return LLMResponse(
                    content=content,
                    input_tokens=int(usage.get("prompt_tokens", 0)),
                    output_tokens=int(usage.get("completion_tokens", 0)),
                    total_tokens=int(usage.get("total_tokens", 0)),
                )
            except Exception as exc:
                logger.warning(
                    "LLM request failed: attempt={}/{} type={} url={} error={}",
                    attempt,
                    self.max_retries,
                    type(exc).__name__,
                    url,
                    str(exc) or "(no detail)",
                )
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(_retry_delay_seconds(attempt))

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
            return json.loads(raw.decode("utf-8"))
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
