from string import Template

WORKFLOW_CORRECTION_INSTRUCTIONS = """
You are an expert in JSON workflow optimization.

--- Instructions ---
- Analyze the provided workflow JSON.
- Correct errors and optimize it according to best practices.
- Ensure:
  1. Only one "Start" node with id "-1000".
  2. At least one "End" node with id lower than any task id.
  3. Task node ids are unique and begin at "-1001" decrementing (-1001, -1002, ...).
  4. Links connect valid ids from Start/Stages/End.
  5. Start node has a "variables" array and variable names start with "$".
  6. All variable names referenced in stages start with "$" (e.g., "$PING_RESULT").
  7. JSON is strictly valid and ready for execution.
- Return only the corrected JSON, without explanations.
"""

WORKFLOW_CORRECTION_PROMPT = Template("""
${instructions}

Context:
$context

Workflow to correct:
$workflow
"""
)


def build_workflow_correction_prompt(context: str, workflow: str) -> str:
    return WORKFLOW_CORRECTION_PROMPT.safe_substitute(
        instructions=WORKFLOW_CORRECTION_INSTRUCTIONS,
        context=context,
        workflow=workflow,
    )
