# Lesson 1: every line of ingest.py

Read this beside `ingest.py` in VS Code. Every nonblank line is explained below; blank lines separate ideas. Indentation groups statements inside functions, loops and checks.

Start with the flow: discover sources -> fingerprint bytes -> extract each page -> validate -> attach metadata -> publish records and manifest.

### Line 1

```python
"""Lesson 1: turn synthetic PDF pages into source-traceable JSON records."""
```

A module docstring explains the purpose of this file. It is documentation, not a command.

### Line 3

```python
import argparse
```

Load Python's command-line argument helper, so --input and --output can be supplied by the user.

### Line 4

```python
import hashlib
```

Load hashing tools. We use a hash to fingerprint the original PDF bytes.

### Line 5

```python
import json
```

Load JSON tools for writing structured records to text files.

### Line 6

```python
import re
```

Load regular expressions for recognizing the document number in a filename.

### Line 7

```python
from datetime import datetime, timezone
```

Import the clock and UTC timezone so the manifest records an unambiguous run time.

### Line 8

```python
from io import BytesIO
```

Import an in-memory byte stream. This lets the PDF parser read the same bytes we hash.

### Line 9

```python
from pathlib import Path
```

Import Path for working with folders and files without hand-building Windows separators.

### Line 11

```python
import pypdf
```

Load the package itself so we can record its installed version.

### Line 12

```python
from pypdf import PdfReader
```

Import the PDF reader class that opens and extracts text from PDFs.

### Line 15

```python
PROJECT_ROOT = Path(__file__).resolve().parent
```

Find the folder containing this script. __file__ is this file's path, resolve() makes it absolute, and parent takes its containing folder. This keeps default paths independent of the terminal's current directory.

### Line 18

```python
def ingest(input_dir: Path, output_dir: Path) -> dict:
```

Define a reusable function. It takes input/output folder Paths and returns a dictionary. The type hints describe expected values; Python does not automatically enforce them.

### Line 19

```python
    """Validate the full batch before replacing any existing output."""
```

Document our batch policy: parse and validate all sources before starting to publish outputs.

### Line 20

```python
    pdf_paths = sorted(input_dir.glob("*.pdf"))
```

Find files ending in .pdf in the input folder and sort their names for consistent processing order. This is not a recursive search.

### Line 21

```python
    if not pdf_paths:
```

Check whether the list is empty. A missing input folder also produces no matches.

### Line 22

```python
        raise ValueError(f"No PDF files found in: {input_dir}")
```

Stop with a useful error rather than claiming success with no documents. The f-string inserts the input folder into the message.

### Line 24

```python
    records = []
```

Create an empty list for page records. Each record will contain text and metadata.

### Line 25

```python
    documents = []
```

Create a separate list for one inventory entry per document.

### Line 26

```python
    for pdf_path in pdf_paths:
```

Process each discovered PDF, one at a time.

### Line 27

```python
        match = re.match(r"fwa_(\d{2})_", pdf_path.name)
```

Match the start of a filename such as fwa_01_claims_integrity.pdf. The parentheses capture exactly two digits; the r prefix marks a raw pattern string.

### Line 28

```python
        if not match:
```

Check whether the filename failed the expected naming convention.

### Line 29

```python
            raise ValueError(f"Expected a name starting fwa_01_, etc.: {pdf_path.name}")
```

Stop if a source does not use our teaching corpus naming convention.

### Line 30

```python
        doc_id = f"FWA-{match.group(1)}"
```

Convert the captured number into an ID such as FWA-01. group(1) retrieves the first captured part of the match.

### Line 31

```python
        if any(document["doc_id"] == doc_id for document in documents):
```

Check whether any previously processed document already has this document ID. This prevents two different files from producing ambiguous document references.

### Line 32

```python
            raise ValueError(f"Duplicate document ID: {doc_id}")
```

Reject a repeated ID with an explicit error.

### Line 33

```python
        source_bytes = pdf_path.read_bytes()
```

Read the PDF into memory as bytes. For very large sources we would revisit memory use.

### Line 34

```python
        source_hash = hashlib.sha256(source_bytes).hexdigest()
```

Compute SHA-256 over those bytes and represent it as hexadecimal text. Changed PDF bytes produce a different source fingerprint; this is not encryption.

### Line 35

```python
        reader = PdfReader(BytesIO(source_bytes))
```

Give PdfReader a byte stream containing exactly the bytes that were hashed, avoiding a separate later read of a potentially changed file.

### Line 36

```python
        if reader.is_encrypted:
```

Check whether the PDF is encrypted.

### Line 37

```python
            raise ValueError(f"Encrypted PDF is not supported in this lesson: {pdf_path.name}")
```

Reject encrypted input because this introductory loader does not handle passwords.

### Line 38

```python
        if len(reader.pages) == 0:
```

Check whether the PDF exposes zero pages.

### Line 39

```python
            raise ValueError(f"PDF has no pages: {pdf_path.name}")
```

Reject an empty PDF instead of silently treating it as a useful source.

### Line 41

```python
        for page_number, page in enumerate(reader.pages, start=1):
```

Loop through pages and assign human-facing page numbers starting at 1. enumerate supplies the counter and page object together.

### Line 42

```python
            text = (page.extract_text() or "").strip()
```

Extract the page text, substitute an empty string if extraction returns None, and remove whitespace only from the beginning and end. Internal text and line breaks remain.

### Line 43

```python
            if not text:
```

Check whether usable text is absent.

### Line 44

```python
                raise ValueError(f"No text in {pdf_path.name}, page {page_number}; inspect for OCR.")
```

Stop and identify the exact page needing inspection. A scanned page may require OCR; this line does not perform OCR.

### Line 45

```python
            if "SYNTHETIC TRAINING DATA" not in text or "NOT REAL DOH DATA" not in text:
```

Require both visible synthetic labels on every page of this specific corpus. This is a corpus validation rule, not a general privacy detector.

### Line 46

```python
                raise ValueError(f"Synthetic label missing: {pdf_path.name}, page {page_number}")
```

Reject a page whose expected label is missing.

### Line 47

```python
            records.append({
```

Begin a dictionary describing one page and append it to the records list.

### Line 48

```python
                "record_id": f"{doc_id}:{source_hash}:p{page_number}",
```

Create a stable record ID from document ID, exact source hash and page number. A source replacement changes these IDs.

### Line 49

```python
                "text": text,
```

Store the extracted page content. This is the text we will clean and chunk in the next lesson.

### Line 50

```python
                "metadata": {
```

Begin the metadata dictionary: facts about the source rather than the policy content itself.

### Line 51

```python
                    "doc_id": doc_id,
```

Store the short document ID for filtering and source references.

### Line 52

```python
                    "source": pdf_path.name,
```

Store the original filename for provenance without embedding the computer's absolute path.

### Line 53

```python
                    "page": page_number,
```

Store the one-based page number for future citations.

### Line 54

```python
                    "source_sha256": source_hash,
```

Store the original PDF fingerprint so the record can be linked to an exact source version.

### Line 55

```python
                    "synthetic": True,
```

Mark that this record belongs to our checked synthetic corpus. True is a Python boolean and becomes true in JSON.

### Line 56

```python
                    "access_scope": "synthetic-training",
```

Attach a descriptive scope label for later access design. Metadata alone does not enforce authorization.

### Line 57

```python
                },
```

Close the metadata dictionary. The comma separates it from any following fields.

### Line 58

```python
            })
```

Close the page dictionary and finish the append call.

### Line 60

```python
        documents.append({
```

After all pages in one PDF have passed, append a document-level inventory entry.

### Line 61

```python
            "doc_id": doc_id,
```

Record the same document ID in the inventory.

### Line 62

```python
            "source": pdf_path.name,
```

Record the source filename in the inventory.

### Line 63

```python
            "source_sha256": source_hash,
```

Record the source hash once at document level as well as on each page.

### Line 64

```python
            "pages": len(reader.pages),
```

Record how many pages the PDF contains.

### Line 65

```python
        })
```

Close the inventory dictionary and append call.

### Line 67

```python
    manifest = {
```

After all PDFs have passed validation, begin the run manifest dictionary.

### Line 68

```python
        "schema_version": 1,
```

Give the output record contract an explicit schema version. Later incompatible field changes should change this version.

### Line 69

```python
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
```

Record the current UTC time as an ISO-formatted string. This field changes between runs even if sources do not.

### Line 70

```python
        "parser": f"pypdf=={pypdf.__version__}",
```

Record the exact parser package version used, which helps reproduce extraction behavior.

### Line 71

```python
        "document_count": len(documents),
```

Count document inventory entries.

### Line 72

```python
        "page_count": len(records),
```

Count page records. This is not the future number of retrieval chunks.

### Line 73

```python
        "documents": documents,
```

Include the complete source inventory in the manifest.

### Line 74

```python
    }
```

Close the manifest dictionary.

### Line 75

```python
    output_dir.mkdir(parents=True, exist_ok=True)
```

Create the output folder and missing parent folders; do not fail simply because it already exists.

### Line 76

```python
    page_file = output_dir / "pages.jsonl"
```

Choose the final page-record filename. The / operator joins Path components.

### Line 77

```python
    temporary_file = output_dir / "pages.jsonl.tmp"
```

Choose a temporary filename next to it, so we can finish writing before replacing the prior page file.

### Line 78

```python
    with temporary_file.open("w", encoding="utf-8", newline="\n") as stream:
```

Open the temporary file for writing using UTF-8 and consistent line endings. The with block closes it automatically.

### Line 79

```python
        for record in records:
```

Visit each validated page record.

### Line 80

```python
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
```

Serialize the dictionary to JSON and add one physical newline. JSON escapes newlines inside text strings, so each complete record remains one line. ensure_ascii=False preserves readable Unicode.

### Line 81

```python
    temporary_file.replace(page_file)
```

Replace the final page file with the completed temporary file. This protects that single file from partial writes; it does not make the manifest and page file one transaction.

### Line 82

```python
    manifest_file = output_dir / "manifest.json"
```

Choose the separate manifest filename.

### Line 83

```python
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
```

Write the manifest as indented UTF-8 JSON for easy human inspection.

### Line 84

```python
    return manifest
```

Return the manifest to the caller so it can report counts or run checks.

### Line 87

```python
def main() -> None:
```

Define the command-line entry function. -> None means it has no meaningful return value.

### Line 88

```python
    parser = argparse.ArgumentParser(description=__doc__)
```

Create a command-line parser and use the module docstring as its description.

### Line 89

```python
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "data" / "raw")
```

Accept an optional --input folder. By default use data/raw inside the project. type=Path converts supplied text into a Path object.

### Line 90

```python
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "data" / "processed")
```

Accept an optional --output folder, defaulting to data/processed.

### Line 91

```python
    args = parser.parse_args()
```

Read and validate the command-line options, storing the results on args.

### Line 92

```python
    try:
```

Begin a block whose operational failures will receive a short command-line error message.

### Line 93

```python
        manifest = ingest(args.input, args.output)
```

Run ingestion with the selected folders and keep the returned manifest.

### Line 94

```python
    except Exception as error:
```

Catch ordinary exceptions such as invalid sources, parser errors or failed writes. A production service would classify and log these separately.

### Line 95

```python
        parser.exit(1, f"Ingestion failed: {error}\n")
```

Exit with status 1 and a clear failure message. This lets a later scheduler recognize an unsuccessful run.

### Line 96

```python
    print(f"Ingested {manifest['document_count']} PDFs / {manifest['page_count']} pages.")
```

Print the verified document and page counts from the manifest.

### Line 97

```python
    print(f"Output: {args.output.resolve()}")
```

Print the resolved output folder so the user knows where the files were written.

### Line 100

```python
if __name__ == "__main__":
```

Run the following block only when Python executes this file directly, not when the tests import its functions.

### Line 101

```python
    main()
```

Call the command-line entry function.
