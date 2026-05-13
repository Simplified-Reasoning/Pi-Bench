from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import List, Optional

from src.data import (
    HiddenIntentItem,
    UserDataRepository,
    format_hidden_intents_with_status_xml,
    format_hidden_intents_xml,
    load_files_read_truncate_chars,
    load_task_files_read_entries,
)
from src.llm import LLMClient
from src.utils import get_logger, log_profile

from .base import BaseUserAgent, UserAgentAction
from .followup_style import normalize_targeted_followup_style
from .prompts import (
    build_intent_satisfaction_judge_prompt,
    build_targeted_followup_judge_prompt,
)

INTENT_DECISION_PATTERN = re.compile(
    r"<c(?P<idx>\d+)>\s*<content>\s*(?P<content>.*?)\s*</content>\s*<decision>\s*(?P<decision>YES|NO)\s*</decision>\s*</c(?P=idx)>",
    flags=re.IGNORECASE | re.DOTALL,
)
FOLLOWUP_DECISION_PATTERN = re.compile(
    r"<c(?P<idx>\d+)>\s*<content>\s*(?P<content>.*?)\s*</content>\s*<decision>\s*(?P<decision>YES|NO)\s*</decision>(?:\s*<style>\s*(?P<style>.*?)\s*</style>)?\s*</c(?P=idx)>",
    flags=re.IGNORECASE | re.DOTALL,
)
DEFAULT_INTENT_PARSE_RETRIES = 16
_RETRY_DELAYS_SECONDS = (1.0, 4.0, 16.0, 64.0, 128.0, 256.0, 512.0)
logger = get_logger("UserAgent.LLM")
hidden_logger = logger.profile("hidden_intent")
HIDDEN_INTENT_STATUS_DISPLAY_ORDER = ("not_provided", "provided", "inferred")
VISIBLE_HIDDEN_INTENT_STATUS_DISPLAY_ORDER = ("not_provided", "provided")


def _normalize_whitespace(value: str) -> str:
    return " ".join((value or "").split())


def _retry_delay_seconds(retry_number: int) -> float:
    if retry_number < 1:
        raise ValueError("retry_number must be >= 1")
    return _RETRY_DELAYS_SECONDS[min(retry_number - 1, len(_RETRY_DELAYS_SECONDS) - 1)]


@dataclass
class RuntimeHiddenIntent:
    idx: int
    content: str
    status: str

    def as_item(self) -> HiddenIntentItem:
        return HiddenIntentItem(content=self.content, status=self.status)


@dataclass(frozen=True)
class IntentDecision:
    idx: int
    content: str
    decision: str


@dataclass(frozen=True)
class FollowupDecision:
    idx: int
    content: str
    decision: str
    style: str | None = None


def _serialize_intent_decisions(
    candidates: list[RuntimeHiddenIntent],
    decisions: list[IntentDecision],
) -> list[dict[str, str | int]]:
    serialized: list[dict[str, str | int]] = []
    for candidate, decision in zip(candidates, decisions):
        serialized.append(
            {
                "idx": candidate.idx,
                "content": candidate.content,
                "decision": decision.decision,
            }
        )
    return serialized


def _serialize_followup_decisions(
    candidates: list[RuntimeHiddenIntent],
    decisions: list[FollowupDecision],
) -> list[dict[str, str | int | None]]:
    serialized: list[dict[str, str | int | None]] = []
    for candidate, decision in zip(candidates, decisions):
        serialized.append(
            {
                "idx": candidate.idx,
                "content": candidate.content,
                "decision": decision.decision,
                "style": decision.style,
            }
        )
    return serialized


class UserAgent(BaseUserAgent):
    """
    LLM-backed user agent driven by hidden intent status transitions.
    """

    def __init__(
        self,
        user_root: str,
        llm_client: LLMClient,
        repository: Optional[UserDataRepository] = None,
        agent_id: str = "user_agent",
        task_ids: Optional[List[str]] = None,
        output_root: str = "outputs",
        model_id: Optional[str] = None,
        workspace_dir: str | Path | None = None,
        copy_task_assets_to_workspace: bool = True,
        history_config_path: str | Path = "config/bench/evaluation/trace_history.yaml",
        intent_parse_retries: int = DEFAULT_INTENT_PARSE_RETRIES,
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
        self.llm = llm_client
        self.intent_parse_retries = int(intent_parse_retries)
        if self.intent_parse_retries < 1:
            raise ValueError("intent_parse_retries must be >= 1")
        self.history_config_path = Path(history_config_path).expanduser()
        self.files_read_truncate_chars = load_files_read_truncate_chars(self.history_config_path)
        self._runtime_hidden_intents: list[RuntimeHiddenIntent] = []
        self._assistant_turn_index = 0

    def initial_user_message(self, task_id: Optional[str]) -> str:
        message = super().initial_user_message(task_id)
        task = self._get_active_task()
        self._assistant_turn_index = 0
        self._runtime_hidden_intents = [
            RuntimeHiddenIntent(idx=idx, content=item.content, status=item.status)
            for idx, item in enumerate(task.hidden_intents, start=1)
        ]
        status_groups = self._hidden_intent_status_groups()
        hidden_logger.info(
            "Hidden intents initialized {}",
            self._format_hidden_intent_status_groups(("not_provided", "provided")),
            data={
                "status_groups": status_groups,
                "hidden_intents": [
                    {"idx": item.idx, "content": item.content, "status": item.status}
                    for item in self._runtime_hidden_intents
                ]
            },
        )
        return message

    @log_profile("hidden_intent")
    async def next_action(self, agent_response: str) -> UserAgentAction:
        self._get_active_task()
        assistant_message_round = self._record_message("assistant", agent_response)
        self._assistant_turn_index += 1
        # self._reset_inferred_hidden_intents()

        satisfaction_candidates = self._runtime_hidden_intents_by_status({"not_provided"})
        if not satisfaction_candidates:
            logger.info(
                "Intent satisfaction skipped: no not_provided hidden intents remain",
            )
            self._close_active_task()
            return UserAgentAction.terminate(reason="all_hidden_intents_resolved")

        satisfaction_decisions = await self._judge_intent_satisfaction(agent_response, satisfaction_candidates)
        newly_inferred: list[int] = []
        for item, decision in zip(satisfaction_candidates, satisfaction_decisions):
            if decision.decision == "YES" and item.status == "not_provided":
                item.status = "inferred"
                newly_inferred.append(item.idx)
        status_groups = self._hidden_intent_status_groups()
        logger.info(
            "Intent satisfaction completed newly_inferred={} {}",
            newly_inferred,
            self._format_hidden_intent_status_groups(VISIBLE_HIDDEN_INTENT_STATUS_DISPLAY_ORDER),
            data={
                "decisions": _serialize_intent_decisions(
                    satisfaction_candidates,
                    satisfaction_decisions,
                ),
                "newly_inferred_indexes": newly_inferred,
                "status_groups": status_groups,
                "statuses": self._hidden_intent_status_snapshot(),
            },
        )
        if all(decision.decision == "YES" for decision in satisfaction_decisions):
            self._close_active_task()
            return UserAgentAction.terminate(reason="termination_policy")

        followup_candidates = self._runtime_hidden_intents_by_status({"not_provided"})
        if not followup_candidates:
            logger.info(
                "Targeted followup skipped: no not_provided hidden intents remain",
            )
            self._close_active_task()
            return UserAgentAction.terminate(reason="all_hidden_intents_resolved")

        followup_decisions = await self._judge_targeted_followups(agent_response, followup_candidates)
        matched_followup_decisions = {
            item.idx: decision
            for item, decision in zip(followup_candidates, followup_decisions)
            if decision.decision == "YES"
        }
        matched_followups = [
            item
            for item, decision in zip(followup_candidates, followup_decisions)
            if decision.decision == "YES"
        ]
        logger.info(
            "Targeted followup completed matched={}",
            [item.idx for item in matched_followups],
            data={
                "decisions": _serialize_followup_decisions(
                    followup_candidates,
                    followup_decisions,
                ),
                "matched_indexes": [item.idx for item in matched_followups],
                "statuses": self._hidden_intent_status_snapshot(),
            },
        )

        if matched_followups:
            reply = await self._build_targeted_followup_reply(agent_response, matched_followups)
            for item in matched_followups:
                item.status = "provided"
            updated_indexes = [item.idx for item in matched_followups]
            reply_metadata = {
                "targeted_followup": {
                    "assistant_turn_index": self._assistant_turn_index,
                    "assistant_message_round": assistant_message_round,
                    "matched_hidden_intents": [
                        {
                            "idx": item.idx,
                            "content": item.content,
                            "style": matched_followup_decisions[item.idx].style,
                        }
                        for item in matched_followups
                    ],
                }
            }
        else:
            target = followup_candidates[0]
            reply = await self._build_first_unmet_reply(agent_response, target)
            target.status = "provided"
            updated_indexes = [target.idx]
            reply_metadata = None

        logger.info(
            "Reply built updated_indexes={}",
            updated_indexes,
            data={
                "updated_indexes": updated_indexes,
                "statuses": self._hidden_intent_status_snapshot(),
            },
        )
        self._record_message("user", reply, metadata=reply_metadata)
        return UserAgentAction.message_action(reply)

    async def _llm_chat(self, prompt: str, temperature: float) -> str:
        response = await self.llm.chat(
            [{"role": "user", "content": prompt}], temperature=temperature
        )
        logger.llm_call(prompt=prompt, response=response.content)
        return response.content

    def _runtime_hidden_intents_as_items(self) -> list[HiddenIntentItem]:
        return [item.as_item() for item in self._runtime_hidden_intents]

    def _runtime_hidden_intents_by_status(self, statuses: set[str]) -> list[RuntimeHiddenIntent]:
        return [item for item in self._runtime_hidden_intents if item.status in statuses]

    def _reset_inferred_hidden_intents(self) -> list[int]:
        reset_indexes: list[int] = []
        for item in self._runtime_hidden_intents:
            if item.status != "inferred":
                continue
            item.status = "not_provided"
            reset_indexes.append(item.idx)
        return reset_indexes

    def _hidden_intents_xml(
        self,
        *,
        indexes: Optional[set[int]] = None,
        include_idx: bool = False,
    ) -> str:
        return format_hidden_intents_xml(
            self._runtime_hidden_intents_as_items(),
            indexes=indexes,
            include_idx=include_idx,
        )

    def _hidden_intents_with_status_xml(
        self,
        *,
        statuses: Optional[set[str]] = None,
        indexes: Optional[set[int]] = None,
    ) -> str:
        return format_hidden_intents_with_status_xml(
            self._runtime_hidden_intents_as_items(),
            statuses=statuses,
            indexes=indexes,
        )

    def _hidden_intent_status_snapshot(self) -> list[dict[str, str | int]]:
        return [
            {"idx": item.idx, "content": item.content, "status": item.status}
            for item in self._runtime_hidden_intents
        ]

    def _hidden_intent_status_groups(self) -> dict[str, list[int]]:
        groups = {status: [] for status in HIDDEN_INTENT_STATUS_DISPLAY_ORDER}
        for item in self._runtime_hidden_intents:
            groups.setdefault(item.status, []).append(item.idx)
        return groups

    def _format_hidden_intent_status_groups(
        self,
        statuses: tuple[str, ...] = HIDDEN_INTENT_STATUS_DISPLAY_ORDER,
    ) -> str:
        groups = self._hidden_intent_status_groups()
        return " ".join(f"{status}={groups.get(status, [])}" for status in statuses)

    def _files_read_context_xml(self) -> str:
        task = self._get_active_task()
        attached_files = load_task_files_read_entries(
            task=task,
            workspace_dir=self.workspace_dir,
            truncate_chars=self.files_read_truncate_chars,
        )
        if not attached_files:
            return "<files />"

        lines: list[str] = []
        for attached_file in attached_files:
            attrs = [f'name="{escape(attached_file.name)}"']
            if not attached_file.exists:
                attrs.append('status="missing"')
            lines.append(f"<file {' '.join(attrs)}>{attached_file.content}</file>")
        return "\n".join(lines)

    async def _judge_intent_satisfaction(
        self,
        latest_assistant_message: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[IntentDecision]:
        prompt = build_intent_satisfaction_judge_prompt(
            role=self.profile.role_text,
            hidden_intents_xml=self._hidden_intents_xml(),
            status_hidden_intents_xml=self._hidden_intents_with_status_xml(
                indexes={item.idx for item in candidates}
            ),
            latest_assistant_message=latest_assistant_message,
            files_context_xml=self._files_read_context_xml(),
            contents=[item.content for item in candidates],
        )
        return await self._request_intent_decisions(
            prompt=prompt,
            candidates=candidates,
        )

    async def _judge_targeted_followups(
        self,
        latest_assistant_message: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[FollowupDecision]:
        prompt = build_targeted_followup_judge_prompt(
            role=self.profile.role_text,
            hidden_intents_xml=self._hidden_intents_xml(),
            status_hidden_intents_xml=self._hidden_intents_with_status_xml(
                statuses={"not_provided"},
                indexes={item.idx for item in candidates},
            ),
            latest_assistant_message=latest_assistant_message,
            contents=[item.content for item in candidates],
        )
        return await self._request_followup_decisions(
            prompt=prompt,
            candidates=candidates,
        )

    async def _build_first_unmet_reply(
        self,
        latest_assistant_message: str,
        target: RuntimeHiddenIntent,
    ) -> str:
        _ = latest_assistant_message
        return target.content

    async def _build_targeted_followup_reply(
        self,
        latest_assistant_message: str,
        targets: list[RuntimeHiddenIntent],
    ) -> str:
        _ = latest_assistant_message
        return "\n".join(item.content for item in targets)

    def _parse_intent_decisions(
        self,
        output: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[IntentDecision]:
        matches = list(INTENT_DECISION_PATTERN.finditer(output or ""))
        if len(matches) != len(candidates):
            raise ValueError(f"invalid block count expected={len(candidates)} got={len(matches)}")

        parsed: dict[int, IntentDecision] = {}
        for match in matches:
            index = int(match.group("idx"))
            if index < 1 or index > len(candidates):
                raise ValueError(f"decision index out of range: {index}")
            if index in parsed:
                raise ValueError(f"duplicate decision index: {index}")

            expected_content = candidates[index - 1].content
            parsed_content = (match.group("content") or "").strip()
            if _normalize_whitespace(parsed_content) != _normalize_whitespace(expected_content):
                raise ValueError(f"content mismatch at index {index}")

            decision = (match.group("decision") or "").strip().upper()
            if decision not in {"YES", "NO"}:
                raise ValueError(f"invalid decision at index {index}: {decision!r}")
            parsed[index] = IntentDecision(
                idx=index,
                content=expected_content,
                decision=decision,
            )

        missing = [index for index in range(1, len(candidates) + 1) if index not in parsed]
        if missing:
            raise ValueError(f"missing decision indexes: {missing}")
        return [parsed[index] for index in range(1, len(candidates) + 1)]

    def _parse_followup_decisions(
        self,
        output: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[FollowupDecision]:
        matches = list(FOLLOWUP_DECISION_PATTERN.finditer(output or ""))
        if len(matches) != len(candidates):
            raise ValueError(f"invalid block count expected={len(candidates)} got={len(matches)}")

        parsed: dict[int, FollowupDecision] = {}
        for match in matches:
            index = int(match.group("idx"))
            if index < 1 or index > len(candidates):
                raise ValueError(f"decision index out of range: {index}")
            if index in parsed:
                raise ValueError(f"duplicate decision index: {index}")

            expected_content = candidates[index - 1].content
            parsed_content = (match.group("content") or "").strip()
            if _normalize_whitespace(parsed_content) != _normalize_whitespace(expected_content):
                raise ValueError(f"content mismatch at index {index}")

            decision = (match.group("decision") or "").strip().upper()
            if decision not in {"YES", "NO"}:
                raise ValueError(f"invalid decision at index {index}: {decision!r}")

            raw_style = (match.group("style") or "").strip()
            if decision == "YES":
                if not raw_style:
                    raise ValueError(f"missing style for YES decision at index {index}")
                style = normalize_targeted_followup_style(raw_style)
            else:
                if raw_style:
                    raise ValueError(f"unexpected style for NO decision at index {index}")
                style = None

            parsed[index] = FollowupDecision(
                idx=index,
                content=expected_content,
                decision=decision,
                style=style,
            )

        missing = [index for index in range(1, len(candidates) + 1) if index not in parsed]
        if missing:
            raise ValueError(f"missing decision indexes: {missing}")
        return [parsed[index] for index in range(1, len(candidates) + 1)]

    async def _request_intent_decisions(
        self,
        *,
        prompt: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[IntentDecision]:
        last_error: ValueError | None = None
        for attempt in range(1, self.intent_parse_retries + 1):
            response = await self._llm_chat(
                prompt,
                temperature=0.0,
            )
            try:
                return self._parse_intent_decisions(response, candidates)
            except ValueError as exc:
                last_error = exc
                if attempt < self.intent_parse_retries:
                    logger.warning(
                        "Retrying intent decision parse attempt={}/{} reason={}",
                        attempt,
                        self.intent_parse_retries,
                        str(exc),
                        data={
                            "attempt": attempt,
                            "retry_limit": self.intent_parse_retries,
                        },
                    )
                    await asyncio.sleep(_retry_delay_seconds(attempt))
        raise ValueError(
            f"failed to parse intent decisions after {self.intent_parse_retries} attempts: {last_error}"
        )

    async def _request_followup_decisions(
        self,
        *,
        prompt: str,
        candidates: list[RuntimeHiddenIntent],
    ) -> list[FollowupDecision]:
        last_error: ValueError | None = None
        for attempt in range(1, self.intent_parse_retries + 1):
            response = await self._llm_chat(
                prompt,
                temperature=0.0,
            )
            try:
                return self._parse_followup_decisions(response, candidates)
            except ValueError as exc:
                last_error = exc
                if attempt < self.intent_parse_retries:
                    logger.warning(
                        "Retrying followup decision parse attempt={}/{} reason={}",
                        attempt,
                        self.intent_parse_retries,
                        str(exc),
                        data={
                            "attempt": attempt,
                            "retry_limit": self.intent_parse_retries,
                        },
                    )
                    await asyncio.sleep(_retry_delay_seconds(attempt))
        raise ValueError(
            f"failed to parse followup decisions after {self.intent_parse_retries} attempts: {last_error}"
        )
