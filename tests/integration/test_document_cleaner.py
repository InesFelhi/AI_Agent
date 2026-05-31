"""
Test DocumentCleaner on all raw documentation folders.

This test:
- Cleans all markdown files in data/raw
- Stores cleaned versions in data/processed
- Verifies output files are created
"""

from pathlib import Path
import pytest

from src.ingestion_pipeline.document_cleaner import DocumentCleaner


RAW_BASE = Path("data/raw")
PROCESSED_BASE = Path("data/processed")


FOLDER_MAPPING = {
    "tasks": "task_docs",
    "app": "app_docs",
    "workflows": "workflow_docs",
}


@pytest.mark.parametrize("raw_folder,processed_folder", FOLDER_MAPPING.items())
def test_clean_all_markdown_files(raw_folder: str, processed_folder: str) -> None:
    """
    Clean all markdown files from a specific raw folder
    and verify cleaned files are generated.
    """

    cleaner = DocumentCleaner()

    raw_path = RAW_BASE / raw_folder
    processed_path = PROCESSED_BASE / processed_folder

    assert raw_path.exists(), f"Raw folder not found: {raw_path}"

    md_files = list(raw_path.glob("*.md"))
    assert md_files, f"No markdown files found in {raw_path}"

    for md_file in md_files:
        output_file = processed_path / md_file.name

        cleaner.clean_file(
            input_path=md_file,
            output_path=output_file
        )

        assert output_file.exists(), f"Cleaned file not created: {output_file}"
        assert output_file.read_text(encoding="utf-8").strip() != "", \
            f"Cleaned file is empty: {output_file}"