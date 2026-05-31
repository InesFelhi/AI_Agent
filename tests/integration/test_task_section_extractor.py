"""
Test script for task section extraction.
"""

from pathlib import Path
import pytest
from src.ingestion_pipeline.task_section_extractor import (
    extract_task_sections,
    format_task_documentation
)

# Test with cmd.md - use relative path
cmd_file = Path(__file__).parent.parent / "data" / "raw" / "tasks" / "cmd.md"

# Skip if test data doesn't exist
if not cmd_file.exists():
    pytest.skip(f"Test data not found: {cmd_file}", allow_module_level=True)

print("=" * 80)
print(f"Testing with: {cmd_file.name}")
print("=" * 80)

# Read the document
content = cmd_file.read_text(encoding="utf-8")

# Extract sections
sections = extract_task_sections(content)

# Display results
print("\n[EXTRACTED SECTIONS]\n")
for section_name, section_content in sections.items():
    if section_content:
        print(f"{'=' * 40}")
        print(f"Section: {section_name.upper()}")
        print(f"{'=' * 40}")
        print(section_content[:500])  # First 500 chars
        if len(section_content) > 500:
            print(f"\n... ({len(section_content) - 500} more characters)")
        print()
    else:
        print(f"✗ Section '{section_name}' NOT FOUND\n")

# Format for LLM
print("\n" + "=" * 80)
print("FORMATTED OUTPUT FOR LLM")
print("=" * 80)
formatted = format_task_documentation("Cmd Stage", sections)
print(formatted[:1500])  # First 1500 chars
if len(formatted) > 1500:
    print(f"\n... ({len(formatted) - 1500} more characters)")
