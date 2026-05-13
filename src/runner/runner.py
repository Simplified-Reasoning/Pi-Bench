from __future__ import annotations

import asyncio
import time
from collections import Counter
from typing import Optional

from ..channels.base import BaseChannel
from ..utils import get_logger
from ..user_agent.base import BaseUserAgent
from .models import BenchmarkRunResult, PendingTask, TaskRunResult

logger = get_logger("Bench.Runner")


class BenchmarkRunner:
    """
    Minimal runner:
    - user agent owns task lifecycle
    - channel owns external communication
    - runner only orchestrates turns and termination states
    """

    def __init__(
        self,
        channel: BaseChannel,
        user_agent: BaseUserAgent,
        max_turns: int = 30,
        turn_timeout: float = 60.0,
    ):
        self.channel = channel
        self.user_agent = user_agent
        self.max_turns = max_turns
        self.turn_timeout = turn_timeout

    async def run(self) -> BenchmarkRunResult:
        run_started = time.monotonic()
        task_results: list[TaskRunResult] = []
        user_id = self._get_user_id()
        total_planned = len(getattr(getattr(self.user_agent, "episode", None), "task_order", []) or [])
        logger.info(
            "Benchmark started user_id={} max_turns={} turn_timeout={:.1f}s planned_tasks={}",
            user_id,
            self.max_turns,
            self.turn_timeout,
            total_planned,
            data={"planned_tasks": total_planned, "max_turns": self.max_turns},
        )

        pending_task = self._load_next_task()
        if pending_task is None:
            self._log_run_summary(task_results, run_started)
            return BenchmarkRunResult(status="COMPLETED", tasks=task_results)

        await self._reset_channel(task_id=pending_task.task_id)

        while pending_task is not None:
            result = await self._run_one_task(pending_task)
            task_results.append(result)
            await self._finish_task(result)

            if result.status == "EXITED_BY_USER":
                self._log_run_summary(task_results, run_started)
                return BenchmarkRunResult(status="EXITED_BY_USER", tasks=task_results)

            pending_task = self._load_next_task()

        self._log_run_summary(task_results, run_started)
        return BenchmarkRunResult(status="COMPLETED", tasks=task_results)

    async def _run_one_task(self, task: PendingTask) -> TaskRunResult:
        task_id = task.task_id
        turns = 0
        task_started = time.monotonic()
        self._sync_channel_identity(task_id=task_id)
        logger.info(
            "Task started task_id={}",
            task_id,
            data={"task_id": task_id, "sender_id": self._get_user_id(), "chat_id": task_id},
        )

        try:
            await self._send_initial_message(task)

            while turns < self.max_turns:
                agent_reply = await self.channel.wait_for_reply(timeout=self.turn_timeout)
                turns += 1

                action = await self.user_agent.next_action(agent_reply)

                task_result = await self._handle_action(
                    task_id=task_id,
                    turns=turns,
                    action_type=action.type,
                    message=action.message or "",
                    reason=action.reason or "",
                    task_started=task_started,
                )
                if task_result is None:
                    continue
                return task_result

            return self._finalize_task(
                task_id=task_id,
                status="MAX_TURNS",
                turns=turns,
                task_started=task_started,
                data={"max_turns": self.max_turns},
            )
        except asyncio.TimeoutError:
            return self._finalize_task(
                task_id=task_id,
                status="TIMEOUT",
                turns=turns,
                task_started=task_started,
                data={"turn_timeout_sec": self.turn_timeout},
            )
        except Exception as exc:
            logger.exception("Task failed task_id={}", task_id)
            return self._finalize_task(
                task_id=task_id,
                status="ERROR",
                turns=turns,
                error=str(exc),
                message=str(exc),
                task_started=task_started,
            )

    def _sync_channel_identity(self, *, task_id: str) -> None:
        self.channel.set_runtime_identity(
            sender_id=self._get_user_id(),
            chat_id=task_id,
        )

    def _load_next_task(self) -> PendingTask | None:
        try:
            initial_message = self.user_agent.initial_user_message(task_id=None)
        except KeyError:
            return None

        task_id = self.user_agent.current_task_id or "unknown_task"
        return PendingTask(task_id=task_id, initial_message=initial_message)

    async def _finish_task(self, result: TaskRunResult) -> None:
        await self._reset_channel(task_id=result.task_id)
        self.user_agent.finalize_task_logging(result.task_id)

    async def _send_initial_message(self, task: PendingTask) -> None:
        self._sync_channel_identity(task_id=task.task_id)
        await self.channel.send(task.initial_message)

    async def _handle_action(
        self,
        *,
        task_id: str,
        turns: int,
        action_type: str,
        message: str,
        reason: str,
        task_started: float,
    ) -> TaskRunResult | None:
        if action_type == "message":
            self._sync_channel_identity(task_id=task_id)
            await self.channel.send(message)
            return None
        if action_type == "terminate":
            return self._finalize_task(
                task_id=task_id,
                status="SUCCESS",
                turns=turns,
                task_started=task_started,
            )
        if action_type == "exit_benchmark":
            return self._finalize_task(
                task_id=task_id,
                status="EXITED_BY_USER",
                turns=turns,
                error=reason,
                message=reason,
                task_started=task_started,
            )
        unsupported = f"Unsupported action type: {action_type}"
        return self._finalize_task(
            task_id=task_id,
            status="ERROR",
            turns=turns,
            error=unsupported,
            message=unsupported,
            task_started=task_started,
        )

    async def _reset_channel(self, *, task_id: str) -> None:
        reset_started = time.monotonic()
        self._sync_channel_identity(task_id=task_id)
        await self.channel.reset()
        logger.info(
            "Channel reset task_id={} elapsed_ms={}",
            task_id,
            int((time.monotonic() - reset_started) * 1000),
            data={"task_id": task_id},
        )

    def _get_user_id(self) -> str:
        user_id = getattr(getattr(self.user_agent, "profile", None), "user_id", "")
        return user_id or "unknown_user"

    def _finalize_task(
        self,
        *,
        task_id: str,
        status: str,
        turns: int,
        task_started: float,
        error: Optional[str] = None,
        message: str = "",
        data: Optional[dict] = None,
    ) -> TaskRunResult:
        elapsed_ms = int((time.monotonic() - task_started) * 1000)
        log_fn = logger.error if status == "ERROR" else logger.warning if status in {"TIMEOUT", "MAX_TURNS"} else logger.info
        detail = message or "-"
        log_fn(
            "Task finished task_id={} status={} turns={} elapsed_ms={} detail={}",
            task_id,
            status,
            turns,
            elapsed_ms,
            detail,
            data={"task_id": task_id, "turns": turns, "elapsed_ms": elapsed_ms, **(data or {})},
        )
        return TaskRunResult(
            task_id=task_id,
            status=status,
            turns=turns,
            error=error,
        )

    def _log_run_summary(self, task_results: list[TaskRunResult], run_started: float) -> None:
        counts = Counter(item.status for item in task_results)
        elapsed_ms = int((time.monotonic() - run_started) * 1000)
        logger.info(
            "Benchmark finished tasks={} elapsed_ms={} statuses={}",
            len(task_results),
            elapsed_ms,
            dict(counts),
            data={"task_count": len(task_results), "elapsed_ms": elapsed_ms, "statuses": dict(counts)},
        )
