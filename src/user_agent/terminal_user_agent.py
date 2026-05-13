from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

from src.data import UserDataRepository
from .base import BaseUserAgent, UserAgentAction


class TerminalUserAgent(BaseUserAgent):
    """
    Terminal-driven user agent.

    Commands:
    - /quit: end current task
    - /exit: end the whole benchmark run
    """

    def __init__(
        self,
        user_root: str,
        repository: Optional[UserDataRepository] = None,
        agent_id: str = "terminal_user_agent",
        task_ids: Optional[list[str]] = None,
        output_root: str = "outputs",
        model_id: Optional[str] = None,
        workspace_dir: str | Path | None = None,
        copy_task_assets_to_workspace: bool = True,
        input_reader: Optional[Callable[[], str]] = None,
        output_writer: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            user_root=user_root,
            repository=repository,
            agent_id=agent_id,
            task_ids=task_ids,
            output_root=output_root,
            model_id=model_id,
            workspace_dir=workspace_dir,
            copy_task_assets_to_workspace=copy_task_assets_to_workspace,
        )
        self._input_reader = input_reader or self._default_input_reader
        self._output_writer = output_writer or print

    async def next_action(self, agent_response: str) -> UserAgentAction:
        self._get_active_task()
        self._record_message("assistant", agent_response)

        self._output_writer(f"\n[Agent]: {agent_response}")
        self._output_writer("[User]: ")

        try:
            user_input = (self._input_reader() or "").strip()
        except KeyboardInterrupt:
            self._close_active_task()
            return UserAgentAction.exit_benchmark(reason="keyboard_interrupt")

        if user_input == "/exit":
            self._close_active_task()
            return UserAgentAction.exit_benchmark(reason="terminal_exit")
        if user_input == "/quit":
            self._close_active_task()
            return UserAgentAction.terminate(reason="terminal_quit")

        self._record_message("user", user_input)
        return UserAgentAction.message_action(user_input)

    @staticmethod
    def _default_input_reader() -> str:
        return sys.stdin.readline()
