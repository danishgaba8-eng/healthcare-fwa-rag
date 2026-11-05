from pathlib import Path

import chromadb

# Locate our project folder.
project_folder = Path(__file__).resolve().parent

# Choose where Chroma will store its database files.
database_folder = project_folder / "data" / "chroma"

# Open an existing local database, or create it.
client = chromadb.PersistentClient(
    path=str(database_folder)
)

# Open an existing collection, or create it.
collection = client.get_or_create_collection(
    name="healthcare_fwa_recursive_v1",
    embedding_function=None,
    metadata={
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
        "synthetic": True,
    },
)

print("Collection:", collection.name)
print("Records stored:", collection.count())
print("Database folder:", database_folder)
