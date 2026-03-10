from pathlib import Path

from src.ingestion_pipeline.document_cleaner import DocumentCleaner


def main():
    cleaner = DocumentCleaner()

    input_path = Path("data/raw/tasks/current-location.md")

    output_path = Path(
        "data/processed/task_docs/current-location.md"
    )

    cleaner.clean_file(
        input_path=input_path,
        output_path=output_path
    )

    print("Document cleaned successfully!")
    print(f"Input : {input_path}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()