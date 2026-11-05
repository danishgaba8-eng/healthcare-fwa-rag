import hashlib
import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter


# 1. Load the page records created during ingestion.
input_file = Path("data/processed/practice_all_pages.json")

with input_file.open("r", encoding="utf-8") as file:
    documents = json.load(file)


# 2. Configure splitting.
# These sizes are measured in characters, not model tokens.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
)


# 3. Split every page and preserve its source metadata.
all_chunks = []

for document in documents:
    page_chunks = splitter.split_text(document["text"])

    for chunk_number, chunk_text in enumerate(page_chunks, start=1):

        # Create a consistent representation of this chunk.
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

        # Convert that representation into a stable fingerprint.
        chunk_id = hashlib.sha256(
            chunk_identity.encode("utf-8")
        ).hexdigest()

        # Store the ID, content, and source details together.
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


# 4. Validate all chunks before saving.
if not all_chunks:
    raise ValueError("No chunks were created.")

for chunk in all_chunks:
    if not chunk["text"].strip():
        raise ValueError("An empty chunk was created.")

    if len(chunk["text"]) > 500:
        raise ValueError("A chunk exceeds 500 characters.")

    metadata = chunk["metadata"]

    if "source" not in metadata or "page" not in metadata:
        raise ValueError("A chunk is missing its source or page.")

chunk_ids = [chunk["id"] for chunk in all_chunks]

if len(chunk_ids) != len(set(chunk_ids)):
    raise ValueError("Duplicate chunk IDs were created.")


# 5. Save the validated chunks.
output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "practice_recursive_chunks.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(all_chunks, file, indent=2, ensure_ascii=False)


# 6. Display the results.
print("Chunk validation passed.")
print("Pages processed:", len(documents))
print("Recursive chunks saved:", len(all_chunks))
print("First chunk ID:", all_chunks[0]["id"])
print("First chunk metadata:", all_chunks[0]["metadata"])
print("Saved to:", output_file)
