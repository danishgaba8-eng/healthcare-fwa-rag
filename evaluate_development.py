import json
from datetime import datetime, timezone
from pathlib import Path

from rag_pipeline import retrieve_evidence, generate_answer


project_folder = Path(__file__).resolve().parent

cases_file = (
    project_folder / "evaluation" / "development_cases.json"
)

with cases_file.open("r", encoding="utf-8") as file:
    cases = json.load(file)


source_options = {
    "1": None,
    "2": "fwa_01_claims_integrity.pdf",
    "3": "fwa_05_dental_fwa.pdf",
}

results = []
collection_name = "healthcare_fwa_policy_v2"

for case in cases:
    print(f"\n=== Running: {case['id']} ===")

    source = source_options[case["scope_choice"]]

    evidence = retrieve_evidence(
    question=case["question"],
    source=source,
    collection_name=collection_name,
)

    result = generate_answer(
        question=case["question"],
        evidence=evidence,
    )

    # Check retrieval separately from answer quality.
    expected_evidence_found = None

    if case["answerable"]:
        expected_evidence_found = any(
            record["metadata"]["source"] == case["expected_source"]
            and record["metadata"]["page"] == case["expected_page"]
            for record in evidence
        )

    case_result = {
        "case_id": case["id"],
        "collection_name": collection_name,
        "question": case["question"],
        "source_filter": source,
        "expected_answerable": case["answerable"],
        "expected_evidence_found": expected_evidence_found,
        "answer": result["answer"],
        "cited_sources": result["cited_sources"],
        "retrieved_evidence": evidence,
        "review_criteria": case["review_criteria"],
        "manual_review": "not_reviewed",
    }

    results.append(case_result)

    print("Expected evidence found:", expected_evidence_found)
    print("Answer:", result["answer"])
    print("Answer quality: awaiting manual review")


# Save the completed development run.
output_folder = project_folder / "evaluation" / "results"
output_folder.mkdir(parents=True, exist_ok=True)

run_id = datetime.now(timezone.utc).strftime(
    "%Y%m%dT%H%M%S%fZ"
)

output_file = output_folder / f"development_{run_id}.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(results, file, indent=2, ensure_ascii=False)

print("\nCases completed:", len(results))
print("Results saved to:", output_file)
