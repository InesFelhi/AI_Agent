from pathlib import Path
from src.ingestion_pipeline.document_cleaner import DocumentCleaner

# Chemins de base
RAW_BASE = Path("data/raw")
PROCESSED_BASE = Path("data/processed")

# Mapping des dossiers raw -> processed
FOLDER_MAPPING = {
    "tasks": "task_docs",
    "app": "app_docs",
    "workflows": "workflow_docs",
}

def main():
    cleaner = DocumentCleaner()

    for raw_folder, processed_folder in FOLDER_MAPPING.items():
        raw_path = RAW_BASE / raw_folder
        processed_path = PROCESSED_BASE / processed_folder
        processed_path.mkdir(parents=True, exist_ok=True)  # Crée le dossier processed si nécessaire

        # Récupère tous les fichiers Markdown
        md_files = list(raw_path.glob("*.md"))

        for md_file in md_files:
            output_file = processed_path / md_file.name
            cleaner.clean_file(input_path=md_file, output_path=output_file)
            print(f"Cleaned: {md_file} -> {output_file}")

if __name__ == "__main__":
    main()