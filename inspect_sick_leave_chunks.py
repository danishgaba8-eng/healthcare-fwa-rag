from pathlib import Path

import chromadb


project_folder = Path(__file__).resolve().parent

client = chromadb.PersistentClient(
    path=str(project_folder / "data" / "chroma")
)

collection = client.get_collection(
    name="healthcare_fwa_policy_v2",
    embedding_function=None,
)

records = collection.get(
    where={"source": "fwa_03_sick_leave_fwa.pdf"},
    include=["documents", "metadatas"],
)

page_one_chunks = [
    (metadata["chunk_number"], text)
    for text, metadata in zip(records["documents"], records["metadatas"])
    if metadata["page"] == 1
]

page_one_chunks.sort(key=lambda item: item[0])

rule_phrase = "resolve overlapping intervals into unique absence days"
rule_chunks = []

for chunk_number, text in page_one_chunks:
    normalized_text = " ".join(text.lower().split())

    if rule_phrase in normalized_text:
        rule_chunks.append(chunk_number)

    print(f"\n=== Page 1, chunk {chunk_number} ===")
    print(text)

print("\nPage 1 chunks inspected:", len(page_one_chunks))
print("Chunks containing the complete rule phrase:", rule_chunks)
# Chunk 3 was the first result in the sick-leave similarity search.
anchor_chunk_number = 3
neighbor_radius = 1

expanded_chunks = [
    (chunk_number, text)
    for chunk_number, text in page_one_chunks
    if abs(chunk_number - anchor_chunk_number) <= neighbor_radius
]

print("\n=== EXPANDED EVIDENCE ===")

for chunk_number, text in expanded_chunks:
    role = "anchor" if chunk_number == anchor_chunk_number else "neighbor"

    print(f"\nPage 1, chunk {chunk_number} ({role})")
    print(text)

expanded_rule_found = any(
    rule_phrase in " ".join(text.lower().split())
    for _, text in expanded_chunks
)

print("\nExpanded chunk numbers:", [
    chunk_number for chunk_number, _ in expanded_chunks
])
print("Complete overlap rule found:", expanded_rule_found)
