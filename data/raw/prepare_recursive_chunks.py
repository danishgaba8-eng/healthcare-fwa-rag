import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

input_file = Path("data/processed/practice_all_pages.json")

with input_file.open("r", encoding="utf-8") as file:
    documents = json.load(file)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
)

all_chunks = []

for document in documents:
    page_chunks = splitter.split_text(document["text"])

    for chunk_number, chunk_text in enumerate(page_chunks, start=1):
        chunk = {
            "text": chunk_text,
            "metadata": {
                **document["metadata"],
                "chunk_number": chunk_number,
                "splitter": "recursive",
            },
        }

        all_chunks.append(chunk)

# Validate after both loops finish
if not all_chunks:
    raise ValueError("No chunks were created.")

for chunk in all_chunks:
    if not chunk["text"].strip():
        raise ValueError("An empty chunk was created.")

    if len(chunk["text"]) > 500:
        raise ValueError("A chunk exceeds 500 characters.")

# Save separately from our original baseline
output_file = Path("data/processed/practice_recursive_chunks.json")

with output_file.open("w", encoding="utf-8") as file:
    json.dump(all_chunks, file, indent=2, ensure_ascii=False)

print("Pages processed:", len(documents))
print("Recursive chunks saved:", len(all_chunks))
print("First chunk metadata:", all_chunks[0]["metadata"])
print("Saved to:", output_file)
