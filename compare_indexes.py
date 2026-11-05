from rag_pipeline import retrieve_evidence

question = "What was PRV00092's verified recovered amount?"

collection_names = [
    "healthcare_fwa_recursive_v1",
    "healthcare_fwa_policy_v2",
]

for collection_name in collection_names:
    print(f"\n=== {collection_name} ===")

    evidence = retrieve_evidence(
        question=question,
        source="fwa_01_claims_integrity.pdf",
        n_results=3,
        collection_name=collection_name,
    )

    for record in evidence:
        metadata = record["metadata"]

        print(
            f"\n[{record['label']}] "
            f"{metadata['source']} — page {metadata['page']}"
        )
        print(record["text"])
