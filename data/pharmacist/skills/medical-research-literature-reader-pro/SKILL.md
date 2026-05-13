---
name: medical-research-literature-reader-pro
description: Use when the task requires reading, synthesizing, or comparing biomedical literature, especially for paper breakdowns, literature summaries, evidence chains, or precedent analysis in the user_medical_zh dataset.
---

# Medical Research Literature Reader Pro

Use this skill for biomedical paper reading and synthesis.

## When to use

- The user asks for a literature summary or research landscape.
- The task is to break down a single paper's scientific question, validation logic, methods, and take-away.
- The task needs evidence-chain reasoning rather than generic domain explanation.

## Workflow

1. Identify whether the task is literature-wide or paper-specific.
2. Preserve traceable bibliographic information when available.
3. Start from the scientific question, then the key evidence, then what remains unproven.
4. Prefer the most decision-relevant figures, methods, or results instead of averaging across all details.
5. End with a short reusable take-away when the user is preparing a report or meeting note.

## Output shape

- For landscape tasks: organize into 3-4 main lines with progress, limits, and open questions.
- For paper tasks: separate scientific question, validation logic, methods, and strongest evidence.
- If inputs are incomplete, request high-information additions such as title, DOI, full text, or key figures.
