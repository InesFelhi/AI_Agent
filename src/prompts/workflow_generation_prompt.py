from string import Template

WORKFLOW_GENERATION_INSTRUCTIONS = """
You are an expert automation assistant for Android workflows.

--- Instructions ---
- Generate a valid workflow JSON strictly following these rules:
  1. There must be exactly one "Start" node with id "-1000".
  2. Task nodes (CmdStage, AppStage, etc.) must use ids starting at "-1001" and decrementing (-1001, -1002, ...).
  3. End nodes must use ids lower than any task id (e.g., "-2000"), and you can have one or more End nodes.
  4. Each task type (CmdStage, AppStage, etc.) can be empty if not used.
  5. "Links" must connect valid ids from Start/Stages/End.
  6. Start node must include a "variables" array where each variable name starts with "$".
  7. All variable names used in workflow stages must begin with "$" (e.g., "$PING_RESULT").
  8. Do not include any explanation, comment or markdown.
  9. Output must be valid strict JSON only.
"""

WORKFLOW_GENERATION_PROMPT = Template("""
${instructions}

Context:
$context

User instruction:
$instruction

Examples:
$examples

--- Expected format ---
{
  "Start": [{"id": "-1000"}],
  "End": [{"id": "-1001"}],
  "CmdStage": [],
  "AppStage": [],
  "Links": [
    {"from": "-1000", "to": "-1001"}
  ]
}
"""
)


def build_workflow_generation_prompt(context: str, instruction: str, examples: str = "") -> str:
    return WORKFLOW_GENERATION_PROMPT.safe_substitute(
        instructions=WORKFLOW_GENERATION_INSTRUCTIONS,
        context=context,
        instruction=instruction,
        examples=examples,
    )
