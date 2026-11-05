from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


project_folder = Path(__file__).resolve().parent
load_dotenv(project_folder / ".env")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    collection_name="healthcare_fwa_policy_v2",
    persist_directory=str(project_folder / "data" / "chroma"),
    embedding_function=embeddings,
    create_collection_if_not_exists=False,
)

question = (
    "Two active sick-leave certificates for the same person cover "
    "September 10 through 12 and September 12 through 15. "
    "How many distinct calendar days do they cover together?"
)

# Embed once so both searches use the same question vector.
question_vector = embeddings.embed_query(question)

rule_phrase = "resolve overlapping intervals into unique absence days"

for k in (3, 5):
    documents = vector_store.similarity_search_by_vector(
        embedding=question_vector,
        k=k,
    )

    print(f"\n=== Top {k} results ===")
    rule_ranks = []

    for rank, document in enumerate(documents, start=1):
        metadata = document.metadata

        # Collapse line breaks and spaces before checking the phrase.
        normalized_text = " ".join(document.page_content.lower().split())

        if rule_phrase in normalized_text:
            rule_ranks.append(rank)

        print(f"\nResult {rank}: {metadata['source']}, page {metadata['page']}")
        print(document.page_content)

    print("\nOverlap rule phrase found:", bool(rule_ranks))
    print("Ranks containing the phrase:", rule_ranks)
