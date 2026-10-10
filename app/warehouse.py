"""Read-only warehouse metadata, query templates, and quality checks."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from etl.paths import DB_PATH, PROJECT_ROOT

DBT_MANIFEST = PROJECT_ROOT / "dbt" / "target" / "manifest.json"
DBT_RESULTS = PROJECT_ROOT / "dbt" / "target" / "run_results.json"


def read_frame(sql: str, path: Path = DB_PATH) -> pd.DataFrame:
    """Read current data, closing the handle so external jobs can write."""
    with duckdb.connect(str(path), read_only=True) as con:
        return con.execute(sql).df()

# The registry remains useful when dbt artifacts have not been generated yet.
DEFAULT_TABLES: dict[str, dict[str, Any]] = {
    "telco_churn": {"layer": "Raw", "schema": "raw", "relation": "telco_churn", "grain": "one row per source customer", "materialization": "table"},
    "stg_telco_churn": {"layer": "Staging", "schema": "staging", "relation": "stg_telco_churn", "grain": "one row per typed customer", "materialization": "view"},
    "dim_date": {"layer": "Core", "schema": "core", "relation": "dim_date", "grain": "one row per month", "materialization": "table"},
    "dim_contract": {"layer": "Core", "schema": "core", "relation": "dim_contract", "grain": "one row per contract type", "materialization": "table"},
    "dim_payment_method": {"layer": "Core", "schema": "core", "relation": "dim_payment_method", "grain": "one row per payment method", "materialization": "table"},
    "dim_service": {"layer": "Core", "schema": "core", "relation": "dim_service", "grain": "one row per service", "materialization": "table"},
    "fact_customer": {"layer": "Core", "schema": "core", "relation": "fact_customer", "grain": "one row per customer", "materialization": "table"},
    "fact_customer_services": {"layer": "Core", "schema": "core", "relation": "fact_customer_services", "grain": "one row per customer-service pair", "materialization": "table"},
    "mart_customer_360": {"layer": "Marts", "schema": "marts", "relation": "mart_customer_360", "grain": "one row per customer", "materialization": "table"},
    "mart_churn_summary": {"layer": "Marts", "schema": "marts", "relation": "mart_churn_summary", "grain": "one row per segment", "materialization": "table"},
    "mart_revenue_analytics": {"layer": "Marts", "schema": "marts", "relation": "mart_revenue_analytics", "grain": "one row per risk/contract segment", "materialization": "table"},
    "churn_predictions": {"layer": "ML outputs", "schema": "marts", "relation": "churn_predictions", "grain": "one row per scored customer", "materialization": "table"},
}

QUERY_TEMPLATES = {
    "customer_sample": "SELECT * FROM marts.mart_customer_360 ORDER BY customer_id LIMIT {limit}",
    "highest_risk": """SELECT customer_id, churn_probability, risk_band, top_reason
FROM marts.churn_predictions ORDER BY churn_probability DESC LIMIT {limit}""",
    "segment_revenue": """SELECT * FROM marts.mart_revenue_analytics
ORDER BY addressable_revenue DESC LIMIT {limit}""",
    "warehouse_counts": """SELECT 'customer_360' AS mart, COUNT(*) AS rows FROM marts.mart_customer_360
UNION ALL SELECT 'predictions', COUNT(*) FROM marts.churn_predictions
UNION ALL SELECT 'churn_summary', COUNT(*) FROM marts.mart_churn_summary""",
}


def _fallback() -> dict[str, dict[str, Any]]:
    return {name: dict(meta, name=name, description="Project warehouse contract (dbt manifest unavailable).", sql="", depends_on=[]) for name, meta in DEFAULT_TABLES.items()}


def load_manifest_models(path: Path = DBT_MANIFEST) -> dict[str, dict[str, Any]]:
    """Return compact model metadata, falling back when artifacts are absent/bad."""
    models = _fallback()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return models
    for node in payload.get("nodes", {}).values():
        if node.get("resource_type") != "model":
            continue
        name = node.get("name")
        if not name:
            continue
        item = models.get(name, {"name": name, "layer": "dbt model", "schema": node.get("schema", ""), "relation": name, "grain": "see model description"})
        item.update({
            "name": name,
            "description": node.get("description") or item.get("description", ""),
            "materialization": node.get("config", {}).get("materialized", item.get("materialization", "table")),
            "sql": node.get("compiled_code") or node.get("raw_code") or item.get("sql", ""),
            "depends_on": [str(dep).split(".")[-1] for dep in node.get("depends_on", {}).get("nodes", [])],
            "columns": node.get("columns", {}),
        })
        models[name] = item
    return models


def query_template(name: str, limit: int = 25) -> str:
    """Return a bounded, fixed query; user input is never treated as SQL."""
    if name not in QUERY_TEMPLATES:
        raise KeyError(name)
    safe_limit = max(1, min(int(limit), 500))
    return QUERY_TEMPLATES[name].format(limit=safe_limit)


def quality_snapshot(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return read-only consistency counts used by the Warehouse page."""
    row = con.execute("""
        SELECT
          (SELECT COUNT(*) FROM marts.mart_customer_360) AS customers,
          (SELECT COUNT(*) FROM marts.churn_predictions) AS predictions,
          (SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM marts.churn_predictions) AS duplicate_prediction_ids,
          (SELECT COUNT(*) FROM marts.churn_predictions p JOIN marts.mart_customer_360 m USING (customer_id)) AS prediction_customer_join
    """).fetchone()
    return dict(zip(("customers", "predictions", "duplicate_prediction_ids", "prediction_customer_join"), row))


def safe_identifier(value: str) -> str:
    """Validate identifiers before using metadata-selected relations in SQL."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return value
