import os
from string import Template

ATLASS_VERSION = os.getenv("ATLASS_VERSION", "1.0.0")

QA_INSTRUCTIONS = f"""
You are Atlass, an assistant for the Android automation application.
Assistant version: {ATLASS_VERSION}

--- Instructions ---
- Answer the user's question using the provided context.
- Be concise and precise, do not give unnecessary explanations.
- Use examples from workflows if needed.
"""

QA_PROMPT = Template("""
${instructions}

Context:
$context

User question:
$question
"""
)


def build_qa_prompt(context: str, question: str) -> str:
    return QA_PROMPT.safe_substitute(
        instructions=QA_INSTRUCTIONS,
        context=context,
        question=question,
    )
