import json
from pathlib import Path

input_file = Path("data/processed/practice_all_pages.json")

with input_file.open("r", encoding="utf-8") as file:
    documents = json.load(file)

chunk_size = 500
chunk_overlap = 100
step = chunk_size - chunk_overlap

all_chunks = []

for document in documents:
    text = document["text"]

    for chunk_number, start in enumerate(
        range(0, len(text), step), start=1
    ):
        chunk_text = text[start:start + chunk_size]

        chunk = {
            "text": chunk_text,
            "metadata": {
                **document["metadata"],
                "chunk_number": chunk_number,
                "start_character": start,
            },
        }

        all_chunks.append(chunk)

        if start + chunk_size >= len(text):
            break
for chunk in all_chunks:
    if not chunk["text"].strip():
        raise ValueError("An empty chunk was created.")

    if len(chunk["text"]) > chunk_size:
        raise ValueError("A chunk exceeds the configured size.")

    metadata = chunk["metadata"]

    if "source" not in metadata or "page" not in metadata:
        raise ValueError("A chunk is missing its source or page.")

print("Chunk validation passed.")

print("Pages processed:", len(documents))
print("Chunks created:", len(all_chunks))
print("First chunk metadata:", all_chunks[0]["metadata"])
output_file = Path("data/processed/practice_chunks.json")

with output_file.open("w", encoding="utf-8") as file:
    json.dump(all_chunks, file, indent=2, ensure_ascii=False)

print("Chunks saved:", len(all_chunks))
print("Saved to:", output_file)
