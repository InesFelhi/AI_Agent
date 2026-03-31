from string import Template

# ----------------------------
# Workflow Generation Prompt
# ----------------------------
WORKFLOW_GENERATION_PROMPT = Template("""
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
""")

# ----------------------------
# Workflow Correction Prompt
# ----------------------------
WORKFLOW_CORRECTION_PROMPT = Template("""
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

Context:
$context

Workflow to correct:
$workflow
""")

# ----------------------------
# QA Prompt
# ----------------------------
QA_PROMPT = Template("""
You are an assistant for the Android automation application.

--- Instructions ---
- Answer the user's question using the provided context.
- Be concise and precise, do not give unnecessary explanations.
- Use examples from workflows if needed.

Context:
$context

User question:
$question
""")

# ----------------------------
# Job Question Prompt
# ----------------------------
JOB_QUESTION_PROMPT = Template("""
You are a job assistant that answers user questions about job workflows and operations (not generating new workflows).

--- Instructions ---
- Read the user question and context.
- Provide a concise, factual answer about the current job workflow, status, or parameters.
- If the user asks to create or modify a workflow, answer that this endpoint provides information and guidance only, and the workflow creation API must be used.
- Output plain text (no JSON object), no markdown, no extra commentary.

Context:
$context

User question:
$question
""")

# ----------------------------
# Functions to build prompts
# ----------------------------

def build_workflow_generation_prompt(context: str, instruction: str, examples: str = "") -> str:
    """Compose the workflow generation prompt with context, instruction, and optional examples."""
    return WORKFLOW_GENERATION_PROMPT.safe_substitute(
        context=context,
        instruction=instruction,
        examples=examples,
    )

def build_workflow_correction_prompt(context: str, workflow: str) -> str:
    """Compose the workflow correction prompt."""
    return WORKFLOW_CORRECTION_PROMPT.safe_substitute(
        context=context,
        workflow=workflow,
    )

def build_qa_prompt(context: str, question: str) -> str:
    """Compose the QA prompt."""
    return QA_PROMPT.safe_substitute(
        context=context,
        question=question,
    )

def build_job_question_prompt(context: str, question: str) -> str:
    """Compose the job question prompt."""
    return JOB_QUESTION_PROMPT.safe_substitute(
        context=context,
        question=question,
    )