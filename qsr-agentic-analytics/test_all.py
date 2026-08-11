from pathlib import Path

from orchestrator import answer_question


QUESTIONS = [
    "What were the total revenue, orders, and average order value for the last 3 months?",
    "Which are the top 5 and bottom 5 stores by revenue?",
    "How does revenue and average order value vary across different channels?",
    "Which are the top 5 SKUs by quantity sold and revenue?",
    "Which cities have shown a decline in revenue over the last 3 months?",
    "How does weekend performance compare with weekdays?",
    "How does festive-period performance compare with normal periods?",
    "Which stores have consistently declined in the last 3 months, and what are the key reasons?",
]


def run_all_tests() -> None:
    results = []
    success_count = 0

    for question in QUESTIONS:
        result = answer_question(question)
        category = result.get("category", "unknown")
        insight = result.get("insight", "")

        if category != "unknown":
            success_count += 1

        line = [
            f"Question: {question}",
            f"Category: {category}",
            f"Insight: {insight}",
        ]
        if category == "unknown":
            line.append("[WARNING] Question not classified correctly")

        output = "\n".join(line)
        print(output)
        print("-" * 60)
        results.append(output)

    summary = f"Successfully classified {success_count} out of {len(QUESTIONS)} questions."
    print(summary)
    results.append(summary)

    output_path = Path(__file__).resolve().parent / "test_results.txt"
    output_path.write_text("\n\n".join(results), encoding="utf-8")
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    run_all_tests()
