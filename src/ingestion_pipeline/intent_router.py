"""Intent routing helpers for user questions in AI Agent.

Goal: classify user questions into doc type categories (app_doc/task_doc/workflow_doc)
for contextual retrieval.
"""
from typing import Literal

DocType = Literal["app_doc", "task_doc", "workflow_doc", "general"]

_APP_KEYWORDS = [
    "installation", "installer", "installation", "web portal", "mobile app", "device", "permission", "connect", "connexion", "configuration", "setup", "dashboard"
]
_TASK_KEYWORDS = [
    "task", "action", "http request", "http", "requête", "requête http", "cmd", "command", "sleep", "click", "screen automator", "ntp", "start", "end", "send sms", "task stage", "parameter", "input", "output", "paramètre"
]
_WORKFLOW_KEYWORDS = [
    "workflow", "flow", "graph", "link", "sequence", "branche", "branch", "condition", "start node", "end node", "execution", "run", "logic", "variable", "resolve", "exécuter"
]


def classify_question_type(question: str) -> DocType:
    """Classify user question toward doc type for retrieval.

    A fuzzy keyword-based fallback. In real use, replace with a lightweight LLM
    classification or an embedding-based classifier for better accuracy.
    """
    if not question or not question.strip():
        return "general"

    q = question.lower()

    app_score = sum(1 for k in _APP_KEYWORDS if k in q)
    task_score = sum(1 for k in _TASK_KEYWORDS if k in q)
    wf_score = sum(1 for k in _WORKFLOW_KEYWORDS if k in q)

    best = max((app_score, "app_doc"), (task_score, "task_doc"), (wf_score, "workflow_doc"))
    score, doc_type = best

    # If no strong signal, treat as general and search all.
    if score == 0:
        return "general"
    return doc_type


def get_filter_for_question(question: str):
    """Return filter dict for vector store based on question classification."""
    doc_type = classify_question_type(question)
    if doc_type == "general":
        return None
    return {"type_doc": doc_type}
