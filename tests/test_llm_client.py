from __future__ import annotations

import asyncio
import io
import urllib.error
from typing import Any

import pytest

from src.llm.llm_client import LLMClient, LLMResponseError


class FakeLLMClient(LLMClient):
    def __init__(self, responses: list[Any], **kwargs: Any) -> None:
        super().__init__(
            model="good-model",
            base_url="https://llm.example/v1",
            api_key="test-key",
            temperature=0.0,
            max_retries=3,
            **kwargs,
        )
        self.responses = list(responses)
        self.attempts = 0
        self.payloads: list[dict[str, Any]] = []

    async def _post_json_async(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        _ = url, headers
        self.attempts += 1
        self.payloads.append(dict(payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def _retry_delay_seconds(self, attempt: int) -> float:
        _ = attempt
        return 0.0


def _success(content: str = "ok") -> dict[str, Any]:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
    }


def _http_error(status: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://llm.example/v1/chat/completions",
        code=status,
        msg="error",
        hdrs={},
        fp=io.BytesIO(b'{"error":"bad"}'),
    )


def test_chat_keeps_core_payload_fields_under_explicit_control() -> None:
    client = FakeLLMClient(
        [_success("done")],
        extra_kwargs={"model": "bad-model", "messages": [], "temperature": 1.0, "top_p": 0.5},
    )

    response = asyncio.run(
        client.chat(
            [{"role": "user", "content": "hello"}],
            temperature=0.2,
            model="request-bad-model",
        )
    )

    assert response.content == "done"
    assert client.payloads[0]["model"] == "good-model"
    assert client.payloads[0]["messages"] == [{"role": "user", "content": "hello"}]
    assert client.payloads[0]["temperature"] == 0.2
    assert client.payloads[0]["top_p"] == 0.5


def test_chat_retries_retryable_http_status() -> None:
    client = FakeLLMClient([_http_error(429), _success("after-retry")])

    response = asyncio.run(client.chat([{"role": "user", "content": "hello"}]))

    assert response.content == "after-retry"
    assert client.attempts == 2


def test_chat_does_not_retry_non_retryable_http_status() -> None:
    client = FakeLLMClient([_http_error(400), _success("should-not-run")])

    with pytest.raises(urllib.error.HTTPError):
        asyncio.run(client.chat([{"role": "user", "content": "hello"}]))

    assert client.attempts == 1


def test_chat_invalid_response_fails_without_retry() -> None:
    client = FakeLLMClient([{"choices": [{"message": {}}]}, _success("should-not-run")])

    with pytest.raises(LLMResponseError, match="content is required"):
        asyncio.run(client.chat([{"role": "user", "content": "hello"}]))

    assert client.attempts == 1
