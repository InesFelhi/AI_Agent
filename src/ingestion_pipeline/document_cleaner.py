# document_cleaner_final.py
"""
Markdown Document Cleaner for AI Agent RAG processing.

Responsibilities:
- Parse raw Markdown
- Preserve header hierarchy
- Convert tables to readable semantic text
- Preserve lists (including nested lists)
- Preserve code block content
- Preserve inline code as semantic content
- Convert Mermaid and flowchart diagrams into readable semantic text
- Remove Markdown noise
- Output clean Markdown ready for chunking & embedding
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from markdown_it import MarkdownIt
from markdown_it.token import Token
import re
from src.utilities.logger import get_module_logger

logger = get_module_logger("document_cleaner")

class DocumentCleaner:
    """Clean and normalize Markdown documents for RAG processing."""

    def __init__(self) -> None:
        self._parser = MarkdownIt("commonmark").enable("table")

    # ---------- Public API ----------
    def clean_file(self, input_path: Path, output_path: Path) -> None:
        logger.info("Cleaning started: %s", input_path)
        if not input_path.exists():
            logger.error("File not found: %s", input_path)
            raise FileNotFoundError(f"{input_path} not found")
        try:
            raw_text = input_path.read_text(encoding="utf-8")
            cleaned_text = self._clean_markdown(raw_text)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(cleaned_text, encoding="utf-8")
            logger.info("Cleaning completed: %s", output_path)
        except Exception:
            logger.exception("Unexpected error during document cleaning")
            raise

    # ---------- Core Cleaning ----------
    def _clean_markdown(self, text: str) -> str:
        tokens: List[Token] = self._parser.parse(text)
        cleaned_lines: List[str] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            # ---------- HEADERS ----------
            if token.type == "heading_open":
                level = int(token.tag[1])
                title = tokens[i + 1].content.strip()
                if title:
                    cleaned_lines.append(f"{'#' * level} {title}")
                    cleaned_lines.append("")
                i += 3
                continue

            # ---------- PARAGRAPHS ----------
            if token.type == "paragraph_open":
                paragraph = self._extract_inline_code(tokens[i + 1])
                if paragraph:
                    cleaned_lines.append(paragraph)
                    cleaned_lines.append("")
                i += 3
                continue

            # ---------- BULLET LIST ----------
            if token.type == "bullet_list_open":
                list_text, new_index = self._extract_list(tokens, i)
                cleaned_lines.extend(list_text)
                cleaned_lines.append("")
                i = new_index
                continue

            # ---------- ORDERED LIST ----------
            if token.type == "ordered_list_open":
                list_text, new_index = self._extract_list(tokens, i, ordered=True)
                cleaned_lines.extend(list_text)
                cleaned_lines.append("")
                i = new_index
                continue

            # ---------- TABLE ----------
            if token.type == "table_open":
                table_text, new_index = self._extract_table(tokens, i)
                if table_text:
                    cleaned_lines.append(table_text)
                    cleaned_lines.append("")
                i = new_index
                continue

            # ---------- CODE BLOCK / MERMAID ----------
            if token.type == "fence":
                code_content = token.content.strip()
                info = token.info.strip()
                if info.lower() == "mermaid":
                    diagram_text = self._convert_mermaid(code_content)
                    if diagram_text:
                        cleaned_lines.append(diagram_text)
                        cleaned_lines.append("")
                else:
                    if code_content:
                        # Preserve backticks with code language marker
                        if info:
                            cleaned_lines.append(f"```{info}")
                        else:
                            cleaned_lines.append("```")
                        cleaned_lines.append(code_content)
                        cleaned_lines.append("```")
                        cleaned_lines.append("")
                i += 1
                continue

            i += 1

        return "\n".join(cleaned_lines).strip()

    # ---------- Inline Code ----------
    def _extract_inline_code(self, token: Token) -> str:
        content = token.content
        for child in token.children or []:
            if child.type == "code_inline":
                content = content.replace(f"{child.content}", f"{child.content}")
        return content.strip()

    # ---------- List Extraction ----------
    def _extract_list(
        self, tokens: List[Token], start_index: int, ordered: bool = False, indent: int = 0
    ) -> Tuple[List[str], int]:
        lines: List[str] = []
        i = start_index
        counter = 1
        list_close_type = "ordered_list_close" if ordered else "bullet_list_close"

        while i < len(tokens) and tokens[i].type != list_close_type:
            if tokens[i].type == "list_item_open":
                item_content = ""
                nested_items: List[str] = []  # Store nested items separately
                j = i + 1
                while tokens[j].type != "list_item_close":
                    if tokens[j].type == "paragraph_open":
                        item_content = self._extract_inline_code(tokens[j + 1])
                        j += 3
                    elif tokens[j].type in ("bullet_list_open", "ordered_list_open"):
                        nested_ordered = tokens[j].type == "ordered_list_open"
                        nested_lines, new_j = self._extract_list(tokens, j, nested_ordered, indent + 2)
                        nested_items.extend(nested_lines)  # Store nested items
                        j = new_j
                        continue
                    else:
                        j += 1
                # Add parent item first, then nested items
                prefix = (" " * indent + f"{counter}. " if ordered else " " * indent + "- ")
                if item_content:
                    lines.append(prefix + item_content)
                # Then add nested items (maintains parent -> children order)
                lines.extend(nested_items)
                counter += 1
                i = j + 1
                continue
            i += 1

        return lines, i + 1

    # ---------- Table Extraction ----------
    def _extract_table(self, tokens: List[Token], start_index: int) -> Tuple[str, int]:
        rows: List[List[str]] = []
        i = start_index
        while i < len(tokens) and tokens[i].type != "table_close":
            if tokens[i].type == "tr_open":
                row: List[str] = []
                j = i + 1
                while tokens[j].type != "tr_close":
                    if tokens[j].type == "inline":
                        row.append(tokens[j].content.strip())
                    j += 1
                rows.append(row)
                i = j
            i += 1

        if not rows:
            return "", i

        headers = rows[0]
        data_rows = rows[1:]
        lines: List[str] = []

        for row in data_rows:
            elements = []
            for idx, value in enumerate(row):
                if idx < len(headers):
                    elements.append(f"{headers[idx]}: {value}")
            lines.append("- " + " | ".join(elements))

        return "\n".join(lines), i + 1

    # ---------- Mermaid / Flowchart Conversion ----------
    def _convert_mermaid(self, diagram: str) -> str:
        nodes = {}
        relations = []

        lines = diagram.splitlines()

        # Extract nodes
        node_pattern = re.compile(r'(\w+)\s*\["?(.*?)"?\]')
        for line in lines:
            line = line.strip()
            match = node_pattern.search(line)
            if match:
                node_id = match.group(1)
                label = match.group(2)
                label = re.sub(r"<br\s*/?>", " ", label)
                label = label.replace('"', "").strip()
                nodes[node_id] = label

        # Extract edges
        edge_pattern = re.compile(r'(\w+)\s*[-.=]+>\s*(\w+)')
        for line in lines:
            line = line.strip()
            match = edge_pattern.search(line)
            if match:
                left = match.group(1)
                right = match.group(2)
                left_label = nodes.get(left, left)
                right_label = nodes.get(right, right)
                relations.append(f"{left_label} → {right_label}")

        # Build semantic text
        output = []
        if nodes:
            output.append("Diagram Nodes:")
            for node_id, label in nodes.items():
                output.append(f"- {node_id}: {label}")
            output.append("")

        if relations:
            output.append("Workflow Flow:")
            for rel in relations:
                output.append(f"- {rel}")

        if output:
            return "\n".join(output)
        return "Diagram describing workflow steps."