import json
from pathlib import Path

project_folder = Path(__file__).resolve().parent
processed_folder = project_folder / "data" / "processed"

input_file = processed_folder / "practice_all_pages.json"

with input_file.open("r", encoding="utf-8") as file:
    documents = json.load(file)

cleaned_documents = []
pages_changed = 0

for document in documents:
    cleaned_document = document.copy()
    metadata = document["metadata"]

    if (
        metadata["source"] == "fwa_01_claims_integrity.pdf"
        and metadata["page"] == 3
    ):
        marker = "\nRAG test\n"

        if marker not in document["text"]:
            raise ValueError(
                "Expected RAG test heading was not found."
            )

        policy_text = document["text"].split(marker, 1)[0].rstrip()

        if "Verified recovered amount" not in policy_text:
            raise ValueError("Recovery metric heading was lost.")

        if "12,000 SCU" not in policy_text:
            raise ValueError("Recovery amount was lost.")

        cleaned_document["text"] = policy_text
        cleaned_document["metadata"] = {
            **metadata,
            "preprocessing": "remove_claims_rag_test_v1",
        }

        pages_changed += 1

    cleaned_documents.append(cleaned_document)

if pages_changed != 1:
    raise ValueError(
        f"Expected to change one page, changed {pages_changed}."
    )

output_file = processed_folder / "practice_policy_pages.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(
        cleaned_documents,
        file,
        indent=2,
        ensure_ascii=False,
    )

print("Page records preserved:", len(cleaned_documents))
print("Pages changed:", pages_changed)
print("Saved to:", output_file)
