import json
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.llm_client import get_llm_response


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def generate_insight(question: str, category: str, data: Dict[str, Any]) -> str:
    system_prompt = (
        "You are a senior business analytics assistant for a QSR company. "
        "Write a polished, executive-style answer in 3-6 sentences. "
        "Use clear business language, reference the most important numbers from the provided data, and explain what those numbers mean for the business. "
        "Write for a non-technical stakeholder and avoid jargon. "
        "Do not use markdown headers, bullet points, or lists. "
        "Keep the response concise, readable, and action-oriented. "
        "Start with the main takeaway, then support it with specific data, and finish with a practical implication or recommendation."
    )

    if category == "declining_stores_reasons":
        system_prompt += (
            " For this category, go beyond reporting the figures and explain likely reasons for the decline by analyzing the discount trend, order count trend, and channel mix data provided in the data."
        )

    user_message = f"Question: {question}\n\nData: {json.dumps(data, default=str)}"
    return get_llm_response(system_prompt, user_message)


if __name__ == "__main__":
    sample_question = "Why are some stores declining?"
    sample_category = "declining_stores_reasons"
    sample_data = {
        "store_id": "ST001",
        "store_name": "QuickBite Pune 01",
        "city": "Pune",
        "monthly_revenue_values": [22669.5, 24034.5, 24144.75, 28665.0, 19640.25, 24444.0],
        "decline_pct": 11.66,
        "avg_discount_amount_trend": [0.0, 6.25, 3.66, 1.53, 6.25, 0.0],
        "order_count_trend": [37, 36, 41, 49, 28, 37],
        "channel_mix_trend": {"online_orders": 0, "offline_orders": 0},
    }
    print(generate_insight(sample_question, sample_category, sample_data))
