"""ETL idempotency: running load twice must not duplicate rows."""
from __future__ import annotations

import duckdb

from etl.paths import DB_PATH


def test_load_twice_same_row_count():
    """Run the full ETL twice; raw table must hold exactly one copy."""
    from etl import load, transform  # noqa: F401 — ensures modules importable

    n1 = load.load()
    n2 = load.load()
    assert n1 == n2 == 7043, f"load not idempotent: {n1} then {n2}"

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows, distinct = con.sql(
            "SELECT COUNT(*), COUNT(DISTINCT customerID) FROM raw.telco_churn"
        ).fetchone()
    finally:
        con.close()
    assert rows == distinct == 7043, "duplicate rows after double load"


def test_transform_types_total_charges():
    """ETL contract: TotalCharges is typed float; the 11 source blanks stay
    NULL here (the warehouse's staging layer owns the imputation rule)."""
    from etl import transform

    df = transform.transform()
    assert df["TotalCharges"].dtype == "float64"
    n_null = int(df["TotalCharges"].isna().sum())
    assert n_null == 11, f"expected 11 NULL TotalCharges, got {n_null}"
    assert (df.loc[df["TotalCharges"].isna(), "tenure"] == 0).all()
