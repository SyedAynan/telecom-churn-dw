"""Load: land the cleaned data into DuckDB's raw schema, idempotently.

Grain: one row per customer (source grain, unchanged).

The raw schema is the unopinionated landing layer — typing and business
logic happen in dbt. `CREATE OR REPLACE TABLE` makes the whole ETL
idempotent: running it twice leaves exactly one copy of each row.
"""
from __future__ import annotations

import duckdb

from etl.paths import CLEAN_PARQUET_PATH, DB_PATH, ensure_dirs


def connect() -> duckdb.DuckDBPyConnection:
    ensure_dirs()
    return duckdb.connect(str(DB_PATH))


def load() -> int:
    if not CLEAN_PARQUET_PATH.exists():
        raise SystemExit(
            f"[load] {CLEAN_PARQUET_PATH} not found — run `make transform` first."
        )

    con = connect()
    try:
        con.sql("CREATE SCHEMA IF NOT EXISTS raw")
        con.sql(
            f"""
            CREATE OR REPLACE TABLE raw.telco_churn AS
            SELECT * FROM '{CLEAN_PARQUET_PATH}'
            """
        )
        n = con.sql("SELECT COUNT(*) FROM raw.telco_churn").fetchone()[0]
        print(f"[load] raw.telco_churn: {n} rows in {DB_PATH}")
        return n
    finally:
        con.close()


if __name__ == "__main__":
    load()
