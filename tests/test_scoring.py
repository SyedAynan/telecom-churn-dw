"""Scoring smoke: predictions exist, in range, banded, joined to 360."""
from __future__ import annotations

import duckdb

from etl.paths import DB_PATH


def test_churn_predictions_written_back():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        n, n_distinct, n_bad = con.sql("""
            SELECT COUNT(*),
                   COUNT(DISTINCT customer_id),
                   SUM(CASE WHEN churn_probability < 0
                             OR churn_probability > 1 THEN 1 ELSE 0 END)
            FROM marts.churn_predictions
        """).fetchone()
        bands = [r[0] for r in con.sql(
            "SELECT DISTINCT risk_band FROM marts.churn_predictions"
        ).fetchall()]
        joined = con.sql("""
            SELECT COUNT(*) FROM marts.churn_predictions p
            JOIN marts.mart_customer_360 m USING (customer_id)
        """).fetchone()[0]
    finally:
        con.close()

    assert n == 7043, f"expected all customers scored, got {n}"
    assert n_distinct == n, "duplicate customer_id in predictions"
    assert n_bad == 0, "probability out of [0, 1]"
    assert set(bands) == {"high", "medium", "low"}, f"unexpected bands {bands}"
    assert joined == n, "predictions do not join 1:1 to mart_customer_360"


def test_model_bundle_loadable():
    import joblib

    from etl.paths import MODELS_DIR

    path = MODELS_DIR / "churn_logreg.joblib"
    assert path.exists(), "run make train before pytest"
    bundle = joblib.load(path)
    assert bundle["auc"] > 0.75, f"model AUC degraded: {bundle['auc']}"
