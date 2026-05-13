from __future__ import annotations

import contextlib
import contextvars
import functools
import inspect
import json
import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, ParamSpec, TextIO, TypeVar

from loguru import logger as _logger

from .model_id import safe_model_id

_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}
_TRANSPARENT_SOURCE_FUNCTIONS = {
    "_llm_chat",
    "_request_intent_decisions",
    "_request_followup_decisions",
}
_SOURCE_STYLE_OPEN = "<cyan>"
_SOURCE_STYLE_CLOSE = "</cyan>"
_BRIGHT_BLUE_OPEN = "<light-blue>"
_BRIGHT_BLUE_CLOSE = "</light-blue>"


@dataclass(frozen=True)
class LogProfileStyle:
    message_open: str = ""
    message_close: str = ""


_PROFILE_STYLES = {
    "default": LogProfileStyle(),
    "hidden_intent": LogProfileStyle(
        message_open="<dim>",
        message_close="</dim>",
    ),
    "agent_io": LogProfileStyle(
        message_open=_BRIGHT_BLUE_OPEN,
        message_close=_BRIGHT_BLUE_CLOSE,
    ),
    "eval": LogProfileStyle(),
    "eval_stage": LogProfileStyle(
        message_open=_BRIGHT_BLUE_OPEN,
        message_close=_BRIGHT_BLUE_CLOSE,
    ),
    "eval_aux": LogProfileStyle(
        message_open="<dim>",
        message_close="</dim>",
    ),
    "eval_result": LogProfileStyle(
        message_open=f"<b>{_BRIGHT_BLUE_OPEN}",
        message_close=f"{_BRIGHT_BLUE_CLOSE}</b>",
    ),
}

P = ParamSpec("P")
R = TypeVar("R")


def _wrap_style(value: str, *, open_tag: str, close_tag: str) -> str:
    if not open_tag or not close_tag:
        return value
    return f"{open_tag}{value}{close_tag}"


def _format_record(record: dict) -> str:
    source = str(record["extra"].get("source") or record["name"])
    profile = str(record["extra"].get("profile") or "default")
    style = _PROFILE_STYLES.get(profile, _PROFILE_STYLES["default"])
    source_text = _wrap_style(
        source,
        open_tag=_SOURCE_STYLE_OPEN,
        close_tag=_SOURCE_STYLE_CLOSE,
    )
    message_text = _wrap_style(
        "{message}",
        open_tag=style.message_open,
        close_tag=style.message_close,
    )
    return (
        f"<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | "
        f"<level>{{level:<8}}</level> | "
        f"{source_text} - {message_text}\n{{exception}}"
    )


def _normalize_level(level: str | None) -> str:
    resolved = str(level or os.getenv("BENCH_LOG_LEVEL", "INFO")).upper()
    if resolved not in _LEVELS:
        raise ValueError(f"unsupported log level: {resolved}")
    return resolved


def _current_timestamp() -> tuple[float, str]:
    now = datetime.now()
    return time.time(), now.isoformat(timespec="seconds")


def _format_message(message: object, args: tuple, kwargs: dict) -> str:
    text = str(message)
    if not args and not kwargs:
        return text
    try:
        return text.format(*args, **kwargs)
    except Exception:
        return f"{text} | args={args!r} kwargs={kwargs!r}"


def _write_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _resolve_source() -> str:
    current = inspect.currentframe()
    frame = current.f_back if current is not None else None
    try:
        while frame is not None:
            module_name = str(frame.f_globals.get("__name__", ""))
            function_name = frame.f_code.co_name or "<module>"
            if module_name == __name__ or function_name in _TRANSPARENT_SOURCE_FUNCTIONS:
                frame = frame.f_back
                continue
            return f"{module_name}:{function_name}:{frame.f_lineno}"
        return "unknown:log:0"
    finally:
        del current


@dataclass
class TaskLogContext:
    task_id: str
    agent_id: str
    log_dir: Path
    log_path: Path
    llm_path: Path
    messages_path: Path
    message_counter: int = 0
    llm_call_counter: int = 0
    log_counter: int = 0


@dataclass
class RunLogContext:
    output_root: Path
    model_id: str
    safe_model_id: str
    user_id: str
    agent_id: str
    task_log_dirname: str
    run_dir: Path
    log_path: Path
    log_counter: int = 0


class _LoggingRuntime:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.console_level = _normalize_level(None)
        self.console_stream: TextIO = sys.stdout
        self.run_context: RunLogContext | None = None
        self._configured = False
        self._active_task: contextvars.ContextVar[TaskLogContext | None] = contextvars.ContextVar(
            "bench_active_task_log_context",
            default=None,
        )
        self._active_profile: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            "bench_active_log_profile",
            default=None,
        )

    def configure_console(self, level: str | None = None, *, stream: TextIO | None = None) -> None:
        with self._lock:
            self.console_level = _normalize_level(level)
            if stream is not None:
                self.console_stream = stream

            _logger.remove()
            _logger.add(
                self.console_stream,
                level="TRACE",
                colorize=self.console_stream.isatty(),
                backtrace=False,
                diagnose=False,
                format=_format_record,
            )
            logging.getLogger("httpx").setLevel(logging.WARNING)
            self._configured = True

    def ensure_console(self) -> None:
        if self._configured:
            return
        self.configure_console()

    def should_print(self, level: str) -> bool:
        return _LEVELS[_normalize_level(level)] >= _LEVELS[self.console_level]

    @contextlib.contextmanager
    def profile_scope(self, profile: str | None) -> Iterator[None]:
        if not profile:
            yield
            return
        token = self._active_profile.set(profile)
        try:
            yield
        finally:
            self._active_profile.reset(token)

    def current_profile(self) -> str | None:
        return self._active_profile.get()

    def bind_run(
        self,
        *,
        output_root: Path,
        model_id: str,
        user_id: str,
        agent_id: str,
        task_log_dirname: str = "history",
    ) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_id = safe_model_id(model_id)
        run_dir = output_root / safe_id / user_id / "run"
        with self._lock:
            self.run_context = RunLogContext(
                output_root=output_root,
                model_id=model_id,
                safe_model_id=safe_id,
                user_id=user_id,
                agent_id=agent_id,
                task_log_dirname=task_log_dirname,
                run_dir=run_dir,
                log_path=run_dir / f"{ts}-log.jsonl",
            )
            self._active_task.set(None)

    def clear_run(self) -> None:
        with self._lock:
            self.run_context = None
            self._active_task.set(None)
            self._active_profile.set(None)

    def activate_task(self, task_id: str, *, session_timestamp: str | None = None) -> None:
        with self._lock:
            if self.run_context is None:
                return
            ts = session_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = (
                self.run_context.output_root
                / self.run_context.safe_model_id
                / self.run_context.user_id
                / task_id
                / Path(self.run_context.task_log_dirname)
            )
            self._active_task.set(
                TaskLogContext(
                    task_id=task_id,
                    agent_id=self.run_context.agent_id,
                    log_dir=log_dir,
                    log_path=log_dir / f"{ts}-log.jsonl",
                    llm_path=log_dir / f"{ts}-user.jsonl",
                    messages_path=log_dir / f"{ts}-messages.jsonl",
                )
            )

    def complete_task(self, task_id: str | None = None) -> None:
        with self._lock:
            task = self._active_task.get()
            if task is None:
                return
            if task_id and task.task_id != task_id:
                return
            self._active_task.set(None)

    def record_message(
        self,
        *,
        role: str,
        message: str,
        metadata: dict | None = None,
    ) -> int | None:
        with self._lock:
            task = self._require_task_context()
            if task is None:
                return None
            task.message_counter += 1
            timestamp, timestamp_iso = _current_timestamp()
            entry = {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "round": task.message_counter,
                "role": role,
                "message": message,
                "chars": len(message),
                "timestamp": timestamp,
                "timestamp_iso": timestamp_iso,
            }
            if metadata:
                entry["metadata"] = metadata
            _write_jsonl(task.messages_path, entry)
            return task.message_counter

    def record_llm_call(
        self,
        *,
        component: str,
        source: str,
        prompt: str,
        response: str,
        level: str,
    ) -> None:
        with self._lock:
            task = self._require_task_context()
            if task is None:
                return
            task.llm_call_counter += 1
            timestamp, timestamp_iso = _current_timestamp()
            _write_jsonl(
                task.llm_path,
                {
                    "record_type": "llm_call",
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                    "component": component,
                    "source": source,
                    "level": _normalize_level(level),
                    "call_index": task.llm_call_counter,
                    "prompt": prompt,
                    "response": response,
                    "prompt_chars": len(prompt),
                    "response_chars": len(response),
                    "timestamp": timestamp,
                    "timestamp_iso": timestamp_iso,
                },
            )

    def record_log(
        self,
        *,
        component: str,
        source: str,
        level: str,
        message: str,
        data: dict | None = None,
        exception: str | None = None,
    ) -> None:
        with self._lock:
            target_path, metadata, entry_index = self._next_log_target()
            if target_path is None:
                return
            timestamp, timestamp_iso = _current_timestamp()
            entry = {
                "record_type": "log",
                "component": component,
                "source": source,
                "level": _normalize_level(level),
                "message": message,
                "data": data or {},
                "timestamp": timestamp,
                "timestamp_iso": timestamp_iso,
                "entry_index": entry_index,
                **metadata,
            }
            if exception:
                entry["exception"] = exception
            _write_jsonl(target_path, entry)

    def _next_log_target(self) -> tuple[Path | None, dict, int]:
        if self.run_context is None:
            return None, {}, 0

        task = self._active_task.get()
        if task is not None:
            task.log_counter += 1
            return (
                task.log_path,
                {
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                },
                task.log_counter,
            )

        self.run_context.log_counter += 1
        return (
            self.run_context.log_path,
            {
                "user_id": self.run_context.user_id,
                "agent_id": self.run_context.agent_id,
            },
            self.run_context.log_counter,
        )

    def _require_task_context(self) -> TaskLogContext | None:
        if self.run_context is None:
            return None
        return self._active_task.get()


_RUNTIME = _LoggingRuntime()


class BenchLogger:
    def __init__(self, component: str, *, default_profile: str | None = None) -> None:
        self.component = component
        self.default_profile = default_profile
        self._logger = _logger.bind(component=component)

    def profile(self, profile: str) -> "BenchLogger":
        return BenchLogger(component=self.component, default_profile=str(profile).strip() or None)

    def profile_scope(self, profile: str | None = None) -> contextlib.AbstractContextManager[None]:
        return _RUNTIME.profile_scope(profile or self.default_profile)

    def debug(
        self,
        message: object,
        *args,
        persist: bool = True,
        data: dict | None = None,
        **kwargs,
    ) -> None:
        self._emit("DEBUG", message, args, kwargs, persist=persist, data=data)

    def info(
        self,
        message: object,
        *args,
        persist: bool = True,
        data: dict | None = None,
        **kwargs,
    ) -> None:
        self._emit("INFO", message, args, kwargs, persist=persist, data=data)

    def warning(
        self,
        message: object,
        *args,
        persist: bool = True,
        data: dict | None = None,
        **kwargs,
    ) -> None:
        self._emit("WARNING", message, args, kwargs, persist=persist, data=data)

    def error(
        self,
        message: object,
        *args,
        persist: bool = True,
        data: dict | None = None,
        **kwargs,
    ) -> None:
        self._emit("ERROR", message, args, kwargs, persist=persist, data=data)

    def exception(
        self,
        message: object,
        *args,
        persist: bool = True,
        data: dict | None = None,
        **kwargs,
    ) -> None:
        self._emit(
            "ERROR",
            message,
            args,
            kwargs,
            persist=persist,
            data=data,
            include_exception=True,
        )

    def block(
        self,
        title: str,
        *lines: object,
        level: str = "INFO",
        persist: bool = True,
        data: dict | None = None,
    ) -> None:
        rendered = "\n".join([title, *[str(line) for line in lines if str(line).strip()]])
        self._emit(level, rendered, (), {}, persist=persist, data=data)

    def llm_call(
        self,
        *,
        prompt: str,
        response: str,
        level: str = "DEBUG",
    ) -> None:
        normalized = _normalize_level(level)
        source = _resolve_source()
        profile = self._resolve_profile()
        if _RUNTIME.should_print(normalized):
            self._logger.bind(source=source, profile=profile).log(
                normalized,
                "[llm] prompt_chars={} response_chars={}",
                len(prompt),
                len(response),
            )
        _RUNTIME.record_llm_call(
            component=self.component,
            source=source,
            prompt=prompt,
            response=response,
            level=normalized,
        )

    def _emit(
        self,
        level: str,
        message: object,
        args: tuple,
        kwargs: dict,
        *,
        persist: bool,
        data: dict | None,
        include_exception: bool = False,
    ) -> None:
        normalized = _normalize_level(level)
        rendered = _format_message(message, args, kwargs)
        exception_text = traceback.format_exc() if include_exception else None
        source = _resolve_source()
        profile = self._resolve_profile()
        if _RUNTIME.should_print(normalized):
            bound_logger = self._logger.bind(source=source, profile=profile)
            if include_exception:
                bound_logger.exception(message, *args, **kwargs)
            else:
                bound_logger.log(normalized, message, *args, **kwargs)
        if not persist:
            return
        _RUNTIME.record_log(
            component=self.component,
            source=source,
            level=normalized,
            message=rendered,
            data=data,
            exception=exception_text if exception_text != "NoneType: None\n" else None,
        )

    def _resolve_profile(self) -> str:
        return _RUNTIME.current_profile() or self.default_profile or "default"


def configure_logging(level: str | None = None, *, stream: TextIO | None = None) -> None:
    _RUNTIME.configure_console(level, stream=stream)


def get_logger(component: str) -> BenchLogger:
    _RUNTIME.ensure_console()
    return BenchLogger(component=component)


def bind_log_run(
    *,
    output_root: str | Path,
    model_id: str,
    user_id: str,
    agent_id: str,
    task_log_dirname: str = "history",
) -> None:
    _RUNTIME.bind_run(
        output_root=Path(output_root),
        model_id=str(model_id),
        user_id=str(user_id),
        agent_id=str(agent_id),
        task_log_dirname=str(task_log_dirname),
    )


def clear_log_run() -> None:
    _RUNTIME.clear_run()


def activate_task_logging(task_id: str, *, session_timestamp: str | None = None) -> None:
    _RUNTIME.activate_task(task_id, session_timestamp=session_timestamp)


def complete_task_logging(task_id: str | None = None) -> None:
    _RUNTIME.complete_task(task_id)


def record_history_message(
    *,
    role: str,
    message: str,
    metadata: dict | None = None,
) -> int | None:
    return _RUNTIME.record_message(role=role, message=message, metadata=metadata)


def reset_logging_state(*, level: str | None = None, stream: TextIO | None = None) -> None:
    _RUNTIME.clear_run()
    _RUNTIME._configured = False
    configure_logging(level=level, stream=stream)


def log_profile(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    profile_name = str(name).strip() or "default"

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with _RUNTIME.profile_scope(profile_name):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with _RUNTIME.profile_scope(profile_name):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator
