from rag_pipeline import retrieve_evidence, generate_answer

question = "What was PRV00092's verified recovered amount?"

evidence = retrieve_evidence(
    question=question,
    source="fwa_01_claims_integrity.pdf",
)

result = generate_answer(
    question=question,
    evidence=evidence,
)

print("\n=== ANSWER ===")
print(result["answer"])

print("\n=== CITED SOURCES ===")

for record in result["cited_sources"]:
    metadata = record["metadata"]

    print(
        f"[{record['label']}] "
        f"{metadata['source']} — page {metadata['page']}"
    )

print("\nThese are synthetic training data, not real DOH data or policy.")
