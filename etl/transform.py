"""Transform: clean the raw CSV into a typed, analysis-ready frame.

Fixes the known quirks of the Telco churn dataset:
- TotalCharges arrives as a string, with ' ' (blank) for 11 customers with
  tenure 0 — coerced to float, blanks become NaN then 0.0 (no tenure yet,
  so no charges yet: a defensible business rule, documented here).
- Yes/No columns are standardized to lowercase 'yes'/'no'.
- 'No phone service' / 'No internet service' values are kept verbatim in the
  service columns at the ETL layer; the dbt staging layer later collapses
  them to 'no' plus a phone_service flag (that's modeling, not cleaning).

Output: data/processed/telco_clean.parquet (overwrite = idempotent).
"""
from __future__ import annotations

import pandas as pd

from etl.paths import CLEAN_PARQUET_PATH, RAW_CSV_PATH, ensure_dirs

BOOL_LIKE_COLUMNS = [
    "Partner", "Dependents", "PhoneService", "PaperlessBilling", "Churn",
]

# Columns where the dataset uses three-state values; kept as-is here.
SERVICE_COLUMNS = [
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
]


def transform() -> pd.DataFrame:
    ensure_dirs()
    if not RAW_CSV_PATH.exists():
        raise SystemExit(
            f"[transform] {RAW_CSV_PATH} not found — run `make extract` first."
        )

    df = pd.read_csv(RAW_CSV_PATH, dtype={"TotalCharges": "string"})
    n_raw = len(df)

    # --- TotalCharges: string with blanks -> float -----------------------
    blanks = (df["TotalCharges"].str.strip() == "").sum()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    # --- standardize yes/no columns to lowercase --------------------------
    for col in BOOL_LIKE_COLUMNS:
        df[col] = df[col].str.strip().str.lower()

    # --- coerce types ------------------------------------------------------
    df["SeniorCitizen"] = df["SeniorCitizen"].astype("int8")
    df["tenure"] = df["tenure"].astype("int16")
    df["MonthlyCharges"] = df["MonthlyCharges"].astype("float64")
    df["TotalCharges"] = df["TotalCharges"].astype("float64")
    df["customerID"] = df["customerID"].astype("string")

    # --- sanity checks before writing -------------------------------------
    assert df["customerID"].is_unique, "customerID must be unique"
    assert df["tenure"].between(0, 72).all(), "tenure must be 0-72 months"
    assert df["MonthlyCharges"].ge(0).all()
    assert df["TotalCharges"].ge(0).all()

    CLEAN_PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_PARQUET_PATH, index=False)
    print(
        f"[transform] {n_raw} rows -> {CLEAN_PARQUET_PATH.name} "
        f"(TotalCharges blanks fixed: {blanks})"
    )
    return df


if __name__ == "__main__":
    transform()
