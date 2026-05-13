INTENT_SATISFACTION_JUDGE_PROMPT_TEMPLATE = """## Latest Assistant Response
<latest_assistant_message>
{latest_assistant_message}
</latest_assistant_message>

## Files Read Context
Use these file contents as additional context for judging intent satisfaction:
{files_context_xml}

## Hidden Intent Status Snapshot
Judge only the hidden intents listed here:
{status_hidden_intents_xml}

## Objective
Decide whether the latest assistant response, together with the files-read context above, already reflects each listed hidden intent.

Evaluation policy:
1. Judge from the latest assistant response and the files-read context above, not earlier turns.
2. Be strict and objective. The assistant must precisely and explicitly hit the hidden intent.
3. A hidden intent is ONLY satisfied if the assistant provides specific, detailed explanations or concrete actions in the response. Vague or generic answers do NOT count.
4. Fully trust the assistant's wording and the files-read context, but strictly evaluate the level of detail provided.
5. Do NOT call tools or check factual accuracy beyond the provided context.
6. YES means the response and context precisely address the hidden intent with specific details.
7. NO means the response and context do not precisely hit the intent, or lack specific details.

## Output Format
Output only XML blocks in this exact shape:

{output_template}
"""


def build_intent_satisfaction_judge_prompt(
    *,
    role: str,
    hidden_intents_xml: str,
    status_hidden_intents_xml: str,
    latest_assistant_message: str,
    files_context_xml: str,
    contents: list[str],
) -> str:
    output_template = "\n\n".join(
        (
            f"<c{idx}>"
            "\n<content>"
            f"\n{content}"
            "\n</content>"
            "\n<decision>"
            "\nYES or NO"
            "\n</decision>"
            f"\n</c{idx}>"
        )
        for idx, content in enumerate(contents, start=1)
    )
    return INTENT_SATISFACTION_JUDGE_PROMPT_TEMPLATE.format(
        status_hidden_intents_xml=status_hidden_intents_xml,
        latest_assistant_message=latest_assistant_message,
        files_context_xml=files_context_xml,
        output_template=output_template,
    )
