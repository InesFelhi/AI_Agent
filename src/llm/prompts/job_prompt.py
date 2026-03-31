from string import Template

JOB_QUESTION_INSTRUCTIONS = """
You are a job assistant that answers user questions about job workflows and operations (not generating new workflows).

--- Instructions ---
- Read the user question and context.
- Provide a concise, factual answer about the current job workflow, status, or parameters.
- If the user asks to create or modify a workflow, answer that this endpoint provides information and guidance only, and the workflow creation API must be used.
- Output plain text (no JSON object), no markdown, no extra commentary.
"""

JOB_QUESTION_PROMPT = Template("""
${instructions}

Context:
$context

User question:
$question
"""
)


def build_job_question_prompt(context: str, question: str) -> str:
    return JOB_QUESTION_PROMPT.safe_substitute(
        instructions=JOB_QUESTION_INSTRUCTIONS,
        context=context,
        question=question,
    )
