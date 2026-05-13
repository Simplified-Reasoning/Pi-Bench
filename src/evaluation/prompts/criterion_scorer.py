from __future__ import annotations

from html import escape

CRITERION_SCORER_PROMPT_TEMPLATE = """## Full Hidden Intent
These are all hidden intents for the current task:
{hidden_intents_xml}

## Interaction History
<history>
{history}
</history>

## Checklist Criteria
{criteria_list}

## Objective
You are a strict evaluator.
For each checklist criterion, decide whether the interaction history clearly satisfies it.

Scoring rules:
1. Use ONLY evidence from the interaction history.
2. Score YES only when the criterion is clearly satisfied.
3. Score NO when evidence is missing, ambiguous, or contradicted.
4. Do not guess.

## Output Format
Output only the XML blocks below. Keep each criterion text exactly the same as given.
Each score must be YES or NO.

{output_template}
"""


def build_criterion_scorer_prompt(
    *,
    role: str,
    hidden_intents_xml: str,
    history: str,
    criteria: list[str],
) -> str:
    escaped_criteria = [escape(item, quote=False) for item in criteria]
    criteria_list = "\n".join(f"{idx}. {item}" for idx, item in enumerate(escaped_criteria, start=1))
    output_template = "\n\n".join(
        (
            f"<c{idx}>"
            "\n<criterion>"
            f"\n{item}"
            "\n</criterion>"
            "\n<score>"
            "\nYES or NO"
            "\n</score>"
            f"\n</c{idx}>"
        )
        for idx, item in enumerate(escaped_criteria, start=1)
    )
    return CRITERION_SCORER_PROMPT_TEMPLATE.format(
        # role=role,
        hidden_intents_xml=hidden_intents_xml,
        history=history,
        criteria_list=criteria_list,
        output_template=output_template,
    )
