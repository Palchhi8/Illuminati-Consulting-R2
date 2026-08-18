import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.llm_client import get_llm_response


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logger = logging.getLogger(__name__)


def generate_fallback_insight(question: str, category: str, data: Dict[str, Any]) -> str:
    if not data:
        return "No analytics data was found for this inquiry. Please verify the query criteria or time period."

    if category == "overall_summary":
        total_rev = data.get("total_revenue", 0)
        total_ord = data.get("total_orders", 0)
        aov = data.get("average_order_value", 0)
        return (
            f"Across the full dataset, the business generated a total revenue of ₹{total_rev:,.2f} "
            f"from {total_ord:,} total orders, with an overall average order value (AOV) of ₹{aov:.2f}. "
            f"Transaction volumes demonstrate steady operational performance across the restaurant network. "
            f"To accelerate growth, we recommend implementing cross-selling combos and loyalty promotions to further increase ticket sizes."
        )

    if category == "summary_last_3_months":
        total_rev = data.get("total_revenue", 0)
        total_ord = data.get("total_orders", 0)
        aov = data.get("average_order_value", 0)
        return (
            f"Over the last 3 months, total revenue reached ₹{total_rev:,.2f} across {total_ord:,} orders, "
            f"yielding an average order value of ₹{aov:.2f}. "
            f"These numbers indicate robust consumer engagement and healthy sales momentum in recent months. "
            f"We recommend optimizing menu placement and promotional timing to sustain and expand this revenue trajectory."
        )

    if category == "category_performance":
        rows = data.get("rows", [])
        if rows:
            top_cat = rows[0]
            cat_summaries = [f"{r.get('category')}: ₹{r.get('total_revenue', 0):,.2f} ({r.get('total_quantity', 0):,} units)" for r in rows[:4]]
            return (
                f"Menu category performance is led by {top_cat.get('category')}, which generated ₹{top_cat.get('total_revenue', 0):,.2f} "
                f"across {top_cat.get('total_quantity', 0):,} units sold. "
                f"Key category contributions include {', '.join(cat_summaries)}. "
                f"We recommend featuring top-selling categories prominently in marketing and pairing them with high-margin beverages and desserts."
            )

    if category == "top_bottom_stores":
        top = data.get("top", [])
        bottom = data.get("bottom", [])
        top_str = ", ".join([f"{s.get('STORE_NAME')} (₹{s.get('total_revenue', 0):,.2f})" for s in top[:3]])
        bottom_str = ", ".join([f"{s.get('STORE_NAME')} (₹{s.get('total_revenue', 0):,.2f})" for s in bottom[:3]])
        return (
            f"Store performance shows significant variation across locations. "
            f"The top-performing stores are led by {top_str}, while underperforming locations include {bottom_str}. "
            f"To narrow this performance gap, we recommend replicating operational and promotional playbooks from top stores in lower-performing locations."
        )

    if category == "channel_performance":
        rows = data.get("rows", [])
        if rows:
            top_ch = rows[0]
            ch_list = [f"{r.get('CHANNEL')} (₹{r.get('total_revenue', 0):,.2f}, AOV: ₹{r.get('average_order_value', 0):.2f})" for r in rows]
            return (
                f"Sales across channels are led by {top_ch.get('CHANNEL')} with ₹{top_ch.get('total_revenue', 0):,.2f} in total revenue. "
                f"Channel breakdown: {'; '.join(ch_list)}. "
                f"Digital channels (Swiggy and Zomato) drive strong volume, while Dine-in and Takeaway provide direct margin capture. "
                f"We recommend continuing digital platform campaigns while boosting in-store dining experiences."
            )

    if category == "top_skus":
        by_qty = data.get("by_quantity", [])
        by_rev = data.get("by_revenue", [])
        top_qty_names = ", ".join([f"{item.get('SKU_NAME')} ({item.get('total_quantity', 0):,} units)" for item in by_qty[:3]])
        top_rev_names = ", ".join([f"{item.get('SKU_NAME')} (₹{item.get('total_revenue', 0):,.2f})" for item in by_rev[:3]])
        return (
            f"Product sales analysis indicates that the highest volume SKUs are {top_qty_names}. "
            f"In terms of revenue generation, the top contributors are {top_rev_names}. "
            f"These hero items represent the core of our business and should receive prioritized inventory support and bundle promotions."
        )

    if category == "declining_cities":
        cities = data.get("cities", [])
        if cities:
            city_str = ", ".join([f"{c.get('city')} (-{c.get('decline_pct')}%, recent avg: ₹{c.get('recent_avg_revenue', 0):,.2f})" for c in cities[:4]])
            return (
                f"Revenue analysis identifies recent revenue declines in key cities, most notably {city_str}. "
                f"These contractions suggest market saturation or emerging competitive pressures in those urban clusters. "
                f"We recommend launching localized promotional campaigns and assessing store-level customer feedback in affected cities."
            )
        return "Revenue across all monitored cities has remained stable or shown growth over the recent 3-month period."

    if category == "weekend_vs_weekday":
        rows = data.get("rows", [])
        if rows:
            parts = [f"{r.get('DAY_TYPE')}: ₹{r.get('total_revenue', 0):,.2f} across {r.get('order_count', 0):,} orders (AOV: ₹{r.get('average_order_value', 0):.2f})" for r in rows]
            return (
                f"Sales distribution by day type reveals: {'; '.join(parts)}. "
                f"Weekdays generate consistent recurring demand across working hours, while weekends present higher individual ticket opportunities. "
                f"We recommend tailoring weekday lunch combo deals and weekend family sharing bundles to optimize revenue."
            )

    if category == "festive_vs_normal":
        rows = data.get("rows", [])
        if rows:
            parts = [f"{r.get('FESTIVE_PERIOD')}: ₹{r.get('total_revenue', 0):,.2f} ({r.get('order_count', 0):,} orders)" for r in rows]
            return (
                f"Comparison between festive and normal operating periods shows: {'; '.join(parts)}. "
                f"Festive events like Diwali, Pujo, and New Year generate concentrated surges in customer spending and higher average order values. "
                f"We recommend preparing seasonal menus, advance staffing, and exclusive holiday combo packs well ahead of festive periods."
            )

    if category == "declining_stores_reasons":
        stores = data.get("stores", [])
        if stores:
            top_dec = stores[:3]
            details = [f"{s.get('STORE_NAME')} in {s.get('CITY')} (-{s.get('decline_pct')}%)" for s in top_dec]
            return (
                f"Stores showing notable revenue declines over recent months include {', '.join(details)}. "
                f"Detailed trend analysis indicates that order volume drops and fluctuating discount effectiveness were primary drivers of the decline. "
                f"We recommend conducting local operational reviews and tailoring discount structures to restore footfall."
            )
        return "No stores exhibited consistent revenue declines over the evaluated 3-month period."

    if category == "general_insights":
        summary = data.get("summary", {})
        top_stores = data.get("top_stores", [])
        top_skus = data.get("top_skus", [])
        tot_rev = summary.get("total_revenue", 0)
        tot_ord = summary.get("total_orders", 0)
        top_store_name = top_stores[0].get("STORE_NAME") if top_stores else "N/A"
        top_sku_name = top_skus[0].get("SKU_NAME") if top_skus else "N/A"
        return (
            f"Overall, the business maintains solid performance with ₹{tot_rev:,.2f} in total revenue from {tot_ord:,} orders. "
            f"Top revenue contributors include {top_store_name} among stores and {top_sku_name} among products. "
            f"Strategic priorities should focus on scaling delivery channels, revitalizing underperforming stores, and expanding high-margin menu items."
        )

    return f"Analysis for {category}: " + json.dumps(data, default=str)


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

    try:
        llm_insight = get_llm_response(system_prompt, user_message)
        if llm_insight and len(llm_insight.strip()) > 0:
            return llm_insight.strip()
    except Exception as exc:
        logger.warning(f"LLM insight generation failed ({exc}). Using deterministic fallback insight.")

    return generate_fallback_insight(question, category, data)


if __name__ == "__main__":
    sample_question = "Why are some stores declining?"
    sample_category = "declining_stores_reasons"
    sample_data = {
        "stores": [
            {
                "STORE_ID": "ST001",
                "STORE_NAME": "QuickBite Pune 01",
                "CITY": "Pune",
                "decline_pct": 11.66,
                "order_count_trend": [37, 36, 41, 49, 28, 37],
                "avg_discount_amount_trend": [0.0, 6.25, 3.66, 1.53, 6.25, 0.0],
                "channel_mix_trend": {"online_orders": 20, "offline_orders": 17},
            }
        ]
    }
    print(generate_insight(sample_question, sample_category, sample_data))
