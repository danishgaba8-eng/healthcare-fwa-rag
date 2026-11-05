import json
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load credentials and create the OpenAI client.
project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

openai_client = OpenAI()

# 2. Load the saved chunks and select five.
input_file = (
    project_folder
    / "data"
    / "processed"
    / "practice_recursive_chunks.json"
)

with input_file.open("r", encoding="utf-8") as file:
    chunks = json.load(file)

sample_chunks = chunks[:5]

# 3. Generate embeddings for the five texts.
texts = [chunk["text"] for chunk in sample_chunks]

response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=texts,
)

# Put results in input order using their returned indexes.
ordered_results = sorted(
    response.data,
    key=lambda result: result.index,
)

embeddings = [result.embedding for result in ordered_results]

if len(embeddings) != len(sample_chunks):
    raise ValueError("Embedding count does not match chunk count.")

# 4. Open the existing ChromaDB collection.
chroma_client = chromadb.PersistentClient(
    path=str(project_folder / "data" / "chroma")
)

collection = chroma_client.get_collection(
    name="healthcare_fwa_recursive_v1",
    embedding_function=None,
)

# 5. Store the IDs, text, metadata, and vectors together.
collection.upsert(
    ids=[chunk["id"] for chunk in sample_chunks],
    documents=texts,
    metadatas=[chunk["metadata"] for chunk in sample_chunks],
    embeddings=embeddings,
)

print("Sample chunks submitted:", len(sample_chunks))
print("Records stored:", collection.count())
