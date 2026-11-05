from pathlib import Path

import chromadb

project_folder = Path(__file__).resolve().parent

client = chromadb.PersistentClient(
    path=str(project_folder / "data" / "chroma")
)

collection = client.get_collection(
    name="healthcare_fwa_recursive_v1",
    embedding_function=None,
)

records = collection.get(
    limit=1,
    include=["documents", "metadatas", "embeddings"],
)

print("Total records:", collection.count())
print("Retrieved ID:", records["ids"][0])
print("Metadata:", records["metadatas"][0])
print("Embedding dimensions:", len(records["embeddings"][0]))
print("Text preview:", records["documents"][0][:200])
