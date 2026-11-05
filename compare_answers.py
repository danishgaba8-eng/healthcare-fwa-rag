from rag_pipeline import retrieve_evidence, generate_answer


question = "What was PRV00092's verified recovered amount?"

collection_names = [
    "healthcare_fwa_recursive_v1",
    "healthcare_fwa_policy_v2",
]

for collection_name in collection_names:
    evidence = retrieve_evidence(
        question=question,
        source="fwa_01_claims_integrity.pdf",
        n_results=3,
        collection_name=collection_name,
    )

    result = generate_answer(
        question=question,
        evidence=evidence,
    )

    print(f"\n=== {collection_name} ===")
    print(result["answer"])

    print("\nCited sources:")

    for record in result["cited_sources"]:
        metadata = record["metadata"]

        print(
            f"[{record['label']}] "
            f"{metadata['source']} — page {metadata['page']}"
        )

print("\nSynthetic training data, not real DOH data or policy.")
