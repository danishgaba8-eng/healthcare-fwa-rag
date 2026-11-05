import json
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# 1. Configure file paths and credentials.
project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

openai_client = OpenAI()

# 2. Load all saved chunks.
input_file = (
    project_folder
    / "data"
    / "processed"
    / "practice_recursive_chunks.json"
)

with input_file.open("r", encoding="utf-8") as file:
    chunks = json.load(file)

if not chunks:
    raise ValueError("No chunks found.")

chunk_ids = [chunk["id"] for chunk in chunks]

if len(chunk_ids) != len(set(chunk_ids)):
    raise ValueError("Duplicate chunk IDs found.")

# 3. Open the existing collection.
chroma_client = chromadb.PersistentClient(
    path=str(project_folder / "data" / "chroma")
)

collection = chroma_client.get_collection(
    name="healthcare_fwa_recursive_v1",
    embedding_function=None,
)

# 4. Embed and store one batch at a time.
batch_size = 25
total_tokens = 0

for start in range(0, len(chunks), batch_size):
    batch = chunks[start:start + batch_size]
    texts = [chunk["text"] for chunk in batch]

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )

    ordered_results = sorted(
        response.data,
        key=lambda result: result.index,
    )

    embeddings = [
        result.embedding for result in ordered_results
    ]

    if len(embeddings) != len(batch):
        raise ValueError("Embedding count does not match batch size.")

    if any(len(vector) != 1536 for vector in embeddings):
        raise ValueError("Unexpected embedding dimensions.")

    collection.upsert(
        ids=[chunk["id"] for chunk in batch],
        documents=texts,
        metadatas=[chunk["metadata"] for chunk in batch],
        embeddings=embeddings,
    )

    total_tokens += response.usage.prompt_tokens
    completed = start + len(batch)

    print(f"Indexed {completed}/{len(chunks)} chunks")

# 5. Report the result.
print("Indexing complete.")
print("Input chunks:", len(chunks))
print("Records stored:", collection.count())
print("Input tokens used:", total_tokens)
