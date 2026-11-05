import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

client = OpenAI()

input_file = (
    project_folder
    / "data"
    / "processed"
    / "practice_recursive_chunks.json"
)

with input_file.open("r", encoding="utf-8") as file:
    chunks = json.load(file)

sample_chunks = chunks[:5]

texts = [chunk["text"] for chunk in sample_chunks]

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts,
)

for result in response.data:
    original_chunk = sample_chunks[result.index]

    print("Chunk ID:", original_chunk["id"])
    print("Embedding dimensions:", len(result.embedding))
    print("---")

print("Embeddings returned:", len(response.data))
print("Input tokens used:", response.usage.prompt_tokens)
