"""Score ALL customers and write predictions back into the warehouse.

The 'predictions live in the warehouse' pattern: ml/score.py writes
marts.churn_predictions (customer_id, churn_probability, risk_band,
top_reason) so SQL/BI users can join risk to customer 360 without
leaving DuckDB. Idempotent — CREATE OR REPLACE TABLE.

top_reason: the single feature pushing this customer's risk furthest from
the population mean (z-like gap * model coefficient). Positive gap on a
churn-positive feature = the thing making THIS customer risky.
"""
from __future__ import annotations

import duckdb
import joblib
import numpy as np
import pandas as pd

from etl.paths import DB_PATH, MODELS_DIR, ensure_dirs
from ml.features import FEATURE_COLUMNS, build_matrix, load_360

REASON_LABELS = {
    "tenure_months":          "New customer (low tenure)",
    "contract_months":        "Month-to-month contract",
    "monthly_charges":        "High monthly charges",
    "total_charges":          "Low lifetime value so far",
    "paperless_billing":      "Paperless billing",
    "payment_method":         "Payment method (electronic check)",
    "is_senior":              "Senior citizen",
    "is_female":              "Female",
    "has_partner":            "No partner",
    "has_dependents":          "No dependents",
    "is_automatic_payment":   "Manual payment (no autopay)",
    "n_internet":             "Internet service",
    "n_addons":               "Few add-on services",
}


def risk_band(p: float) -> str:
    if p >= 0.75:
        return "high"
    if p >= 0.45:
        return "medium"
    return "low"


def score() -> int:
    ensure_dirs()
    model_path = MODELS_DIR / "churn_logreg.joblib"
    if not model_path.exists():
        raise SystemExit(f"[score] {model_path} not found — run `make train` first.")
    bundle = joblib.load(model_path)
    pipe = bundle["pipeline"]

    con = duckdb.connect(str(DB_PATH))
    try:
        df = load_360(con)
        X = build_matrix(df)

        proba = pipe.predict_proba(X)[:, 1]

        # per-customer top reason: scaled feature gap * model coefficient
        scaler = pipe.named_steps["scaler"]
        clf = pipe.named_steps["clf"]
        z = scaler.transform(X)
        push = z * clf.coef_[0]          # contribution per feature (n, k)
        top_idx = np.asarray(push).argmax(axis=1)
        reasons = [REASON_LABELS[FEATURE_COLUMNS[i]] for i in top_idx]

        preds = pd.DataFrame({
            "customer_id": df["customer_id"],
            "churn_probability": np.round(proba, 4),
            "risk_band": [risk_band(p) for p in proba],
            "top_reason": reasons,
        })

        con.sql("CREATE SCHEMA IF NOT EXISTS marts")
        con.register("preds_df", preds)
        con.sql("CREATE OR REPLACE TABLE marts.churn_predictions AS SELECT * FROM preds_df")
        con.unregister("preds_df")

        n = con.sql("SELECT COUNT(*) FROM marts.churn_predictions").fetchone()[0]
        bands = con.sql(
            "SELECT risk_band, COUNT(*) n FROM marts.churn_predictions GROUP BY 1 ORDER BY 1"
        ).fetchall()
        print(f"[score] marts.churn_predictions: {n} rows written back to warehouse")
        for band, cnt in bands:
            print(f"    {band:8s} {cnt:>6,}  ({cnt / n:.1%})")
        return n
    finally:
        con.close()


if __name__ == "__main__":
    score()
