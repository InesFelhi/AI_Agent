from pathlib import Path
import hashlib
from src.ingestion_pipeline.ingestion_service import clean_documents, chunk_documents


def test_clean_documents_and_chunk_documents_compute_doc_hash(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    source_file = raw_dir / "task-sample.md"
    source_file.write_text("# Sample Task\n\nThis is a sample task document.\n", encoding="utf-8")

    processed_files = clean_documents(raw_dir, processed_dir)

    assert len(processed_files) == 1
    processed_path = processed_files[0]

    assert processed_path.exists()
    assert processed_path.read_text(encoding="utf-8").strip() != ""

    expected_hash = hashlib.md5(source_file.read_bytes()).hexdigest()

    chunks = chunk_documents(processed_files, {"type_doc": "task_doc"}, max_chunk_size=100, overlap=10)
    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk.metadata["document_id"] == processed_path.stem
        assert chunk.metadata["type_doc"] == "task_doc"
