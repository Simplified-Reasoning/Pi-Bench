#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text_list_from_hidden_intent(task: dict[str, Any]) -> list[str]:
    items = as_list(task.get("intent", {}).get("hidden_intent"))
    out: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("content")
            if text:
                out.append(str(text).strip())
        elif item:
            out.append(str(item).strip())
    return out


def text_list_from_checklist(task: dict[str, Any]) -> list[str]:
    items = as_list(task.get("objectives", {}).get("checklist"))
    out: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("criterion")
            if text:
                out.append(str(text).strip())
        elif item:
            out.append(str(item).strip())
    return out


def path_list(task: dict[str, Any], field: str) -> list[str]:
    items = as_list(task.get("objectives", {}).get(field))
    out: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("path"):
            out.append(str(item["path"]).strip())
    return out


def stringify_bullets(items: list[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def code_block(text: str) -> str:
    return f"```text\n{text.rstrip()}\n```"


def json_block(data: dict[str, Any]) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"


def task_brief(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": task.get("title", ""),
        "task_type": task.get("task_type", ""),
        "initial_input": task.get("intent", {}).get("initial_input", ""),
        "hidden_intent": text_list_from_hidden_intent(task),
        "checklist": text_list_from_checklist(task),
        "file_read": path_list(task, "file_read"),
        "file_create": path_list(task, "file_create"),
    }


def dependency_packet(task_id: str, task: dict[str, Any]) -> dict[str, Any]:
    brief = task_brief(task)
    return {
        "task_id": task_id,
        "title": brief["title"],
        "initial_input": brief["initial_input"],
        "hidden_intent": brief["hidden_intent"],
    }


def step_packets(
    task_id: str,
    task: dict[str, Any],
    deps: list[str],
    task_map: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    brief = task_brief(task)
    missing_deps: list[str] = []
    dep_intent_packets: list[dict[str, Any]] = []
    for dep_id in deps:
        dep_task = task_map.get(dep_id)
        if not dep_task:
            missing_deps.append(dep_id)
            continue
        dep_intent_packets.append(dependency_packet(dep_id, dep_task))

    step1 = {
        "target_task_id": task_id,
        "mode": "step1_hidden_intent_pass",
        "current_task": {
            "task_id": task_id,
            "title": brief["title"],
            "initial_input": brief["initial_input"],
            "hidden_intent": brief["hidden_intent"],
        },
        "instructions": [
            "Generate a candidate answer using only the current task initial_input and current task hidden_intent.",
            "Do not use any checklist.",
            "Do not assume access to dependency tasks unless explicitly included here.",
        ],
    }
    step2 = {
        "target_task_id": task_id,
        "mode": "step2_dependency_intent_pass",
        "current_task": {
            "task_id": task_id,
            "title": brief["title"],
            "initial_input": brief["initial_input"],
        },
        "dependency_tasks": dep_intent_packets,
        "instructions": [
            "Generate a candidate answer using only the current task initial_input and dependency task intents.",
            "Do not use the current task hidden_intent.",
            "Do not use any checklist.",
        ],
    }
    step3 = {
        "target_task_id": task_id,
        "mode": "step3_prompt_only_fail",
        "current_task": {
            "task_id": task_id,
            "title": brief["title"],
            "initial_input": brief["initial_input"],
        },
        "instructions": [
            "Generate a candidate answer using only the current task initial_input.",
            "Do not use hidden_intent.",
            "Do not use dependency task intents.",
            "Do not use any checklist.",
        ],
    }
    return step1, step2, step3, missing_deps


def build_report(root: Path, packets_dir: Path | None = None) -> tuple[str, dict[str, Any] | None]:
    episode_path = root / "episode.yaml"
    if not episode_path.exists():
        raise FileNotFoundError(f"missing episode.yaml: {episode_path}")

    episode = load_yaml(episode_path)
    tasks = as_list(episode.get("tasks"))
    task_map: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for item in tasks:
        task_id = item.get("task_id")
        if not task_id:
            errors.append("episode entry missing task_id")
            continue
        task_path = root / "tasks" / task_id / "task.yaml"
        if not task_path.exists():
            errors.append(f"missing task file: {task_path}")
            continue
        task_map[task_id] = load_yaml(task_path)

    lines: list[str] = []
    lines.append(f"# Task Validation Report\n")
    lines.append(f"Dataset root: `{root}`\n")
    lines.append("## Summary\n")
    lines.append(f"- Episode id: `{episode.get('episode_id', '-')}`")
    lines.append(f"- User id: `{episode.get('user_id', '-')}`")
    lines.append(f"- Task count: `{len(tasks)}`")
    lines.append("")

    if errors:
        lines.append("## Structural Errors\n")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    packet_paths: list[str] = []
    manifest: dict[str, Any] | None = None
    if packets_dir is not None:
        manifest = {
            "dataset_root": str(root),
            "episode_id": episode.get("episode_id", "-"),
            "user_id": episode.get("user_id", "-"),
            "groups": [],
        }
    lines.append("## Task Index\n")
    lines.append("| # | task_id | task_type | depends_on | hidden_intent_count | checklist_count | file_io |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for idx, item in enumerate(tasks, 1):
        task_id = item.get("task_id", "-")
        task = task_map.get(task_id, {})
        brief = task_brief(task) if task else {
            "task_type": "-",
            "hidden_intent": [],
            "checklist": [],
            "file_read": [],
            "file_create": [],
        }
        deps = as_list(item.get("depends_on"))
        io_parts: list[str] = []
        if brief["file_read"]:
            io_parts.append("read")
        if brief["file_create"]:
            io_parts.append("write")
        file_io = "/".join(io_parts) if io_parts else "-"
        lines.append(
            f"| {idx} | {task_id} | {brief['task_type']} | "
            f"{', '.join(deps) if deps else '-'} | {len(brief['hidden_intent'])} | "
            f"{len(brief['checklist'])} | {file_io} |"
        )
    lines.append("")

    lines.append("## Parallel Subagent Execution Plan\n")
    lines.append("- Validation unit: one dependency group per target task.")
    lines.append("- Recommended parallelism: run one subagent per group.")
    lines.append("- Subagents should only receive generated step packets, never the checklist.")
    lines.append("- Main agent performs final checklist judging after all candidate outputs are returned.")
    lines.append("")

    lines.append("## Per-Task Validation Packets\n")
    for idx, item in enumerate(tasks, 1):
        task_id = item.get("task_id", "-")
        task = task_map.get(task_id)
        lines.append(f"### {idx}. {task_id}\n")
        if not task:
            lines.append("- Missing task.yaml\n")
            continue

        brief = task_brief(task)
        deps = as_list(item.get("depends_on"))
        step1_packet, step2_packet, step3_packet, missing_deps = step_packets(task_id, task, deps, task_map)
        dep_packets = step2_packet["dependency_tasks"]

        if packets_dir is not None:
            packets_dir.mkdir(parents=True, exist_ok=True)
            group_dir = packets_dir / task_id
            group_dir.mkdir(parents=True, exist_ok=True)
            step1_path = group_dir / "step1.json"
            step2_path = group_dir / "step2.json"
            step3_path = group_dir / "step3.json"
            output_template_path = group_dir / "subagent_outputs.template.json"
            (step1_path).write_text(json.dumps(step1_packet, ensure_ascii=False, indent=2) + "\n")
            (step2_path).write_text(json.dumps(step2_packet, ensure_ascii=False, indent=2) + "\n")
            (step3_path).write_text(json.dumps(step3_packet, ensure_ascii=False, indent=2) + "\n")
            output_template = {
                "target_task_id": task_id,
                "step1_candidate_output": "TODO",
                "step2_candidate_output": "TODO",
                "step3_candidate_output": "TODO",
                "notes": "Fill with subagent-generated outputs. Checklist must not be shown to subagents.",
            }
            output_template_path.write_text(json.dumps(output_template, ensure_ascii=False, indent=2) + "\n")
            packet_paths.append(str(group_dir))
            if manifest is not None:
                manifest["groups"].append(
                    {
                        "task_id": task_id,
                        "depends_on": deps,
                        "group_dir": str(group_dir),
                        "step_packets": {
                            "step1": str(step1_path),
                            "step2": str(step2_path),
                            "step3": str(step3_path),
                        },
                        "subagent_output_template": str(output_template_path),
                        "subagent_instruction": (
                            "Use the step packet only. Do not read or infer the checklist. "
                            "Generate one candidate output per step and write them into the output template."
                        ),
                    }
                )

        structural_notes: list[str] = []
        if not brief["checklist"]:
            structural_notes.append("No checklist: checklist-based validation is not applicable.")
        if brief["checklist"] and not brief["hidden_intent"]:
            structural_notes.append("Checklist exists but current task hidden_intent is empty.")
        if deps and missing_deps:
            structural_notes.append(f"Missing dependency task files: {', '.join(missing_deps)}.")
        if deps and not dep_packets:
            structural_notes.append("Step 2 cannot be reviewed because no dependency intent packet could be built.")
        if not deps:
            structural_notes.append("No dependencies: Step 2 is not applicable.")

        lines.append(f"- Title: `{brief['title']}`")
        lines.append(f"- Task type: `{brief['task_type']}`")
        lines.append(f"- Depends on: `{', '.join(deps) if deps else '-'}`")
        lines.append(f"- Hidden intent count: `{len(brief['hidden_intent'])}`")
        lines.append(f"- Checklist count: `{len(brief['checklist'])}`")
        lines.append("")

        lines.append("#### Checklist")
        lines.append(stringify_bullets(brief["checklist"]))
        lines.append("")

        lines.append("#### Step 1 Input: current initial_input + current hidden_intent")
        lines.append(json_block(step1_packet))
        lines.append("")

        lines.append("#### Step 2 Input: current initial_input + dependency task intents")
        lines.append(json_block(step2_packet))
        lines.append("")

        lines.append("#### Step 3 Input: current initial_input only")
        lines.append(json_block(step3_packet))
        lines.append("")

        lines.append("#### Candidate Outputs")
        lines.append("- Step 1 candidate output: TODO")
        lines.append("- Step 2 candidate output: TODO")
        lines.append("- Step 3 candidate output: TODO")
        lines.append("")

        lines.append("#### Structural Notes")
        if structural_notes:
            lines.extend(f"- {note}" for note in structural_notes)
        else:
            lines.append("- No structural blocker detected.")
        lines.append("")

        lines.append("#### Review Verdict")
        lines.append("- Step 1 Hidden-Intent Pass: TODO")
        lines.append("- Step 2 Dependency-Intent Pass: TODO")
        lines.append("- Step 3 Prompt-Only Fail: TODO")
        lines.append("- Final Verdict: TODO")
        lines.append("")

    if packet_paths:
        lines.append("## Packet Directories\n")
        for path in packet_paths:
            lines.append(f"- `{path}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n", manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a proactive task validation report.")
    parser.add_argument("--root", required=True, help="Dataset root containing episode.yaml and tasks/")
    parser.add_argument("--output", required=True, help="Output markdown report path")
    parser.add_argument(
        "--packets-dir",
        help="Optional directory to write per-group subagent input packets (step1.json, step2.json, step3.json)",
    )
    parser.add_argument(
        "--manifest",
        help="Optional path to write a manifest.json describing group packet locations and subagent handoff contract",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    packets_dir = Path(args.packets_dir).expanduser().resolve() if args.packets_dir else None
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else None
    report, manifest = build_report(root, packets_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report)
    print(f"wrote {output}")
    if packets_dir is not None:
        print(f"wrote packets under {packets_dir}")
    if manifest_path is not None and manifest is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
