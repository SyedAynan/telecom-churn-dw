"""Tests for the read-only warehouse interaction helpers."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from app.warehouse import (
    DEFAULT_TABLES,
    load_manifest_models,
    quality_snapshot,
    query_template,
)
from app import simulator


def test_warehouse_reads_refresh_after_an_external_writer(tmp_path):
    import subprocess
    import sys
    from app.warehouse import read_frame

    path = tmp_path / "refresh.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("CREATE TABLE sample AS SELECT 1 AS value")
    assert read_frame("SELECT * FROM sample", path).value.tolist() == [1]
    writer = subprocess.run(
        [sys.executable, "-c",
         "import duckdb,sys; con=duckdb.connect(sys.argv[1]); con.execute('UPDATE sample SET value=2'); con.close()",
         str(path)], capture_output=True, text=True, timeout=30,
    )
    assert writer.returncode == 0, writer.stderr
    assert read_frame("SELECT * FROM sample", path).value.tolist() == [2]


def test_empty_event_stream_can_be_filtered_before_first_batch():
    import pandas as pd

    sim = simulator.Simulator(pd.DataFrame(), seed=3)
    events = sim.recent()

    assert events[events.operator.isin(["Jio"])].empty
    assert list(events.columns) == ["ts", "customer_id", "operator", "event_type", "detail"]


def test_simulator_assigns_demo_operator_dimension():
    import pandas as pd

    customers = pd.DataFrame({
        "customer_id": ["a", "b"],
        "churn_probability": [.2, .8],
        "monthly_charges": [20, 40],
        "risk_band": ["low", "high"],
    })
    sim = simulator.Simulator(customers, seed=3)
    events = sim._tick()

    assert events
    assert {event.operator for event in events} <= {"Jio", "Airtel", "Vi", "BSNL"}
    assert all(event.operator for event in events)


def test_customer_deltas_aggregate_event_stream():
    import pandas as pd

    customers = pd.DataFrame({
        "customer_id": ["a", "b"],
        "churn_probability": [.2, .8],
        "monthly_charges": [20, 40],
        "risk_band": ["low", "high"],
    })
    sim = simulator.Simulator(customers, seed=3)
    sim._events.extend([
        simulator.Event(1.0, "a", "Jio", "payment", "auto-payment processed"),
        simulator.Event(2.0, "a", "Jio", "ticket", "billing dispute opened"),
        simulator.Event(3.0, "b", "Vi", "cancellation", "requested cancellation"),
    ])

    deltas = sim.customer_deltas().set_index("customer_id")

    assert deltas.loc["a", "neg_events"] == 1
    assert deltas.loc["a", "pos_events"] == 1
    assert deltas.loc["a", "cancellations"] == 0
    assert deltas.loc["b", "cancellations"] == 1


def test_live_negative_counts_can_filter_operator():
    import time
    import pandas as pd

    customers = pd.DataFrame({
        "customer_id": ["a"], "churn_probability": [.8],
        "monthly_charges": [40], "risk_band": ["high"],
    })
    sim = simulator.Simulator(customers, seed=3)
    sim._events.extend([
        simulator.Event(time.time(), "a", "Jio", "ticket", "billing dispute opened"),
        simulator.Event(time.time(), "a", "Vi", "failed_payment", "card declined"),
    ])

    counts = sim.live_negative_counts(operators=["Jio"])

    assert counts.to_dict("records") == [{"customer_id": "a", "neg_events": 1}]


@pytest.mark.parametrize("operators,expected", [(["Jio"], ["a"]), ([], []), (None, ["b"])])
def test_recent_filters_before_limiting_the_console(operators, expected):
    import pandas as pd

    sim = simulator.Simulator(pd.DataFrame(), seed=3)
    sim._events.extend([
        simulator.Event(1.0, "a", "Jio", "ticket", "billing dispute"),
        simulator.Event(2.0, "b", "Vi", "ticket", "billing dispute"),
    ])
    assert sim.recent(1, operators=operators).customer_id.tolist() == expected


def test_demo_stage_rows_descend_the_pipeline():
    from app.simulation import stage_rows

    stages = stage_rows()
    ids = [s["id"] for s in stages]
    assert ids == ["source", "extract", "staging", "core", "mart", "model", "serve"]
    # monotonic funnel: each stage keeps <= rows of the one before
    rows = [s["rows"] for s in stages]
    assert rows[0] == rows[-1] == 7043
    assert all(rows[i] <= rows[i + 1] for i in range(len(rows) - 1))


def test_model_features_pack_into_named_vector():
    import numpy as np

    from app.simulation import FEATURE_ORDER, pack_features

    row = {
        "tenure_months": 3, "monthly_charges": 90.0, "total_charges": 260.0,
        "is_female": 0, "is_senior": 0, "has_partner": 1, "has_dependents": 0,
        "paperless_billing": 1, "contract_months": 0, "is_automatic_payment": 0,
        "n_internet": 1, "n_addons": 1,
    }
    vec = pack_features(row)
    assert list(vec.columns) == FEATURE_ORDER
    assert vec.loc[0, "tenure_months"] == 3
    assert vec.shape == (1, len(FEATURE_ORDER))


def test_manifest_falls_back_to_known_warehouse_contract(tmp_path: Path):
    models = load_manifest_models(tmp_path / "missing-manifest.json")

    assert set(DEFAULT_TABLES).issubset(models)
    assert models["mart_customer_360"]["grain"] == "one row per customer"
    assert models["mart_customer_360"]["materialization"] == "table"


def test_manifest_extracts_model_provenance(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "nodes": {
            "model.demo.orders": {
                "resource_type": "model",
                "name": "orders",
                "description": "One row per order.",
                "config": {"materialized": "table"},
                "compiled_code": "select * from raw.orders",
                "depends_on": {"nodes": ["model.demo.raw_orders"]},
                "columns": {"order_id": {"description": "Primary key"}},
            },
            "seed.demo.ignore": {"resource_type": "seed", "name": "ignore"},
        }
    }))

    models = load_manifest_models(manifest)

    assert models["orders"]["description"] == "One row per order."
    assert models["orders"]["sql"] == "select * from raw.orders"
    assert models["orders"]["depends_on"] == ["raw_orders"]
    assert "ignore" not in models


def test_query_template_is_bounded_and_quality_counts_are_consistent(tmp_path: Path):
    db = tmp_path / "quality.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema marts")
    con.execute("create table marts.mart_customer_360 (customer_id varchar, churned boolean)")
    con.execute("insert into marts.mart_customer_360 values ('a', true), ('b', false)")
    con.execute("create table marts.churn_predictions (customer_id varchar, churn_probability double)")
    con.execute("insert into marts.churn_predictions values ('a', .8), ('b', .2)")

    sql = query_template("customer_sample", limit=7)
    assert "limit 7" in sql.lower()
    assert "select" in sql.lower()

    quality = quality_snapshot(con)
    con.close()
    assert quality["customers"] == 2
    assert quality["predictions"] == 2
    assert quality["duplicate_prediction_ids"] == 0
    assert quality["prediction_customer_join"] == 2
