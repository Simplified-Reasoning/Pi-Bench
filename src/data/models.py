from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict


@dataclass
class RoleProfile:
    """
    Role profile loaded from `data/{user_id}/profile.yaml`.

    Sub-structure (file-level meaning):
    - Identity
      - `user_id`: the primary identifier used to load the user agent from `data/`.
    - Role Text (the "who is the user" narrative)
      - `role_text`: a single long text block describing background, habits, and preferences.
    - Preferences (optional, structured hints)
      - `preferences`: lightweight knobs (verbosity, proactiveness, language, etc.).
        This is NOT required for correctness; it only guides prompt style.
    - Long-term Goals (optional, structured hints)
      - `long_term_goals`: stable objectives across tasks in the same episode.

    Runtime note:
    - Treat RoleProfile as read-only during execution. Any derived summaries should
      be stored elsewhere (e.g., runtime logs), not mutated here.
    """

    user_id: str
    role_text: str
    preferences: Dict[str, Any]
    long_term_goals: List[str]


class ObjectiveItemDict(TypedDict, total=False):
    """
    A single objective checklist item.

    Sub-structure:
    - Criterion
      - `criterion`: human-readable pass/fail requirement used by an evaluator.
    - Weight
      - `weight`: multiplier applied when the criterion is scored YES.
    - Evaluation Kind
      - `evaluation`: `llm` for text criteria scored by LLM.
    """

    criterion: str
    weight: float
    evaluation: str


@dataclass(frozen=True)
class ToolTraceSpec:
    """One tool trace extraction rule from `objectives.tools`."""

    tool_name: str
    call_paths: list[str]
    result_paths: list[str]


VALID_HIDDEN_INTENT_STATUSES = ("not_provided", "provided", "inferred")
VALID_TASK_HIDDEN_INTENT_STATUSES = ("not_provided", "provided")


@dataclass(frozen=True)
class HiddenIntentItem:
    """One hidden intent point from task.yaml."""

    content: str
    status: str


def format_hidden_intents_xml(
    hidden_intents: List[HiddenIntentItem],
    *,
    indexes: Optional[set[int]] = None,
    include_idx: bool = True,
) -> str:
    return "\n".join(
        (
            f'<hidden_intent idx="{idx}">{escape(item.content, quote=False)}</hidden_intent>'
            if include_idx
            else f"<hidden_intent>{escape(item.content, quote=False)}</hidden_intent>"
        )
        for idx, item in enumerate(hidden_intents, start=1)
        if indexes is None or idx in indexes
    )


def format_hidden_intents_with_status_xml(
    hidden_intents: List[HiddenIntentItem],
    *,
    statuses: Optional[set[str]] = None,
    indexes: Optional[set[int]] = None,
) -> str:
    lines: list[str] = []
    for idx, item in enumerate(hidden_intents, start=1):
        if indexes is not None and idx not in indexes:
            continue
        if statuses is not None and item.status not in statuses:
            continue
        lines.append(
            f'<hidden_intent idx="{idx}" status="{item.status}">{escape(item.content, quote=False)}</hidden_intent>'
        )
    return "\n".join(lines)


@dataclass
class TaskSpec:
    """
    Task spec loaded from `data/{user_id}/tasks/{task_id}/task.yaml`.

    TaskSpec is the key unit for the user agent. It defines:
    - what the user initially asks for (`initial_input`)
    - what the user actually wants (`hidden_intents`) used for user-agent reasoning
    - which generated files should be reloaded into per-turn `trace_{turn_idx}.txt` during evaluation

    Sub-structure (how to read the fields):
    - Identity
      - `schema_version`: task schema version from YAML.
      - `task_id`: unique task id within the episode.
      - `user_id`: back-reference to the owning user.
      - `environment_id`: environment binding for the task.
      - `task_dir`: source directory that contains `task.yaml` and any task-scoped assets.
    - Metadata (reporting/debugging only)
      - `title`, `description`
      - `task_type`: short_term_independent | short_term_contextual | long_term
      - `metadata`: free-form mapping copied from YAML
    - Trigger & Intent (what starts the task + what user says)
      - `trigger_type`: user_query | environmental_signal
      - `initial_input`: the message published at task start
      - `hidden_intents`: ordered hidden intent points with v2-only status metadata
    - Objectives (evaluator-oriented, not necessarily enforced by runtime)
      - `files_read`: artifact filenames to inline into evaluation history
      - `objectives`: list of `ObjectiveItemDict`
    - Raw YAML
      - `raw`: original mapping to support escape-hatches and debugging without adding fields
    """

    schema_version: str
    task_id: str
    user_id: str
    environment_id: str
    task_dir: Path

    # Metadata (for reporting / debugging)
    title: str
    description: str
    task_type: str
    metadata: Dict[str, Any]

    # Trigger & intent
    trigger_type: str  # user_query | environmental_signal
    initial_input: str
    hidden_intents: List[HiddenIntentItem]

    # Objectives (lightweight config)
    files_read: List[str]
    objectives: List[ObjectiveItemDict]
    tool_trace_specs: List[ToolTraceSpec]
    tools_evaluation_path: Path | None

    raw: Dict[str, Any]


@dataclass
class EpisodeSpec:
    """
    Episode spec loaded from `data/{user_id}/episode.yaml`.

    EpisodeSpec defines the runnable unit for a single user agent instance.

    Sub-structure:
    - Identity
      - `episode_id`: unique id for the episode.
      - `user_id`: user identifier (folder name under `data/`).
    - Environment binding
      - `docker_image_id`: one episode maps to one docker image; all tasks share it.
    - Execution order
      - `task_order`: the task ids in execution sequence.
    - Raw YAML
      - `raw`: original mapping for debugging.
    """

    episode_id: str
    user_id: str
    docker_image_id: str
    task_order: List[str]
    raw: Dict[str, Any]
