import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv

from etl import load_excel_to_sqlite, resolve_excel_path


load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_db_path() -> Path:
    env_path = os.getenv("QSR_DB_PATH")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists() or (not str(env_path).startswith("C:") and not str(env_path).startswith("c:")):
            return p
    return Path(__file__).resolve().parent / "qsr.db"


def make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except Exception:
            return value
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return int(value)
    return value


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def df_to_serializable(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
    }


def run_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_summary_last_n_months(n: int = 3) -> Dict[str, Any]:
    query = """
        SELECT
            SUM(o.NET_REVENUE) AS total_revenue,
            COUNT(o.ORDER_ID) AS total_orders,
            AVG(o.NET_REVENUE) AS average_order_value
        FROM Orders o
        WHERE strftime('%Y-%m', o.ORDER_DATETIME) IN (
            SELECT DISTINCT strftime('%Y-%m', ORDER_DATETIME)
            FROM Orders
            ORDER BY 1 DESC
            LIMIT ?
        )
    """
    rows = run_query(query, (n,))
    return make_json_safe(rows[0] if rows else {})


def get_overall_summary() -> Dict[str, Any]:
    query = """
        SELECT
            SUM(o.NET_REVENUE) AS total_revenue,
            COUNT(o.ORDER_ID) AS total_orders,
            AVG(o.NET_REVENUE) AS average_order_value,
            MIN(date(o.ORDER_DATETIME)) AS start_date,
            MAX(date(o.ORDER_DATETIME)) AS end_date
        FROM Orders o
    """
    rows = run_query(query)
    return make_json_safe(rows[0] if rows else {})


def get_category_performance() -> Dict[str, Any]:
    query = """
        SELECT
            COALESCE(pm.CATEGORY, 'Unknown') AS category,
            SUM(od.QUANTITY) AS total_quantity,
            SUM(od.LINE_NET_VALUE) AS total_revenue,
            COUNT(DISTINCT od.ORDER_ID) AS order_count
        FROM Order_Details od
        LEFT JOIN Product_Master pm ON pm.SKU_ID = od.SKU_ID
        GROUP BY pm.CATEGORY
        ORDER BY total_revenue DESC
    """
    return make_json_safe({"rows": run_query(query)})


def get_top_bottom_stores(n: int = 5) -> Dict[str, Any]:
    query = """
        SELECT
            o.STORE_ID,
            sm.STORE_NAME,
            sm.CITY,
            SUM(o.NET_REVENUE) AS total_revenue
        FROM Orders o
        LEFT JOIN Store_Master sm ON sm.STORE_ID = o.STORE_ID
        GROUP BY o.STORE_ID, sm.STORE_NAME, sm.CITY
        ORDER BY total_revenue DESC
    """
    rows = run_query(query)
    ranked = sorted(rows, key=lambda r: r["total_revenue"], reverse=True)
    top = ranked[:n]
    bottom = ranked[-n:][::-1]
    return make_json_safe({
        "top": top,
        "bottom": bottom,
    })


def get_channel_performance() -> Dict[str, Any]:
    query = """
        SELECT
            CHANNEL,
            SUM(NET_REVENUE) AS total_revenue,
            AVG(NET_REVENUE) AS average_order_value,
            COUNT(ORDER_ID) AS order_count
        FROM Orders
        GROUP BY CHANNEL
        ORDER BY total_revenue DESC
    """
    return make_json_safe({"rows": run_query(query)})


def get_top_skus(n: int = 5) -> Dict[str, Any]:
    query = """
        SELECT
            od.SKU_ID,
            pm.SKU_NAME,
            SUM(od.QUANTITY) AS total_quantity,
            SUM(od.LINE_NET_VALUE) AS total_revenue
        FROM Order_Details od
        LEFT JOIN Product_Master pm ON pm.SKU_ID = od.SKU_ID
        GROUP BY od.SKU_ID, pm.SKU_NAME
        ORDER BY total_quantity DESC, total_revenue DESC
    """
    rows = run_query(query)
    top_qty = rows[:n]
    top_rev = sorted(rows, key=lambda r: r["total_revenue"], reverse=True)[:n]
    return make_json_safe({
        "by_quantity": top_qty,
        "by_revenue": top_rev,
    })


def get_declining_cities(n_months: int = 3) -> Dict[str, Any]:
    query = """
        WITH monthly_revenue AS (
            SELECT
                sm.CITY AS city,
                strftime('%Y-%m', o.ORDER_DATETIME) AS month_key,
                SUM(o.NET_REVENUE) AS revenue
            FROM Orders o
            LEFT JOIN Store_Master sm ON sm.STORE_ID = o.STORE_ID
            GROUP BY sm.CITY, strftime('%Y-%m', o.ORDER_DATETIME)
        )
        SELECT city, month_key, revenue
        FROM monthly_revenue
        ORDER BY city, month_key
    """
    rows = run_query(query)
    df = pd.DataFrame(rows)
    if df.empty:
        return {"cities": []}
    df["month_key"] = pd.to_datetime(df["month_key"])
    result = []
    for city, city_df in df.groupby("city", sort=False):
        city_df = city_df.sort_values("month_key")
        if len(city_df) < max(2, n_months):
            continue
        recent = city_df.tail(n_months)
        prev = city_df.iloc[-(n_months + 1) : -1]
        if prev.empty:
            continue
        prev_rev = prev["revenue"].mean()
        recent_rev = recent["revenue"].mean()
        if recent_rev < prev_rev:
            result.append({
                "city": city,
                "previous_avg_revenue": round(float(prev_rev), 2),
                "recent_avg_revenue": round(float(recent_rev), 2),
                "decline_pct": round(((prev_rev - recent_rev) / prev_rev) * 100 if prev_rev else 0.0, 2),
            })
    return make_json_safe({"cities": result})


def get_weekend_vs_weekday() -> Dict[str, Any]:
    query = """
        SELECT
            c.DAY_TYPE,
            SUM(o.NET_REVENUE) AS total_revenue,
            COUNT(o.ORDER_ID) AS order_count,
            AVG(o.NET_REVENUE) AS average_order_value
        FROM Orders o
        LEFT JOIN Calendar c ON date(o.ORDER_DATETIME) = date(c.DATE)
        GROUP BY c.DAY_TYPE
        ORDER BY c.DAY_TYPE
    """
    return make_json_safe({"rows": run_query(query)})


def get_festive_vs_normal() -> Dict[str, Any]:
    query = """
        SELECT
            c.FESTIVE_PERIOD,
            SUM(o.NET_REVENUE) AS total_revenue,
            COUNT(o.ORDER_ID) AS order_count,
            AVG(o.NET_REVENUE) AS average_order_value
        FROM Orders o
        LEFT JOIN Calendar c ON date(o.ORDER_DATETIME) = date(c.DATE)
        GROUP BY c.FESTIVE_PERIOD
        ORDER BY c.FESTIVE_PERIOD
    """
    return make_json_safe({"rows": run_query(query)})


def get_declining_stores(n_months: int = 3) -> Dict[str, Any]:
    query = """
        WITH monthly_revenue AS (
            SELECT
                o.STORE_ID,
                sm.STORE_NAME,
                sm.CITY,
                strftime('%Y-%m', o.ORDER_DATETIME) AS month_key,
                SUM(o.NET_REVENUE) AS revenue,
                AVG(o.DISCOUNT_AMOUNT) AS avg_discount_amount,
                COUNT(DISTINCT o.ORDER_ID) AS order_count,
                COUNT(DISTINCT CASE WHEN o.CHANNEL IN ('Zomato', 'Swiggy', 'Online') THEN o.ORDER_ID END) AS online_orders,
                COUNT(DISTINCT CASE WHEN o.CHANNEL IN ('Dine-in', 'Takeaway', 'Offline') THEN o.ORDER_ID END) AS offline_orders
            FROM Orders o
            LEFT JOIN Store_Master sm ON sm.STORE_ID = o.STORE_ID
            GROUP BY o.STORE_ID, sm.STORE_NAME, sm.CITY, strftime('%Y-%m', o.ORDER_DATETIME)
        )
        SELECT *
        FROM monthly_revenue
        ORDER BY STORE_ID, month_key
    """
    rows = run_query(query)
    df = pd.DataFrame(rows)
    if df.empty:
        return {"stores": []}
    df["month_key"] = pd.to_datetime(df["month_key"])
    result = []
    for store_id, store_df in df.groupby("STORE_ID", sort=False):
        store_df = store_df.sort_values("month_key")
        if len(store_df) < n_months + 1:
            continue
        recent = store_df.tail(n_months)
        prior = store_df.iloc[-(n_months + 1) : -1]
        if prior.empty:
            continue
        prior_rev = prior["revenue"].mean()
        recent_rev = recent["revenue"].mean()
        if recent_rev < prior_rev:
            channel_mix = {
                "online_orders": int(recent["online_orders"].sum()),
                "offline_orders": int(recent["offline_orders"].sum()),
            }
            result.append({
                "STORE_ID": store_id,
                "STORE_NAME": store_df["STORE_NAME"].iloc[0],
                "CITY": store_df["CITY"].iloc[0],
                "monthly_revenue_values": [round(float(v), 2) for v in store_df["revenue"].tolist()],
                "decline_pct": round(((prior_rev - recent_rev) / prior_rev) * 100 if prior_rev else 0.0, 2),
                "avg_discount_amount_trend": [round(float(v), 2) for v in store_df["avg_discount_amount"].tolist()],
                "order_count_trend": [int(v) for v in store_df["order_count"].tolist()],
                "channel_mix_trend": channel_mix,
            })
    return make_json_safe({"stores": result})


def get_general_insights() -> Dict[str, Any]:
    summary = get_overall_summary()
    top_stores = get_top_bottom_stores(3)
    channels = get_channel_performance()
    categories = get_category_performance()
    top_skus = get_top_skus(3)
    return make_json_safe({
        "summary": summary,
        "top_stores": top_stores.get("top", []),
        "channels": channels.get("rows", []),
        "categories": categories.get("rows", []),
        "top_skus": top_skus.get("by_revenue", []),
    })


def ensure_database_ready() -> Path:
    db_path = get_db_path()
    if db_path.exists() and db_path.stat().st_size > 0:
        return db_path

    excel_path = resolve_excel_path()
    load_excel_to_sqlite(excel_path, db_path)
    return db_path


def main() -> None:
    print("overall_summary:")
    print(get_overall_summary())
    print("\ncategory_performance:")
    print(get_category_performance())
    print("\nsummary_last_n_months:")
    print(get_summary_last_n_months(3))
    print("\nTop/bottom stores:")
    print(get_top_bottom_stores(5))
    print("\nChannel performance:")
    print(get_channel_performance())
    print("\nTop SKUs:")
    print(get_top_skus(5))
    print("\nDeclining cities:")
    print(get_declining_cities(3))
    print("\nWeekend vs weekday:")
    print(get_weekend_vs_weekday())
    print("\nFestive vs normal:")
    print(get_festive_vs_normal())
    print("\nDeclining stores:")
    print(get_declining_stores(3))


if __name__ == "__main__":
    main()
