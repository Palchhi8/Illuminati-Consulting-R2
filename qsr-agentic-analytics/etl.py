import os
import sqlite3
from pathlib import Path

import pandas as pd


SHEET_COLUMNS = {
    "Store_Master": [
        "STORE_ID",
        "STORE_NAME",
        "CITY",
        "STATE",
        "REGION",
        "STORE_FORMAT",
        "OPENING_DATE",
        "CITY_PRICE_INDEX",
        "PERFORMANCE_FACTOR",
        "STATUS",
    ],
    "Product_Master": [
        "SKU_ID",
        "SKU_NAME",
        "CATEGORY",
        "VEG_NONVEG",
        "BASE_PRICE_INR",
        "EST_COGS_PCT",
        "STATUS",
    ],
    "Customer_Master": [
        "CUSTOMER_ID",
        "HOME_CITY",
        "CUSTOMER_SEGMENT",
        "JOIN_DATE",
    ],
    "Promotions": [
        "PROMO_ID",
        "PROMO_NAME",
        "PROMO_TYPE",
        "START_DATE",
        "END_DATE",
        "APPLICABLE_DAYS",
        "APPLICABILITY",
        "DISCOUNT_PCT",
        "MIN_BILL_VALUE",
        "MAX_DISCOUNT_INR",
    ],
    "Calendar": [
        "DATE",
        "YEAR",
        "MONTH",
        "MONTH_NO",
        "DAY_NAME",
        "DAY_TYPE",
        "FESTIVE_PERIOD",
    ],
    "Orders": [
        "ORDER_ID",
        "ORDER_DATETIME",
        "STORE_ID",
        "CUSTOMER_ID",
        "CHANNEL",
        "TOTAL_QTY",
        "GROSS_BILL_VALUE",
        "DISCOUNT_AMOUNT",
        "PROMO_ID",
        "NET_BEFORE_TAX",
        "TAX_AMOUNT",
        "NET_REVENUE",
    ],
    "Order_Details": [
        "ORDER_DETAIL_ID",
        "ORDER_ID",
        "SKU_ID",
        "QUANTITY",
        "UNIT_PRICE",
        "LINE_GROSS_VALUE",
        "LINE_DISCOUNT",
        "LINE_NET_VALUE",
        "EST_COGS",
    ],
}

DATE_COLUMNS = {
    "Store_Master": ["OPENING_DATE"],
    "Product_Master": [],
    "Customer_Master": ["JOIN_DATE"],
    "Promotions": ["START_DATE", "END_DATE"],
    "Calendar": ["DATE"],
    "Orders": ["ORDER_DATETIME"],
    "Order_Details": [],
}


def resolve_excel_path() -> Path:
    candidate_paths = []
    env_path = os.getenv("QSR_EXCEL_PATH")
    if env_path:
        candidate_paths.append(Path(env_path).expanduser())

    candidate_paths.extend(
        [
            Path(__file__).resolve().parent / "QSR_Agentic_Insights_Dataset.xlsx",
            Path.cwd() / "QSR_Agentic_Insights_Dataset.xlsx",
        ]
    )

    for path in candidate_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find QSR_Agentic_Insights_Dataset.xlsx. Set QSR_EXCEL_PATH or place the file in the project folder."
    )


def parse_date_columns(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    for column in DATE_COLUMNS.get(sheet_name, []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def load_excel_to_sqlite(excel_path: Path, db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        for sheet_name, columns in SHEET_COLUMNS.items():
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            missing_columns = [col for col in columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Sheet '{sheet_name}' is missing columns: {missing_columns}")

            df = df[columns].copy()
            df = parse_date_columns(df, sheet_name)
            df.to_sql(name=sheet_name, con=conn, if_exists="replace", index=False)

            row_count = conn.execute(f'SELECT COUNT(*) FROM "{sheet_name}"').fetchone()[0]
            print(f"{sheet_name}: {row_count} rows")

    print(f"SQLite database created at: {db_path}")


def main() -> None:
    excel_path = resolve_excel_path()
    db_path = Path(os.getenv("QSR_DB_PATH", Path(__file__).resolve().parent / "qsr.db"))
    load_excel_to_sqlite(excel_path, db_path)


if __name__ == "__main__":
    main()
