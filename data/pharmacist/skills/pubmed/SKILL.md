---
name: pubmed
description: Use when the task needs biomedical literature retrieval through PubMed-style search, especially for oncology, pharmacy, drug development, or PROTAC research in the user_medical_zh dataset.
---

# PubMed

Use this skill when the core need is biomedical literature search.

## When to use

- The user asks for recent or representative medical literature.
- The task requires authoritative sources for treatment pathways, precedents, or research status.
- The answer should cite PMID, DOI, journal, or year when possible.

## Workflow

1. Convert the request into 2-4 search concepts: disease, modality, endpoint, and constraint.
2. Prefer review articles for fast orientation and primary studies for specific claims.
3. Record citation anchors such as title, journal, year, DOI, or PMID.
4. Distinguish established findings from early or limited evidence.
5. If evidence is sparse or conflicting, say so explicitly.

## Output shape

- Provide a compact literature map, not an unstructured paper dump.
- Group by theme, mechanism, treatment stage, or precedent family when useful.
