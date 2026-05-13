#!/usr/bin/env python3
"""
本地测试服务示例，供 nanobot test channel 连接使用。

协议：
- GET /poll?timeout=30  长轮询，返回 messages 数组，每条可含 meta
- POST /send            body: chat_id, content, media?, meta?，接收 bot 回复
- GET /sent?after=N[&chat_id=xxx] 查询回复列表；可按 chat_id 过滤
- POST /inject          body: sender_id, chat_id, content, media?, meta?

运行：python scripts/test_server.py
默认：http://localhost:9999

为 bench 单独一路：可再起一个实例并指定端口，例如：
  PORT=9998 python scripts/test_server.py
  或  python scripts/test_server.py 9998
在 config 中启用 channels.testBench.enabled 并设置 baseUrl 为 http://localhost:9998。
"""

import json
import logging
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

QUEUE: deque = deque()
SENT: list = []
LOGGER = logging.getLogger("test_server")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_event(event: str, **fields: object) -> None:
    parts = [f"event={event}"]
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).strip()
        if text == "":
            continue
        text = text.replace("\n", " ").replace("\r", " ")
        parts.append(f"{key}={text}")
    LOGGER.info(" ".join(parts))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path.startswith("/poll"):
            self._handle_poll()
            return
        if self.path == "/sent" or self.path.startswith("/sent?"):
            self._handle_sent()
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/send" or self.path == "/send/":
            self._handle_send()
            return
        if self.path == "/inject" or self.path == "/inject/":
            self._handle_inject()
            return
        self.send_response(404)
        self.end_headers()

    def _json_response(self, payload: dict) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(body)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
        return {}

    @staticmethod
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _handle_poll(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        timeout = self._parse_int(qs.get("timeout", ["30"])[0], 30)
        timeout = min(max(1, timeout), 60)
        messages = []
        try:
            messages.append(QUEUE.popleft())
        except IndexError:
            pass
        sender_id = str((messages[0] or {}).get("sender_id", "")) if messages else ""
        chat_id = str((messages[0] or {}).get("chat_id", "")) if messages else ""
        log_event(
            "poll",
            got=len(messages),
            sender_id=sender_id,
            chat_id=chat_id,
            queue=len(QUEUE),
        )
        self._json_response({"messages": messages})

    def _handle_sent(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        after = self._parse_int(qs.get("after", ["-1"])[0], -1)
        chat_id = (qs.get("chat_id", [""])[0] or "").strip()

        indexed = list(enumerate(SENT))
        if after >= 0:
            indexed = [item for item in indexed if item[0] > after]
        if chat_id:
            indexed = [
                item for item in indexed
                if str((item[1] or {}).get("chat_id", "")) == chat_id
            ]
        subset = [item[1] for item in indexed]
        log_event(
            "sent_query",
            after=after,
            chat_id=chat_id,
            returned=len(subset),
            total=len(SENT),
        )

        self._json_response({
            "sent": subset,
            "count": len(SENT),
        })

    def _handle_send(self) -> None:
        data = self._read_json_body()
        if data:
            SENT.append(data)
            log_event(
                "send",
                chat_id=str(data.get("chat_id", "")),
                len=len(str(data.get("content", ""))),
                progress=bool((data.get("meta") or {}).get("_progress")),
                total=len(SENT),
            )
        self._json_response({"ok": True})

    def _handle_inject(self) -> None:
        data = self._read_json_body()
        message = {
            "sender_id": data.get("sender_id", "test_user"),
            "chat_id": data.get("chat_id", "test_chat"),
            "content": data.get("content", "hello"),
            "media": data.get("media", []),
            "meta": data.get("meta") if isinstance(
                data.get("meta"), dict) else {},
        }
        QUEUE.append(message)
        log_event(
            "inject",
            sender_id=str(message.get("sender_id", "")),
            chat_id=str(message.get("chat_id", "")),
            len=len(str(message.get("content", ""))),
            queue=len(QUEUE),
        )
        self._json_response({"ok": True})


def main():
    import os
    import sys
    setup_logging()
    port = 9999
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    elif os.environ.get("PORT"):
        try:
            port = int(os.environ["PORT"])
        except ValueError:
            pass
    host = "0.0.0.0"
    server = HTTPServer((host, port), Handler)
    log_event(
        "server_start",
        host=host,
        port=port,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
