"""Shared feature engineering for train and score.

Both scripts must build the feature matrix identically, so the logic lives
here once. Reads mart_customer_360 from DuckDB; returns X (numeric frame),
y (churn flag, may be all-NaN at score time) and the customer ids.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from etl.paths import DB_PATH

FEATURE_COLUMNS = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "is_female",
    "is_senior",
    "has_partner",
    "has_dependents",
    "paperless_billing",
    "contract_months",
    "is_automatic_payment",
    "n_internet",
    "n_addons",
]

CATEGORICAL = ["payment_method_label", "contract_label"]


def load_360(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql("SELECT * FROM marts.mart_customer_360").df()


def build_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """One row per customer, numeric features only (id + churn excluded)."""
    out = pd.DataFrame(index=df.index)
    out["tenure_months"] = df["tenure_months"].astype(float)
    out["monthly_charges"] = df["monthly_charges"].astype(float)
    out["total_charges"] = df["total_charges"].astype(float)
    out["is_female"] = df["is_female"].astype(float)
    out["is_senior"] = df["is_senior"].astype(float)
    out["has_partner"] = df["has_partner"].astype(float)
    out["has_dependents"] = df["has_dependents"].astype(float)
    out["paperless_billing"] = df["paperless_billing"].astype(float)
    out["contract_months"] = df["contract_months"].astype(float)
    out["is_automatic_payment"] = (df["payment_automation"] == "Automatic").astype(float)
    out["n_internet"] = df["n_internet"].astype(float)       # 0 = none, 1 = dsl/fiber
    out["n_addons"] = df["n_addons"].astype(float)           # 0-6 subscribed add-ons
    return out


def churn_flag(df: pd.DataFrame) -> pd.Series:
    return df["churned"].astype(bool)
