---
name: local-web-search
description: Use when the task needs targeted web searching for public products, formulation benchmarks, or comparable market examples, especially in the user_medical_zh formulation tasks.
---

# Local Web Search

Use this skill for focused public-web discovery.

## When to use

- The user wants existing products or comparable public examples.
- The task needs topical web search before deeper page reading.
- The work is benchmark-oriented rather than literature-oriented.

## Workflow

1. Search with product name, dosage form, route, ingredient, brand, and benchmark terms.
2. Prefer pages that expose concrete formulation or product details.
3. De-duplicate near-identical hits.
4. Extract comparable fields such as form, active, concentration, route, and claimed use.
5. Return a short comparison set instead of a long raw search list.
