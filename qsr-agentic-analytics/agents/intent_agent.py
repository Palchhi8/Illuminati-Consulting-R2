import json
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.llm_client import get_llm_response


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SYSTEM_PROMPT = """
You are a strict classifier for QSR business analytics questions.
Classify the user's question into exactly one of these categories:
1. summary_last_3_months
2. top_bottom_stores
3. channel_performance
4. top_skus
5. declining_cities
6. weekend_vs_weekday
7. festive_vs_normal
8. declining_stores_reasons

Respond with ONLY a JSON object and nothing else, in this exact form:
{"category": "<one of the 8 above>", "params": {}}

If the question does not clearly match any category, use:
{"category": "unknown", "params": {}}
"""


def classify_question(question: str) -> Dict[str, Any]:
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
                return {
                    "category": parsed.get("category", "unknown"),
                    "params": parsed.get("params", {}),
                }
        except Exception:
            pass
    except Exception:
        pass

    return {"category": "unknown", "params": {}}


if __name__ == "__main__":
    sample_question = "What are the top and bottom stores by revenue?"
    print(classify_question(sample_question))
