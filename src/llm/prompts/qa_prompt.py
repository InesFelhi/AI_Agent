from string import Template

QA_INSTRUCTIONS = """
You are an assistant for the Android automation application.

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
