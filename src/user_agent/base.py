from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.data import (
    EpisodeSpec,
    RoleProfile,
    TaskSpec,
    UserDataRepository,
    list_task_workspace_assets,
)
from src.utils import (
    activate_task_logging,
    bind_log_run,
    complete_task_logging,
    get_logger,
    record_history_message,
)

logger = get_logger("UserAgent.Base")


@dataclass(frozen=True)
class UserAgentAction:
    """Output of a user agent step."""

    type: str  # "message" | "terminate" | "exit_benchmark"
    message: Optional[str] = None
    reason: Optional[str] = None

    @classmethod
    def message_action(cls, message: str) -> "UserAgentAction":
        return cls(type="message", message=message)

    @classmethod
    def terminate(cls, reason: str = "not_implemented") -> "UserAgentAction":
        return cls(type="terminate", reason=reason)

    @classmethod
    def exit_benchmark(cls, reason: str = "user_exit") -> "UserAgentAction":
        return cls(type="exit_benchmark", reason=reason)


class BaseUserAgent(ABC):
    """
    Shared user agent base:
    - loads user profile/episode/tasks
    - owns task cursor and active task state
    - provides task start flow via initial_user_message
    """

    def __init__(
        self,
        user_root: str,
        repository: Optional[UserDataRepository] = None,
        agent_id: str = "user_agent",
        task_ids: Optional[List[str]] = None,
        output_root: str | Path = "outputs",
        model_id: Optional[str] = None,
        workspace_dir: str | Path | None = None,
        copy_task_assets_to_workspace: bool = True,
    ):
        self.user_root = Path(user_root)
        if not self.user_root.exists():
            raise FileNotFoundError(f"Missing user data path: {self.user_root}")
        if not self.user_root.is_dir():
            raise NotADirectoryError(f"User data path must be a directory: {self.user_root}")

        user_id = self.user_root.name
        repo = repository or UserDataRepository(data_root=str(self.user_root.parent))
        profile, episode, tasks = repo.load_user(user_id)

        selected_task_ids = [item.strip() for item in (task_ids or []) if item and item.strip()]
        if selected_task_ids:
            selected_set = set(selected_task_ids)
            filtered_order = [task_id for task_id in episode.task_order if task_id in selected_set]
            if not filtered_order:
                raise KeyError(f"No matching task_id found in episode.task_order: {selected_task_ids}")
            missing = [task_id for task_id in selected_task_ids if task_id not in tasks]
            if missing:
                raise KeyError(f"Unknown task_id: {missing}")
            episode.task_order = filtered_order
            tasks = {task_id: tasks[task_id] for task_id in filtered_order}

        self.profile: RoleProfile = profile
        self.episode: EpisodeSpec = episode
        self.tasks: Dict[str, TaskSpec] = tasks
        self.agent_id = agent_id
        self.output_root = Path(output_root)
        self.model_id = str(model_id or agent_id)
        self.workspace_dir = Path(workspace_dir).expanduser() if workspace_dir is not None else None
        self.copy_task_assets_to_workspace = bool(copy_task_assets_to_workspace)

        self.active_task_id: Optional[str] = None
        self._task_cursor = 0
        bind_log_run(
            output_root=self.output_root,
            model_id=self.model_id,
            user_id=self.profile.user_id,
            agent_id=self.agent_id,
        )

    @property
    def current_task_id(self) -> Optional[str]:
        return self.active_task_id

    def initial_user_message(self, task_id: Optional[str]) -> str:
        if task_id is None:
            task_id = self._next_task_id()
        elif task_id in self.episode.task_order:
            self._set_cursor_after(task_id)
        if task_id not in self.tasks:
            raise KeyError(f"Unknown task_id: {task_id}")

        self.active_task_id = task_id
        task_session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        activate_task_logging(task_id, session_timestamp=task_session_ts)
        self._stage_task_workspace(self.tasks[task_id])
        message = self.tasks[task_id].initial_input
        self._record_message("user", message)
        return message

    @abstractmethod
    async def next_action(self, agent_response: str) -> UserAgentAction:
        """Given the latest agent response, return next user action."""

    def _record_message(
        self,
        role: str,
        message: str,
        *,
        metadata: dict | None = None,
    ) -> int | None:
        return record_history_message(role=role, message=message, metadata=metadata)

    def _get_active_task(self) -> TaskSpec:
        if self.active_task_id is None:
            raise RuntimeError("No active task; call initial_user_message first.")
        return self.tasks[self.active_task_id]

    def _close_active_task(self) -> None:
        self.active_task_id = None

    def finalize_task_logging(self, task_id: str | None = None) -> None:
        complete_task_logging(task_id)

    def _stage_task_workspace(self, task: TaskSpec) -> None:
        if self.workspace_dir is None:
            logger.info(
                "Task workspace setup skipped task_id={} reason=missing_workspace_dir",
                task.task_id,
                data={"task_id": task.task_id, "reason": "missing_workspace_dir"},
            )
            return

        should_copy_task_assets = self.copy_task_assets_to_workspace
        task_assets = list_task_workspace_assets(task) if should_copy_task_assets else []
        skills_source_path = self.user_root / "skills"
        should_copy_user_skills = skills_source_path.exists()

        if not should_copy_task_assets and not should_copy_user_skills:
            logger.info(
                "Task workspace setup skipped task_id={} reason=disabled",
                task.task_id,
                data={"task_id": task.task_id, "reason": "disabled"},
            )
            return
        if not task_assets and not should_copy_user_skills:
            logger.info(
                "Task workspace setup skipped task_id={} reason=no_assets",
                task.task_id,
                data={"task_id": task.task_id, "reason": "no_assets"},
            )
            return

        copied_paths: list[str] = []
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            for source_path in task_assets:
                relative_path = source_path.relative_to(task.task_dir)
                destination_path = self.workspace_dir / relative_path
                self._copy_task_asset(source_path, destination_path)
                copied_paths.append(str(relative_path))
            if should_copy_user_skills:
                skills_destination = self.workspace_dir / "skills"
                self._copy_task_asset(skills_source_path, skills_destination)
                copied_paths.append("skills")
        except Exception as exc:
            logger.error(
                "Task workspace setup failed task_id={} workspace_dir={} copied={} error={}",
                task.task_id,
                self.workspace_dir,
                self._format_workspace_items(copied_paths),
                exc,
                data={"task_id": task.task_id, "copied_paths": copied_paths},
            )
            raise

        logger.info(
            "Task workspace setup copied task_id={} assets={} workspace_dir={} items={}",
            task.task_id,
            len(copied_paths),
            self.workspace_dir,
            self._format_workspace_items(copied_paths),
            data={
                "task_id": task.task_id,
                "copied_count": len(copied_paths),
                "copied_paths": copied_paths,
            },
        )

    def _copy_task_asset(self, source_path: Path, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        self._remove_existing_path(destination_path)
        if source_path.is_dir():
            shutil.copytree(source_path, destination_path)
            return
        shutil.copy2(source_path, destination_path)

    @staticmethod
    def _remove_existing_path(path: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return
        if path.is_symlink() or path.is_file():
            path.unlink()
            return
        shutil.rmtree(path)

    @staticmethod
    def _format_workspace_items(items: Iterable[str]) -> str:
        values = [str(item) for item in items if str(item)]
        if not values:
            return "-"
        return ", ".join(values)

    def _next_task_id(self) -> str:
        order = self.episode.task_order
        while self._task_cursor < len(order):
            task_id = order[self._task_cursor]
            self._task_cursor += 1
            if task_id in self.tasks:
                return task_id
        raise KeyError("No remaining task_id in episode.task_order.")

    def _set_cursor_after(self, task_id: str) -> None:
        try:
            index = self.episode.task_order.index(task_id)
        except ValueError:
            return
        self._task_cursor = max(self._task_cursor, index + 1)
