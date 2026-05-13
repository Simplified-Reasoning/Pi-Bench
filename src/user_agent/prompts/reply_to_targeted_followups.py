REPLY_TO_TARGETED_FOLLOWUPS_PROMPT_TEMPLATE = """## User Role
<role>
{role}
</role>

The user role describes how this user tends to speak, what tone they prefer, and how they frame requests.
Use it only to shape style, tone, wording, directness, and level of politeness.
Do NOT use the user role as a source of extra facts, preferences, requirements, goals, or background details for this reply.
If the user role mentions additional domain context or likely preferences that are not present in the target hidden intent below, do not add them.

## Latest Assistant Response
<latest_assistant_message>
{latest_assistant_message}
</latest_assistant_message>

## Hidden Intents To Answer Now
{target_hidden_intents_xml}

These targeted hidden intents are the only information content you should answer in this reply.
Treat them as the source of truth for reply content.

## Objective
Write the next user reply that answers only the hidden intents listed above.

Requirements:
1. Answer only the assistant's specific follow-up questions that correspond to the targeted hidden intents.
2. If the assistant asked a confirmation question, answer naturally in confirmation form.
3. Let the user role affect only style. It may change tone or phrasing, but it must not add new substantive information.
4. Do not add any information beyond what is needed to answer the targeted hidden intents.
5. Do not introduce other hidden intents, even if they seem related or would make the reply more complete.
6. Do not expand with role-based elaboration such as extra preferences, rationale, background, examples, or constraints unless they already appear in the targeted hidden intents.
7. Do not restate the hidden intent wording unless natural language requires a small overlap.
8. Do not mention XML, status, hidden intent, or evaluation.
9. Keep the reply concise but make sure every targeted hidden intent is answered.

## Output Format
Output exactly one plain-text user reply.
"""


def build_reply_to_targeted_followups_prompt(
    *,
    role: str,
    hidden_intents_xml: str,
    target_hidden_intents_xml: str,
    latest_assistant_message: str,
) -> str:
    return REPLY_TO_TARGETED_FOLLOWUPS_PROMPT_TEMPLATE.format(
        role=role,
        # hidden_intents_xml=hidden_intents_xml,
        target_hidden_intents_xml=target_hidden_intents_xml,
        latest_assistant_message=latest_assistant_message,
    )
