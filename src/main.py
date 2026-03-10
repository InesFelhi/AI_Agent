
from pathlib import Path
from src.ingestion_pipeline.chunker import Chunker
from src.ingestion_pipeline.schemas import Chunk
import uuid

# Fichier Markdown à tester
MD_FILE = Path("data/processed/task_docs/http-request.md")

def main():
    if not MD_FILE.exists():
        print(f"File does not exist: {MD_FILE}")
        return

    text = MD_FILE.read_text(encoding="utf-8")
    print(f"\nRead Markdown file: {MD_FILE.name} ({len(text)} characters)\n")

    # Initialisation du chunker
    chunker = Chunker(max_chunk_size=200, overlap=50)

    # Metadata de test
    metadata = {
        "document_id": str(uuid.uuid4()),
        "type_doc": "task_doc",
        "file_name": MD_FILE.name
    }

    # Création des chunks
    chunks = chunker.chunk(text, metadata)
    print(f"Total chunks created: {len(chunks)}\n{'='*50}\n")

    # Affichage de tous les chunks
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} | ID: {chunk.id} | Words: {len(chunk.content.split())}")
        print(chunk.content)
        print("-"*80)

if __name__ == "__main__":
    main()