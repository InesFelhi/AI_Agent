"""
Task Section Extractor module.

Extracts the required sections from task documentation:
- ## Summary
- ## Detailed description
- ## Input parameters
- ## Outputs
- ## Code examples
"""

import re
from typing import Dict, Optional, List
from src.utilities.logger import get_module_logger
from src.ingestion_pipeline.vector_store import VectorStore

logger = get_module_logger("task_section_extractor")


SECTION_TITLE_ALIASES = {
    "Summary": ["Summary"],
    "Detailed description": ["Detailed description"],
    "Input parameters": ["Input parameters"],
    "Outputs": ["Output parameters"],
    "Code examples": ["Code examples", "Complete JSON example"]
}


def extract_section(text: str, section_title: str) -> Optional[str]:
    """
    Extract a specific section from markdown document.

    Args:
        text: full document text
        section_title: title of section to extract (e.g., "Summary", "Detailed description")

    Returns:
        Section content or None if not found
    """
    aliases = SECTION_TITLE_ALIASES.get(section_title, [section_title])

    for alias in aliases:
        pattern = rf"^\s*#{{1,6}}\s+{re.escape(alias)}\s*$\n?(.*?)(?=^\s*#{{1,6}}\s+|\Z)"
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            return content

    return None


def extract_task_sections(document_content: str) -> Dict[str, Optional[str]]:
    """
    Extract the required task documentation sections.

    For workflow JSON generation, we need:
    1. ## Summary
    2. ## Detailed description
    3. ## Input parameters
    4. ## Outputs
    5. ## Code examples  ← nouveau

    Args:
        document_content: full markdown document text

    Returns:
        {
            "summary": "...",
            "detailed_description": "...",
            "input_parameters": "...",
            "outputs": "...",
            "code_examples": "..."
        }
    """
    logger.info("Extracting task sections from document")

    sections = {
        "summary": extract_section(document_content, "Summary"),
        "detailed_description": extract_section(document_content, "Detailed description"),
        "input_parameters": extract_section(document_content, "Input parameters"),
        "outputs": extract_section(document_content, "Outputs"),
        "code_examples": extract_section(document_content, "Code examples"),  # nouveau
    }

    for section_name, content in sections.items():
        if content:
            logger.info(f"✓ Found section '{section_name}' ({len(content)} chars)")
        else:
            logger.warning(f"✗ Section '{section_name}' not found")

    return sections


def format_task_documentation(task_name: str, sections: Dict[str, Optional[str]]) -> str:
    """
    Format extracted sections into a clean prompt context.
    Code examples sont exclus ici — ils sont injectés séparément dans le prompt.

    Args:
        task_name: name of the task (e.g., "Cmd Stage")
        sections: dict from extract_task_sections()

    Returns:
        Formatted text ready for LLM (sans code_examples)
    """
    output = f"# {task_name}\n\n"

    if sections.get("summary"):
        output += f"## Summary\n{sections['summary']}\n\n"

    if sections.get("detailed_description"):
        output += f"## Detailed description\n{sections['detailed_description']}\n\n"

    if sections.get("input_parameters"):
        output += f"## Input parameters\n{sections['input_parameters']}\n\n"

    if sections.get("outputs"):
        output += f"## Outputs\n{sections['outputs']}\n\n"

    return output.strip()


def format_task_code_examples(
    internal_name: str,
    sections: Dict[str, Optional[str]]
) -> Optional[str]:
    """
    Formate les code examples d'une tâche pour injection dans le prompt.
    Utilise l'internal name comme label pour que le LLM fasse le lien
    avec les clés JSON qu'il doit générer.

    Args:
        internal_name: internal name de la tâche (ex: "CmdStage")
        sections: dict from extract_task_sections()

    Returns:
        Bloc formaté ou None si pas d'exemples
    """
    code_examples = sections.get("code_examples")
    if not code_examples:
        return None

    return f"### {internal_name}\n{code_examples}"


def build_workflow_context_for_tasks(
    task_names: List[str],
    store: VectorStore,
    internal_names: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Build workflow prompt context from task documentation sections.

    Args:
        task_names: list of task document titles (ex: ["Cmd Stage", "Java Code"])
        store: VectorStore instance connected to Qdrant
        internal_names: list of internal names dans le même ordre que task_names
                        (ex: ["CmdStage", "JavaCode"])
                        Si None, on utilise task_names comme labels pour les exemples.

    Returns:
        {
            "context": "texte narratif pour toutes les tâches",
            "task_examples": "exemples JSON structurés par tâche avec internal names"
        }
    """
    context_blocks = []
    examples_blocks = []

    for i, task_name in enumerate(task_names):
        document_text = store.get_document_text_by_title(task_name, doc_type="task_doc")
        if not document_text:
            logger.warning("Task document not found for title: %s", task_name)
            continue

        sections = extract_task_sections(document_text)

        # --- Contexte narratif (sans code examples) ---
        formatted = format_task_documentation(task_name, sections)
        context_blocks.append(formatted)

        # --- Code examples avec internal name comme label ---
        label = internal_names[i] if internal_names and i < len(internal_names) else task_name
        example_block = format_task_code_examples(label, sections)
        if example_block:
            examples_blocks.append(example_block)
            logger.info("✓ Code examples extracted for task: %s (label: %s)", task_name, label)
        else:
            logger.warning("✗ No code examples found for task: %s", task_name)

    return {
        "context": "\n\n".join(context_blocks).strip(),
        "task_examples": "\n\n".join(examples_blocks).strip()
    }