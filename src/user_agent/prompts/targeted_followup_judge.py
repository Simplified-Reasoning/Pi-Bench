TARGETED_FOLLOWUP_JUDGE_PROMPT_TEMPLATE = """## Latest Assistant Response
<latest_assistant_message>
{latest_assistant_message}
</latest_assistant_message>

## Hidden Intents Still Not Provided
Judge only the hidden intents listed here:
{status_hidden_intents_xml}

## Objective
Decide whether the latest assistant response contains a clear follow-up question that is specifically about each listed hidden intent.

Evaluation policy:
1. Judge only from the latest assistant response, not earlier turns. Consider all follow-up questions/requests/action suggestions inside it, not only the last sentence.
2. YES means the assistant explicitly asks about that hidden intent, asks a very close confirmation question about it, or proposes/requests concrete next steps that directly correspond to it.
3. NO means the question is missing, vague, generic, or does not clearly target that hidden intent.
4. Generic prompts like "anything else?" or "do you want to add more?" must be NO.
5. A question must clearly get the point. Broad topic overlap is not enough.
6. If decision is YES, also label the follow-up style:
   - Clarify: ask for missing information when the user must choose from many valid directions.
   - Options: ask the user to choose from one likely option or a short list of explicit options.
7. Output <style> only when decision is YES. Do not output <style> for NO.

## Output Format
Output only XML blocks in this exact shape:

{output_template}
"""


def build_targeted_followup_judge_prompt(
    *,
    role: str,
    hidden_intents_xml: str,
    status_hidden_intents_xml: str,
    latest_assistant_message: str,
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
            "\n<style>"
            "\nClarify or Options"
            "\n</style>"
            f"\n</c{idx}>"
        )
        for idx, content in enumerate(contents, start=1)
    )
    return TARGETED_FOLLOWUP_JUDGE_PROMPT_TEMPLATE.format(
        # role=role,
        # hidden_intents_xml=hidden_intents_xml,
        status_hidden_intents_xml=status_hidden_intents_xml,
        latest_assistant_message=latest_assistant_message,
        output_template=output_template,
    )
