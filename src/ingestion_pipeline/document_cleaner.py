"""
document_cleaner.py

Markdown Document Cleaner for AI Agent RAG processing.

Responsibilities:
- Parse raw Markdown
- Preserve header hierarchy
- Convert tables to readable semantic text
- Preserve lists (including nested lists)
- Preserve code block content (remove fences)
- Preserve inline code as semantic content
- Remove markdown noise
- Output clean Markdown ready for chunking & embedding
- Use module-specific logger for logging in production

Usage:
    from pathlib import Path
    from src.ingestion_pipeline.document_cleaner import DocumentCleaner

    cleaner = DocumentCleaner()
    cleaner.clean_file(
        input_path=Path("raw_task.md"),
        output_path=Path("clean_task.md")
    )
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from markdown_it import MarkdownIt
from markdown_it.token import Token
from src.utilities.logger import get_module_logger  # Corrected logger import

# Module-specific logger
logger = get_module_logger("document_cleaner")


class DocumentCleaner:
    """Clean and normalize Markdown documents for RAG processing with nested lists and inline code preservation."""

    def __init__(self) -> None:
        """
        Initialize the Markdown parser with table support enabled.
        """
        self._parser = MarkdownIt("commonmark").enable("table")

    # ---------------- Public API ----------------
    def clean_file(self, input_path: Path, output_path: Path) -> None:
        """
        Clean a Markdown file and write the processed version.

        Args:
            input_path (Path): Path to raw Markdown file
            output_path (Path): Path to cleaned Markdown output

        Raises:
            FileNotFoundError: If the input file does not exist
            Exception: If any unexpected error occurs during cleaning
        """
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

    # ---------------- Internal Processing ----------------
    def _clean_markdown(self, text: str) -> str:
        """
        Process raw Markdown text and return cleaned version.

        Args:
            text (str): Raw Markdown content

        Returns:
            str: Cleaned Markdown text
        """
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

            # ---------- CODE BLOCK (FENCED) ----------
            if token.type == "fence":
                code_content = token.content.strip()
                if code_content:
                    cleaned_lines.append(code_content)
                    cleaned_lines.append("")
                i += 1
                continue

            i += 1

        return "\n".join(cleaned_lines).strip()

    # ---------------- Inline Code Handling ----------------
    def _extract_inline_code(self, token: Token) -> str:
        """
        Preserve inline code by converting backticks to single quotes.

        Args:
            token (Token): Markdown inline token

        Returns:
            str: String with inline code preserved as semantic content
        """
        content = token.content
        for child in token.children or []:
            if child.type == "code_inline":
                content = content.replace(f"`{child.content}`", f"'{child.content}'")
        return content.strip()

    # ---------------- List Extraction (Nested Support) ----------------
    def _extract_list(
        self,
        tokens: List[Token],
        start_index: int,
        ordered: bool = False,
        indent: int = 0
    ) -> Tuple[List[str], int]:
        """
        Extract a bullet or ordered list from tokens, supporting nested lists.

        Args:
            tokens (List[Token]): List of Markdown tokens
            start_index (int): Current index in tokens
            ordered (bool): True if ordered list, False if bullet
            indent (int): Number of spaces for nested indentation

        Returns:
            Tuple[List[str], int]: List of lines and new index in tokens
        """
        lines: List[str] = []
        i = start_index
        counter = 1
        list_close_type = "ordered_list_close" if ordered else "bullet_list_close"

        while i < len(tokens) and tokens[i].type != list_close_type:
            if tokens[i].type == "list_item_open":
                item_content = ""
                j = i + 1
                while tokens[j].type != "list_item_close":
                    if tokens[j].type == "paragraph_open":
                        item_content = self._extract_inline_code(tokens[j + 1])
                        j += 3
                    elif tokens[j].type in ("bullet_list_open", "ordered_list_open"):
                        nested_ordered = tokens[j].type == "ordered_list_open"
                        nested_lines, new_j = self._extract_list(tokens, j, nested_ordered, indent + 2)
                        lines.extend(nested_lines)
                        j = new_j
                        continue
                    else:
                        j += 1

                prefix = (" " * indent + f"{counter}. " if ordered else " " * indent + "- ")
                if item_content:
                    lines.append(prefix + item_content)
                counter += 1
                i = j + 1
                continue
            i += 1

        return lines, i + 1

    # ---------------- Table Extraction ----------------
    def _extract_table(self, tokens: List[Token], start_index: int) -> Tuple[str, int]:
        """
        Convert Markdown table into readable semantic text.

        Args:
            tokens (List[Token]): List of Markdown tokens
            start_index (int): Current index in tokens

        Returns:
            Tuple[str, int]: String representation of table and new index
        """
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