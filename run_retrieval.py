from rag_pipeline import retrieve_evidence

evidence = retrieve_evidence(
    question="What was PRV00092's verified recovered amount?",
    source="fwa_01_claims_integrity.pdf",
    n_results=3,
)

print("Evidence records returned:", len(evidence))

for record in evidence:
    print(
        record["label"],
        record["metadata"]["source"],
        record["metadata"]["page"],
    )
