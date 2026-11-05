import hashlib
import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter


# 1. Locate the cleaned page records.
project_folder = Path(__file__).resolve().parent
processed_folder = project_folder / "data" / "processed"

input_file = processed_folder / "practice_policy_pages.json"

with input_file.open("r", encoding="utf-8") as file:
    documents = json.load(file)


# 2. Configure character-based recursive splitting.
chunk_size = 500
chunk_overlap = 100

splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
)


# 3. Split every page and create stable chunk IDs.
all_chunks = []

for document in documents:
    page_chunks = splitter.split_text(document["text"])

    for chunk_number, chunk_text in enumerate(page_chunks, start=1):
        chunk_identity = json.dumps(
            {
                "source": document["metadata"]["source"],
                "page": document["metadata"]["page"],
                "chunk_number": chunk_number,
                "text": chunk_text,
            },
            sort_keys=True,
            ensure_ascii=False,
        )

        chunk_id = hashlib.sha256(
            chunk_identity.encode("utf-8")
        ).hexdigest()

        chunk = {
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {
                **document["metadata"],
                "chunk_number": chunk_number,
                "splitter": "recursive",
            },
        }

        all_chunks.append(chunk)


# 4. Validate content and metadata.
if not all_chunks:
    raise ValueError("No chunks were created.")

for chunk in all_chunks:
    if not chunk["text"].strip():
        raise ValueError("An empty chunk was created.")

    if len(chunk["text"]) > chunk_size:
        raise ValueError("A chunk exceeds the configured size.")

    metadata = chunk["metadata"]

    if "source" not in metadata or "page" not in metadata:
        raise ValueError("A chunk is missing its source or page.")

    # Check the specific teaching section we removed.
    if (
        metadata["source"] == "fwa_01_claims_integrity.pdf"
        and metadata["page"] == 3
        and "RAG test" in chunk["text"]
    ):
        raise ValueError(
            "The removed teaching heading remains in a chunk."
        )


# 5. Check that every chunk ID is unique.
chunk_ids = [chunk["id"] for chunk in all_chunks]

if len(chunk_ids) != len(set(chunk_ids)):
    raise ValueError("Duplicate chunk IDs were created.")


# 6. Save separately from the original baseline.
processed_folder.mkdir(parents=True, exist_ok=True)

output_file = processed_folder / "practice_policy_chunks.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(
        all_chunks,
        file,
        indent=2,
        ensure_ascii=False,
    )


# 7. Display the results.
print("Chunk validation passed.")
print("Targeted teaching-heading check passed.")
print("Pages processed:", len(documents))
print("Policy chunks saved:", len(all_chunks))
print("First chunk ID:", all_chunks[0]["id"])
print("First chunk metadata:", all_chunks[0]["metadata"])
print("Saved to:", output_file)
