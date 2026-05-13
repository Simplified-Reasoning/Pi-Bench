REPLY_FIRST_UNMET_INTENT_PROMPT_TEMPLATE = """## User Role
You are given the following user role:
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

## Hidden Intent To Reveal Now
{target_hidden_intent_xml}

This target hidden intent is the only new information content you should reveal in this reply.
Treat it as the source of truth for reply content.

## Objective
Write the next user reply.

Requirements:
1. Start by revealing the target hidden intent in natural user language.
2. Let the user role affect only style. It may change tone or phrasing, but it must not add new substantive information.
3. Do not add explanations, examples, preferences, constraints, motivations, background, or suggestions unless they are already contained in the target hidden intent.
4. Do not pull in content from other hidden intents, even if it would sound helpful or role-consistent.
5. Do not copy the hidden intent verbatim. Rephrase it naturally while preserving its full meaning.
6. Do not mention XML, status, hidden intent, or evaluation.
7. Keep the reply concise but complete enough to cover the target hidden intent.

## Output Format
Output exactly one plain-text user reply.
"""


def build_reply_first_unmet_intent_prompt(
    *,
    role: str,
    hidden_intents_xml: str,
    target_hidden_intent_xml: str,
    latest_assistant_message: str,
) -> str:
    return REPLY_FIRST_UNMET_INTENT_PROMPT_TEMPLATE.format(
        role=role,
        # hidden_intents_xml=hidden_intents_xml,
        target_hidden_intent_xml=target_hidden_intent_xml,
        latest_assistant_message=latest_assistant_message,
    )
