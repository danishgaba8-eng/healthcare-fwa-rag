import json
from pathlib import Path
from pypdf import PdfReader

input_folder = Path("data/raw")
pdf_files = sorted(input_folder.glob("*.pdf"))
if not pdf_files:
    raise ValueError(f"No PDF files found in: {input_folder}")

documents = []

for pdf_path in pdf_files:
    reader = PdfReader(pdf_path)
    print(f"Reading {pdf_path.name}: {len(reader.pages)} pages")

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            raise ValueError(
                f"No text extracted from {pdf_path.name}, page {page_number}"
                )

        document = {
            "text": page_text,
            "metadata": {
                "source": pdf_path.name,
                "page": page_number,
                "synthetic": True,
            },
        }

        documents.append(document)

output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "practice_all_pages.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(documents, file, indent=2, ensure_ascii=False)

print("PDFs processed:", len(pdf_files))
print("Page records saved:", len(documents))
print("Saved to:", output_file)
