import sys
from pathlib import Path
from typing import Any, Dict, Optional

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent))

from agents.intent_agent import classify_question
from agents.insight_agent import generate_insight
from queries import (
    get_category_performance,
    get_channel_performance,
    get_declining_cities,
    get_declining_stores,
    get_festive_vs_normal,
    get_general_insights,
    get_overall_summary,
    get_summary_last_n_months,
    get_top_bottom_stores,
    get_top_skus,
    get_weekend_vs_weekday,
)


CATEGORY_TO_FUNCTION = {
    "overall_summary": get_overall_summary,
    "summary_last_3_months": get_summary_last_n_months,
    "category_performance": get_category_performance,
    "top_bottom_stores": get_top_bottom_stores,
    "channel_performance": get_channel_performance,
    "top_skus": get_top_skus,
    "declining_cities": get_declining_cities,
    "weekend_vs_weekday": get_weekend_vs_weekday,
    "festive_vs_normal": get_festive_vs_normal,
    "declining_stores_reasons": get_declining_stores,
    "general_insights": get_general_insights,
}


SUPPORTED_TYPES = [
    "overall_summary",
    "summary_last_3_months",
    "category_performance",
    "top_bottom_stores",
    "channel_performance",
    "top_skus",
    "declining_cities",
    "weekend_vs_weekday",
    "festive_vs_normal",
    "declining_stores_reasons",
    "general_insights",
]


def answer_question(question: str) -> Dict[str, Any]:
    classification = classify_question(question)
    category = classification.get("category", "unknown")
    params = classification.get("params", {}) or {}

    data: Optional[Dict[str, Any]] = None

    if category in CATEGORY_TO_FUNCTION:
        func = CATEGORY_TO_FUNCTION[category]
        try:
            data = func(**params)
        except TypeError:
            try:
                data = func()
            except Exception:
                data = None
        except Exception:
            data = None

    if data is not None:
        insight_text = generate_insight(question, category, data)
    else:
        insight_text = (
            "This question is not supported yet. Supported question types include: "
            + ", ".join(SUPPORTED_TYPES)
            + "."
        )

    return {
        "question": question,
        "category": category,
        "raw_data": data,
        "insight": insight_text,
    }


if __name__ == "__main__":
    sample_questions = [
        "What were the total revenue, orders, and average order value for the last 3 months?",
        "Which are the top 5 SKUs by quantity sold and revenue?",
        "Which stores have consistently declined in the last 3 months, and what are the key reasons?",
    ]

    for sample_question in sample_questions:
        result = answer_question(sample_question)
        print(f"Question: {sample_question}")
        print(f"Category: {result['category']}")
        print(f"Insight: {result['insight']}")
        print("-" * 80)
