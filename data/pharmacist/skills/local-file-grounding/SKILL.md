---
name: local-file-grounding
description: Use when the task must read or write local task materials such as txt, md, csv, json, svg, or output files, and the response should be grounded in those files rather than generic knowledge.
---

# Local File Grounding

Use this skill for local task-directory execution.

## When to use

- The task names local files that must be read first.
- The answer should use task materials such as txt, md, csv, json, png, or svg.
- The task requires writing a result file back into the task directory.

## Workflow

1. Inspect the task directory and identify the required inputs and outputs.
2. Read the named files before producing conclusions.
3. Quote or summarize only what the files support.
4. If writing output is required, create the file in the requested location and keep the content aligned with the read materials.
5. Do not fabricate specifics that are not grounded in the local files.
