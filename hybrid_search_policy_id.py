import json
import re
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


project_folder = Path(__file__).resolve().parent
chunk_file = project_folder / "data" / "processed" / "practice_policy_chunks.json"

with chunk_file.open("r", encoding="utf-8") as file:
    chunks = json.load(file)

policy_id = "DE-P03"

exact_id = re.compile(
    rf"(?<![\w-]){re.escape(policy_id)}(?![\w-])",
    re.IGNORECASE,
)

heading = re.compile(
    rf"^\s*{re.escape(policy_id)}[ \t]*\|",
    re.IGNORECASE | re.MULTILINE,
)

matches = []

for chunk in chunks:
    text = chunk["text"]

    if exact_id.search(text):
        is_heading = bool(heading.search(text))
        matches.append((is_heading, chunk))

# Put the policy heading ahead of cross-references.
matches.sort(key=lambda match: match[0], reverse=True)

print("Policy ID:", policy_id)
print("Exact matches:", len(matches))

for rank, (is_heading, chunk) in enumerate(matches[:3], start=1):
    metadata = chunk["metadata"]

    print(f"\n=== Result {rank} ===")
    print("Source:", metadata["source"])
    print("Page:", metadata["page"])
    print("Policy heading found:", is_heading)
    print(chunk["text"])

# Search the same corpus by meaning.
load_dotenv(project_folder / ".env")

question = f"What does {policy_id} say about repeated tooth restorations?"

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
question_vector = embeddings.embed_query(question)

client = chromadb.PersistentClient(
    path=str(project_folder / "data" / "chroma")
)

collection = client.get_collection(
    name="healthcare_fwa_policy_v2",
    embedding_function=None,
)

dense_results = collection.query(
    query_embeddings=[question_vector],
    n_results=5,
    include=["metadatas"],
)

dense_ids = dense_results["ids"][0]
keyword_ids = [chunk["id"] for _, chunk in matches]
chunks_by_id = {chunk["id"]: chunk for chunk in chunks}

# Combine the rankings using reciprocal rank fusion (RRF).
rank_constant = 60
scores = {}

for ranked_ids in (dense_ids, keyword_ids):
    for rank, chunk_id in enumerate(ranked_ids, start=1):
        contribution = 1 / (rank_constant + rank)
        scores[chunk_id] = scores.get(chunk_id, 0) + contribution

hybrid_ids = sorted(scores, key=scores.get, reverse=True)

print("\nQuestion:", question)
print("\n=== HYBRID RESULTS ===")

for rank, chunk_id in enumerate(hybrid_ids[:3], start=1):
    chunk = chunks_by_id[chunk_id]
    metadata = chunk["metadata"]

    dense_rank = dense_ids.index(chunk_id) + 1 if chunk_id in dense_ids else None
    keyword_rank = (
        keyword_ids.index(chunk_id) + 1 if chunk_id in keyword_ids else None
    )

    print(f"\nResult {rank}: {metadata['source']}, page {metadata['page']}")
    print("Vector rank:", dense_rank)
    print("Keyword rank:", keyword_rank)
    print(chunk["text"])
def contains_policy_body(chunk):
    text = chunk["text"]
    heading_match = heading.search(text)

    if heading_match is None:
        return False

    # Skip the rest of the heading line, which contains the policy title.
    lines_after_match = text[heading_match.end():].splitlines()
    body_lines = lines_after_match[1:]

    return any(line.strip() for line in body_lines)


# Rerank the same three keyword candidates for a controlled comparison.
candidates = keyword_ids[:3]

reranked_ids = sorted(
    candidates,
    key=lambda chunk_id: contains_policy_body(chunks_by_id[chunk_id]),
    reverse=True,
)

print("\n=== KEYWORD CANDIDATES AFTER RERANKING ===")

for rank, chunk_id in enumerate(reranked_ids, start=1):
    chunk = chunks_by_id[chunk_id]
    metadata = chunk["metadata"]

    print(f"\nResult {rank}: {metadata['source']}, page {metadata['page']}")
    print("Original keyword rank:", keyword_ids.index(chunk_id) + 1)
    print("Text below policy heading:", contains_policy_body(chunk))
    print(chunk["text"])
