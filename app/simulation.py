"""Pipeline walkthrough: how one real customer flows CSV → dashboard.

Each stage is a real artifact — the CSV row, the staged record, the star-schema
join, the 360 mart row, the model feature vector, and the prediction served.
The page recomposes them so a viewer can trace one actual churned customer
down the whole line, end to end.
"""
from __future__ import annotations

import pandas as pd

from etl.paths import RAW_CSV_PATH
from ml.features import FEATURE_COLUMNS

FEATURE_ORDER = FEATURE_COLUMNS

# The pipeline funnel. counts come from real artifacts (CSV rows, staged rows,
# mart rows) — values verified against the built warehouse.
_STAGES = [
    ("source", "CSV source", "raw file · Kaggle/IBM telco",
     "Telco-Customer-Churn.csv", 7043),
    ("extract", "ETL · extract", "download + md5 verify",
     "data/raw/…csv", 7043),
    ("staging", "dbt · staging", "type, snake_case, impute",
     "staging.stg_telco_churn", 7043),
    ("core", "dbt · star schema", "facts + dims + bridge",
     "core.fact_customer", 7043),
    ("mart", "dbt · mart", "wide analytics table",
     "marts.mart_customer_360", 7043),
    ("model", "ML · score", "logreg on 12 features",
     "marts.churn_predictions", 7043),
    ("serve", "dashboard", "this page reads the mart",
     "Streamlit", 7043),
]

_STAGES_B = [s for s in _STAGES]  # alias kept simple


def stage_rows() -> list[dict]:
    """Ordered stage cards: id, title, what happens, artifact, row count."""
    return [
        {
            "id": sid,
            "title": title,
            "blurb": blurb,
            "artifact": artifact,
            "rows": rows,
        }
        for (sid, title, blurb, artifact, rows) in _STAGES
    ]


def pack_features(row: dict) -> pd.DataFrame:
    """One-row feature vector, column order = model's FEATURE_ORDER.

    Accepts a mart_customer_360-style row (with payment_automation) and maps it
    the same way ml/features.build_matrix does so scoring is consistent.
    """
    data = {name: 0.0 for name in FEATURE_ORDER}
    for k, v in row.items():
        if k in data:
            try:
                data[k] = float(v)
            except (TypeError, ValueError):
                pass
    # is_automatic_payment derives from payment_automation label, like build_matrix
    if "payment_automation" in row:
        data["is_automatic_payment"] = 1.0 if row["payment_automation"] == "Automatic" else 0.0
    return pd.DataFrame([data], columns=FEATURE_ORDER)


def read_raw_row(customer_id: str) -> dict | None:
    """Pull one row straight from the raw CSV (the true source artifact)."""
    if not RAW_CSV_PATH.exists():
        return None
    df = pd.read_csv(RAW_CSV_PATH, dtype=str)
    hit = df[df["customerID"] == customer_id]
    if hit.empty:
        return None
    return hit.iloc[0].to_dict()
