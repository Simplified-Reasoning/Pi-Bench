---
name: proactive-task-validator
description: Use this skill when validating proactive task datasets, especially when you need to check whether a task's checklist is supported by current hidden intent, dependency intents, and not satisfiable from the current prompt alone. Generates a validation report for a dataset root containing episode.yaml and tasks/*/task.yaml.
---

# Proactive Task Validator

Use this skill when the user wants a **complete proactive task validation workflow**, not just a structural lint pass.

This skill is for validating whether a dataset really satisfies the three-step task validation flow:

1. current `initial_input` + current `hidden_intent` should satisfy checklist
2. current `initial_input` + dependency task intents should satisfy checklist
3. current `initial_input` only should **not** satisfy checklist

## Core Isolation Rule

Validation must be organized by **dependency group**, not by isolated task file order.

A group means:

- one target task to validate
- all of its dependency tasks needed to construct the historical intent context

To avoid checklist leakage:

- subagents that generate candidate outputs must **not** see checklist
- checklist is only used in the final judging phase
- output generation and checklist judging must be separated

When the platform supports subagents, this skill should use **parallel subagents** at the group level.

## What this skill does

This skill combines:

1. automatic extraction of validation packets
2. structural checks
3. Codex review of Step 1 / Step 2 / Step 3
4. a final written verdict for each task

The script is only the first half of the workflow.
The second half is mandatory: Codex must read the generated packet and complete the review verdicts.

## When to use it

Use this skill when a dataset follows this structure:

- `episode.yaml`
- `tasks/<task_id>/task.yaml`

The script is best for:

- proactive `test` tasks
- dependency-heavy `regular` tasks
- dataset audits before writing benchmark reports

## Required Workflow

### Phase 1. Generate validation packets

Run:

```bash
python skills/proactive-task-validator/scripts/validate_task_dataset.py \
  --root /abs/path/to/dataset \
  --output /abs/path/to/report.md \
  --packets-dir /abs/path/to/packets \
  --manifest /abs/path/to/manifest.json
```

This produces a report with:

- dataset summary
- task index
- per-task Step 1 / Step 2 / Step 3 input packets
- structural warnings
- empty verdict slots
- one packet directory per task group with:
  - `step1.json`
  - `step2.json`
  - `step3.json`
  - `subagent_outputs.template.json`

### Phase 2. Build dependency groups

Before judging, Codex must group tasks by validation target.

For each target task:

- include the current task
- include every task in its `depends_on`
- build one isolated validation packet for that group

Do not merge multiple unrelated groups into one reasoning context if that would leak checklist expectations across tasks.

### Phase 3. Run subagents in parallel for group outputs

When subagents are available, use them.

This is not optional hand-holding from the user.
After packet generation, Codex should proceed to subagent execution automatically.
Do not wait for the user to remind you to launch subagents.

Required execution pattern:

1. Spawn one subagent per validation group.
2. Run multiple groups in parallel when possible.
3. Give each subagent only:
   - current task `initial_input`
   - current task `hidden_intent` when needed for Step 1
   - dependency task intents when needed for Step 2
   - current task `initial_input` only for Step 3
4. Do **not** give the subagent the checklist.
5. Ask the subagent to produce candidate outputs for Step 1 / Step 2 / Step 3.
6. Ask the subagent to write those outputs back into that group's `subagent_outputs.template.json`.

Write-scope rule for this phase:

- generation subagents may write only to their own group's `subagent_outputs.template.json`
- generation subagents must not edit `task.yaml`, `episode.yaml`, or other dataset source files
- final judgment and dataset edits belong to the main agent or later repair workers

This phase is for output generation only.

The reason for this design:

- it prevents checklist contamination
- it avoids one task's judging criteria leaking into another task's generation process
- it keeps each dependency chain locally coherent

### Phase 4. Perform final checklist judging centrally

After all subagents finish producing outputs, the main Codex agent performs the final checklist judging.

At this stage, Codex may read:

- the generated candidate outputs
- the target task checklist
- the dependency packet

Codex then reviews each task and replaces the `TODO` verdicts.

For each task:

1. Read the task packet in the generated report.
2. Read the candidate outputs from the subagent.
3. Read the original `task.yaml` if needed for context.
4. Judge:
   - whether Step 1 should pass
   - whether Step 2 should pass
   - whether Step 3 should fail
5. Write short notes explaining the reason.
6. Replace:
   - `Step 1 Hidden-Intent Pass: TODO`
   - `Step 2 Dependency-Intent Pass: TODO`
   - `Step 3 Prompt-Only Fail: TODO`
   - `Final Verdict: TODO`

Checklist judging must be explicit and itemized.

Do not only say "roughly satisfies the checklist" or "fails because information is missing".
For each validated task, include a point-by-point checklist review that states:

- which checklist bullets are satisfied
- which checklist bullets are not satisfied
- the concrete reason for each unsatisfied bullet
- when useful, which candidate output sentence or behavior supports the judgment

The expected final labels are:

- `Pass`
- `Fail`
- `N/A`

If you want to pre-fill returned subagent outputs back into the report before final judgment, run:

```bash
python skills/proactive-task-validator/scripts/merge_subagent_outputs.py \
  --report /abs/path/to/report.md \
  --manifest /abs/path/to/manifest.json \
  --output /abs/path/to/reviewed_report.md
```

### Phase 5. Produce a final reviewed report

The final deliverable is not the raw script output.
The final deliverable is the reviewed Markdown report with:

- group-scoped generation results
- verdicts filled in
- short notes added
- itemized checklist review per validated task
- optional dataset-level summary at the top

If the user asked to validate only part of a dataset, the reviewed report must clearly mark the scope as partial.
Do not imply that unreviewed tasks were fully validated.

### Phase 6. Provide repair guidance

Validation does not stop at verdicts when the user is auditing or improving a dataset.

After producing the reviewed report, Codex should also provide:

1. repair angles
2. a revised task design proposal

This should be written either:

- as a dedicated follow-up section in the reviewed report, or
- as a separate Markdown remediation note next to the report

The repair guidance should be concrete, not generic.

For each failed or weak task, include:

- what is structurally wrong
- whether the issue is missing checklist, weak hidden intent, weak dependency reconstruction, or prompt leakage
- the minimum change that would fix it
- an example revised dependency / hidden_intent / checklist direction when possible
- whether the task should instead be reclassified as `setup`, `regular`, or non-proactive

### Phase 7. Apply the repairs

When the user wants dataset improvement rather than review only, Codex should continue after proposing the repair plan.

The default behavior is:

1. generate the reviewed report
2. generate concrete repair guidance
3. have the main agent apply the approved repair direction to the dataset files in scope
4. if feasible, re-run validation on the updated tasks

Do not stop after listing suggested fixes when the user clearly wants the dataset updated.
The main agent should make the edits directly unless the user explicitly asks to stop at recommendations.

If multiple repair options exist:

- choose the minimum viable fix that restores validation quality
- note the chosen option in the report or remediation note
- then apply that option to the task files

If the repair would materially change task intent or benchmark scope, call that out before editing.

Subagent policy in this phase:

- repair worker subagents may edit dataset files, including `task.yaml` and closely related local task materials, when the write ownership is clearly partitioned
- do not let multiple repair workers edit the same file concurrently
- the main agent remains responsible for final integration, consistency review, and re-validation

## What the script validates automatically

- `episode.yaml` exists
- task files exist
- dependency targets exist
- counts of hidden intents and checklist items
- file read and file write declarations
- whether dependency intents are available for Step 2

## What Codex must judge manually

The script does **not** replace the semantic validation step.

Codex must still determine:

- whether current hidden intent is sufficient for checklist completion
- whether dependency intents are sufficient for checklist completion
- whether prompt-only information is insufficient

This manual judgment is part of the skill, not an optional extra.

Subagents are used to generate isolated candidate answers.
The main agent is responsible for final scoring and verdict writing.

## Output

The final reviewed report should contain:

- dataset summary
- per-task summary table
- per-task three-step validation packet
- per-task generated candidate outputs
- structural warnings
- filled verdicts
- short review notes
- optional final counts such as:
  - how many tasks satisfy `Pass / Pass / Fail`
  - which tasks fail Step 2
  - which tasks are not good proactive tasks

When the user is using validation to improve the dataset, also include:

- repair angles
- proposed revised task designs
- explicit notes about which changes are minimal fixes versus larger redesigns
- the actual applied updates when Codex proceeds to edit the dataset

## Notes

- For `setup` tasks without checklist, the script marks checklist-based validation as not applicable.
- For tasks without dependencies, Step 2 is marked as not applicable.
- If the dataset uses extra fields, the script preserves only the fields needed for validation flow review.
- When the user asks for “validation”, do not stop after generating the packet. Finish the review.
- If subagents are available, default to group-level parallel execution so checklist context does not leak into generation.

## Codex Orchestration Protocol

When Codex is actually running this skill end-to-end, use this protocol:

1. Run `validate_task_dataset.py` with:
   - `--root`
   - `--output`
   - `--packets-dir`
   - `--manifest`
2. Read `manifest.json`.
3. Select validation targets in batches of `3`.
4. Spawn `3` subagents in parallel, one per target group.
5. For each subagent:
   - provide only that group's `step1.json`, `step2.json`, `step3.json`
   - explicitly forbid reading checklist
   - ask for three candidate outputs only
6. Wait for the batch to finish.
7. Write the returned outputs into that group's `subagent_outputs.template.json`.
8. After all groups are complete, run `merge_subagent_outputs.py`.
9. The main agent then reads the merged report and performs final checklist judging.
10. Export the reviewed report.
11. Without waiting for additional user prompting, provide repair guidance for any failed, weak, or non-applicable tasks when the user's goal is dataset improvement.
12. Unless the user asked for review only, apply the repair plan to the in-scope dataset files.
13. If practical, re-run validation for the updated tasks and attach the post-fix result.

Hard rule:

- Never give checklist to the generation subagent.
- Checklist belongs only to the main agent in the final judging stage.
- Do not stop at packet generation or verdict filling when the user clearly wants an actionable dataset audit.
- Do not stop at repair suggestions when the user wants the dataset fixed; the main agent should carry the repair through to file updates.
- Do not allow generation subagents to modify dataset source files; only repair-stage workers may do that under explicit ownership.
