"""
Task Section Extractor module.

Extracts ONLY the required sections from task documentation:
- ## Summary
- ## Detailed description
- ## Input parameters
- ## Outputs

These 4 sections are essential for workflow JSON generation.
"""

import re
from typing import Dict, Optional, List
from src.utilities.logger import get_module_logger
from src.ingestion_pipeline.vector_store import VectorStore

logger = get_module_logger("task_section_extractor")


def extract_section(text: str, section_title: str) -> Optional[str]:
    """
    Extract a specific section from markdown document.
    
    Args:
        text: full document text
        section_title: title of section to extract (e.g., "Summary", "Detailed description")
    
    Returns:
        Section content or None if not found
    """
    # Regex to find ## Section Title and capture content until next ## or end of file
    pattern = rf"^##\s+{re.escape(section_title)}\s*$(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    
    if match:
        content = match.group(1).strip()
        return content
    return None


def extract_task_sections(document_content: str) -> Dict[str, Optional[str]]:
    """
    Extract the 4 required task documentation sections.
    
    For workflow JSON generation, we ONLY need:
    1. ## Summary
    2. ## Detailed description
    3. ## Input parameters
    4. ## Outputs
    
    Args:
        document_content: full markdown document text
    
    Returns:
        {
            "summary": "...",
            "detailed_description": "...",
            "input_parameters": "...",
            "outputs": "..."
        }
    """
    logger.info("Extracting task sections from document")
    
    sections = {
        "summary": extract_section(document_content, "Summary"),
        "detailed_description": extract_section(document_content, "Detailed description"),
        "input_parameters": extract_section(document_content, "Input parameters"),
        "outputs": extract_section(document_content, "Outputs")
    }
    
    # Log what we found
    for section_name, content in sections.items():
        if content:
            logger.info(f"✓ Found section '{section_name}' ({len(content)} chars)")
        else:
            logger.warning(f"✗ Section '{section_name}' not found")
    
    return sections


def format_task_documentation(task_name: str, sections: Dict[str, Optional[str]]) -> str:
    """
    Format extracted sections into a clean prompt context.
    
    Args:
        task_name: name of the task (e.g., "Cmd Stage")
        sections: dict from extract_task_sections()
    
    Returns:
        Formatted text ready for LLM
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


def build_workflow_context_for_tasks(task_names: List[str], store: VectorStore) -> str:
    """
    Build a workflow prompt context from task documentation sections.

    Args:
        task_names: list of task document titles to include
        store: VectorStore instance connected to Qdrant

    Returns:
        Combined formatted documentation text for the given tasks.
    """
    blocks = []

    for task_name in task_names:
        document_text = store.get_document_text_by_title(task_name, doc_type="task_doc")
        if not document_text:
            logger.warning("Task document not found for title: %s", task_name)
            continue

        sections = extract_task_sections(document_text)
        formatted = format_task_documentation(task_name, sections)
        blocks.append(formatted)

    return "\n\n".join(blocks).strip()
