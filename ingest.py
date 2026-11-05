"""Lesson 1: turn synthetic PDF pages into source-traceable JSON records."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pypdf
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parent


def ingest(input_dir: Path, output_dir: Path) -> dict:
    """Validate the full batch before replacing any existing output."""
    pdf_paths = sorted(input_dir.glob("*.pdf"))
    if not pdf_paths:
        raise ValueError(f"No PDF files found in: {input_dir}")

    records = []
    documents = []
    for pdf_path in pdf_paths:
        match = re.match(r"fwa_(\d{2})_", pdf_path.name)
        if not match:
            raise ValueError(f"Expected a name starting fwa_01_, etc.: {pdf_path.name}")
        doc_id = f"FWA-{match.group(1)}"
        if any(document["doc_id"] == doc_id for document in documents):
            raise ValueError(f"Duplicate document ID: {doc_id}")
        source_bytes = pdf_path.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        reader = PdfReader(BytesIO(source_bytes))
        if reader.is_encrypted:
            raise ValueError(f"Encrypted PDF is not supported in this lesson: {pdf_path.name}")
        if len(reader.pages) == 0:
            raise ValueError(f"PDF has no pages: {pdf_path.name}")

        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                raise ValueError(f"No text in {pdf_path.name}, page {page_number}; inspect for OCR.")
            if "SYNTHETIC TRAINING DATA" not in text or "NOT REAL DOH DATA" not in text:
                raise ValueError(f"Synthetic label missing: {pdf_path.name}, page {page_number}")
            records.append({
                "record_id": f"{doc_id}:{source_hash}:p{page_number}",
                "text": text,
                "metadata": {
                    "doc_id": doc_id,
                    "source": pdf_path.name,
                    "page": page_number,
                    "source_sha256": source_hash,
                    "synthetic": True,
                    "access_scope": "synthetic-training",
                },
            })

        documents.append({
            "doc_id": doc_id,
            "source": pdf_path.name,
            "source_sha256": source_hash,
            "pages": len(reader.pages),
        })

    manifest = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parser": f"pypdf=={pypdf.__version__}",
        "document_count": len(documents),
        "page_count": len(records),
        "documents": documents,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    page_file = output_dir / "pages.jsonl"
    temporary_file = output_dir / "pages.jsonl.tmp"
    with temporary_file.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    temporary_file.replace(page_file)
    manifest_file = output_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "data" / "raw")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "processed")
    args = parser.parse_args()
    try:
        manifest = ingest(args.input, args.output)
    except Exception as error:
        parser.exit(1, f"Ingestion failed: {error}\n")
    print(f"Ingested {manifest['document_count']} PDFs / {manifest['page_count']} pages.")
    print(f"Output: {args.output.resolve()}")


if __name__ == "__main__":
    main()
