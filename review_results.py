"""Record human review decisions without changing the original RAG results."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_FOLDER = Path(__file__).resolve().parent
STATUSES = {"1": "pass", "2": "needs_improvement", "3": "fail"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="A specific development results JSON file")
    args = parser.parse_args()

    if args.input is not None:
        input_file = args.input.resolve()
    else:
        candidates = sorted(
            (PROJECT_FOLDER / "evaluation" / "results").glob("development_*.json")
        )
        if not candidates:
            raise ValueError("No development results found. Run evaluate_development.py first.")
        input_file = candidates[-1]

    with input_file.open("r", encoding="utf-8") as file:
        results = json.load(file)

    if not isinstance(results, list) or not results:
        raise ValueError("Expected a nonempty JSON list of evaluation results.")

    for case in results:
        if not isinstance(case, dict) or not all(
            field in case for field in ("case_id", "question", "answer", "review_criteria")
        ):
            raise ValueError("A result is missing required review fields.")

    print("Reviewing:", input_file)
    print("These decisions are entered by you; this script does not grade answers.")

    for case in results:
        print(f"\n=== {case['case_id']} ===")
        print("Question:", case["question"])
        print("Answer:", case["answer"])
        print("Expected evidence found:", case.get("expected_evidence_found"))
        print("Review criteria:")
        for criterion in case["review_criteria"]:
            print("-", criterion)

        print("\nRetrieved evidence:")
        for record in case.get("retrieved_evidence", []):
            metadata = record["metadata"]
            print(f"[{record['label']}] {metadata['source']} - page {metadata['page']}")
            print(record["text"])

        choice = input("\n1 = pass, 2 = needs improvement, 3 = fail: ").strip()
        while choice not in STATUSES:
            choice = input("Please enter 1, 2, or 3: ").strip()

        notes = input("Review notes: ").strip()
        while not notes:
            notes = input("Please explain your decision: ").strip()

        case["manual_review"] = {
            "status": STATUSES[choice],
            "notes": notes,
            "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_file = input_file.with_name(f"reviewed_{input_file.stem}_{run_id}.json")
    with output_file.open("x", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    print("\nReview summary:")
    for status in STATUSES.values():
        count = sum(case["manual_review"]["status"] == status for case in results)
        print(f"{status}: {count}")
    print("Reviewed copy saved to:", output_file)
    print("Original results unchanged.")


if __name__ == "__main__":
    main()
