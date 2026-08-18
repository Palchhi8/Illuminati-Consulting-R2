import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.llm_client import get_llm_response


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger(__name__)

SUPPORTED_CATEGORIES = [
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

SYSTEM_PROMPT = """
You are a strict classifier for QSR business analytics questions.
Classify the user's question into exactly one of these categories:
1. overall_summary (e.g., total orders, total revenue, overall AOV, dataset row count, how many orders)
2. summary_last_3_months (e.g., last 3 months revenue, orders, AOV)
3. category_performance (e.g., highest revenue category, Burgers vs Pizza vs Wraps vs Sides vs Beverages vs Desserts)
4. top_bottom_stores (e.g., top 5 or bottom 5 stores by revenue)
5. channel_performance (e.g., Zomato, Swiggy, Dine-in, Takeaway performance, comparison)
6. top_skus (e.g., top 5 SKUs / products by quantity or revenue)
7. declining_cities (e.g., cities with declining revenue over last 3 months)
8. weekend_vs_weekday (e.g., weekend performance vs weekdays)
9. festive_vs_normal (e.g., festive period vs normal days, Diwali, Pujo, New Year)
10. declining_stores_reasons (e.g., stores declining and reasons / drivers)
11. general_insights (e.g., general takeaways, key insights, highlights of data)

Respond with ONLY a JSON object and nothing else, in this exact form:
{"category": "<one of the categories above>", "params": {}}

If the question does not clearly match any category, use:
{"category": "unknown", "params": {}}
"""


def fallback_classify_question(question: str) -> Dict[str, Any]:
    q = question.lower().strip()

    # Declining stores with reasons
    if ("store" in q or "stores" in q) and ("declin" in q or "drop" in q or "reason" in q or "why" in q):
        return {"category": "declining_stores_reasons", "params": {"n_months": 3}}

    # Declining cities
    if ("cit" in q or "cities" in q or "city" in q) and ("declin" in q or "drop" in q or "loss" in q):
        return {"category": "declining_cities", "params": {"n_months": 3}}

    # Weekend vs weekday
    if "weekend" in q or "weekday" in q or "saturday" in q or "sunday" in q:
        return {"category": "weekend_vs_weekday", "params": {}}

    # Festive vs normal
    if "festive" in q or "festival" in q or "diwali" in q or "pujo" in q or "holiday" in q:
        return {"category": "festive_vs_normal", "params": {}}

    # Channels (Zomato, Swiggy, Dine-in, Takeaway, Channel)
    if "channel" in q or "zomato" in q or "swiggy" in q or "takeaway" in q or "dine-in" in q or "dine in" in q:
        return {"category": "channel_performance", "params": {}}

    # SKUs / Products
    if "sku" in q or "skus" in q or "item" in q or "items" in q or "product" in q or "products" in q or "quantity sold" in q:
        return {"category": "top_skus", "params": {"n": 5}}

    # Top & Bottom Stores
    if ("top" in q or "bottom" in q or "best" in q or "worst" in q or "highest" in q or "lowest" in q) and ("store" in q or "stores" in q or "outlet" in q):
        return {"category": "top_bottom_stores", "params": {"n": 5}}

    # Categories (Burgers, Pizza, Wraps, Category, Categories)
    if "category" in q or "categories" in q or "burger" in q or "pizza" in q or "wrap" in q or "beverage" in q or "dessert" in q:
        return {"category": "category_performance", "params": {}}

    # 3 Months / Quarter summary
    if "3 month" in q or "three month" in q or "last quarter" in q:
        return {"category": "summary_last_3_months", "params": {"n": 3}}

    # General / Overall Summary (Order count, total revenue, rows in orders table)
    if ("how many" in q or "total" in q or "count" in q or "row" in q or "number of" in q or "all" in q) and ("order" in q or "orders" in q or "revenue" in q or "sales" in q or "table" in q):
        return {"category": "overall_summary", "params": {}}

    # General insights
    if "insight" in q or "insights" in q or "takeaway" in q or "takeaways" in q or "summary" in q or "overview" in q or "highlights" in q:
        return {"category": "general_insights", "params": {}}

    return {"category": "unknown", "params": {}}


def classify_question(question: str) -> Dict[str, Any]:
    # 1. Try LLM Classification
    try:
        raw_text = get_llm_response(SYSTEM_PROMPT, question)
        raw_text = raw_text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[len("```json"):]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                category = parsed.get("category", "unknown")
                if category in SUPPORTED_CATEGORIES:
                    return {
                        "category": category,
                        "params": parsed.get("params", {}),
                    }
        except Exception as json_err:
            logger.warning(f"Could not parse LLM JSON response: {raw_text} ({json_err})")
    except Exception as llm_err:
        logger.warning(f"Intent LLM classification encountered error: {llm_err}. Using deterministic fallback.")

    # 2. Deterministic Fallback Classification
    return fallback_classify_question(question)


if __name__ == "__main__":
    test_questions = [
        "How many orders are there?",
        "What is the total revenue?",
        "Which category has the highest revenue?",
        "Compare revenue between Zomato and Swiggy.",
        "What were the total revenue, orders, and average order value for the last 3 months?",
        "Which are the top 5 and bottom 5 stores by revenue?",
        "Which are the top 5 SKUs by quantity sold and revenue?",
        "Which cities have shown a decline in revenue over the last 3 months?",
        "How does weekend performance compare with weekdays?",
        "How does festive-period performance compare with normal periods?",
        "Which stores have consistently declined in the last 3 months, and what are the key reasons?",
        "What are the most important insights from the QSR data?",
    ]
    for tq in test_questions:
        print(f"'{tq}' -> {classify_question(tq)}")
