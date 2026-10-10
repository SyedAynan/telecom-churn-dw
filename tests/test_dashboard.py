"""Exercise dashboard navigation and displayed warehouse values."""
from __future__ import annotations

import duckdb
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app import simulator
from etl.paths import DB_PATH, PROJECT_ROOT
from ml.features import FEATURE_COLUMNS, build_matrix


@pytest.fixture
def dashboard(monkeypatch):
    # Keep the stream deterministic without starting a background writer.
    sim = simulator.Simulator(pd.DataFrame(), seed=3)
    monkeypatch.setattr(simulator, "get_simulator", lambda *args, **kwargs: sim)
    app = AppTest.from_file(str(PROJECT_ROOT / "app" / "dashboard.py"), default_timeout=30)
    yield app
    st.cache_data.clear()
    st.cache_resource.clear()


def test_pipeline_displays_the_features_used_for_scoring(dashboard):
    dashboard.run()
    dashboard.sidebar.radio[0].set_value("Pipeline").run()
    assert not dashboard.exception
    frames = [element.value for element in dashboard.dataframe]
    mart = next(frame for frame in frames if "payment_automation" in frame.columns)
    displayed = next(frame for frame in frames if list(frame.columns) == FEATURE_COLUMNS)
    pd.testing.assert_frame_equal(displayed, build_matrix(mart), check_dtype=False)


@pytest.mark.parametrize("page", ["Overview", "Watchlist", "Factors", "Live", "Warehouse"])
def test_dashboard_pages_render_without_exceptions(dashboard, page):
    dashboard.run()
    dashboard.sidebar.radio[0].set_value(page).run()
    assert not dashboard.exception


def test_overview_retention_value_counts_each_customer_once(dashboard):
    dashboard.run()
    dashboard.sidebar.selectbox(key="data_mode").select("Warehouse snapshot").run()
    assert not dashboard.exception
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        expected = con.sql("""
            SELECT SUM(addressable_revenue) FROM marts.mart_revenue_analytics
            WHERE segment_type = 'risk_band'
        """).fetchone()[0]
    tiles = [element.proto.body for element in dashboard.get("html")]
    retention_tile = next(tile for tile in tiles if "Addressable retention value" in tile)
    assert f"${expected:,.0f}" in retention_tile


def test_dynamic_overview_updates_charts_and_freezes_when_paused(dashboard, monkeypatch):
    import app.dynamic as dynamic

    monkeypatch.setattr(dynamic, "current_second", lambda: 100)
    dashboard.run()
    first = dashboard.session_state["visible_customers"].copy()
    first_html = next(e.proto.body for e in dashboard.get("html") if "stats-grid" in e.proto.body)
    monkeypatch.setattr(dynamic, "current_second", lambda: 101)
    dashboard.run()
    second = dashboard.session_state["visible_customers"].copy()
    second_html = next(e.proto.body for e in dashboard.get("html") if "stats-grid" in e.proto.body)
    assert not first.churned.equals(second.churned)
    assert first_html != second_html
    assert "Simulated live demo" in second_html
    dashboard.sidebar.toggle[0].set_value(False).run()
    monkeypatch.setattr(dynamic, "current_second", lambda: 102)
    dashboard.run()
    pd.testing.assert_frame_equal(second, dashboard.session_state["visible_customers"])
    dashboard.sidebar.toggle[0].set_value(True).run()
    assert not second.monthly_charges.equals(dashboard.session_state["visible_customers"].monthly_charges)


def test_refresh_does_not_rebuild_csv_until_download(dashboard, monkeypatch):
    calls = []
    original = pd.DataFrame.to_csv

    def tracked(frame, *args, **kwargs):
        calls.append(len(frame))
        return original(frame, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_csv", tracked)
    dashboard.run()
    dashboard.run()
    assert not dashboard.exception
    assert calls == []


@pytest.mark.parametrize("provider", ["Jio", "Vi", "Airtel", "BSNL"])
def test_provider_selection_filters_the_overview_and_export(dashboard, provider):
    from app.providers import assign_provider

    dashboard.run()
    dashboard.selectbox(key="provider_filter").select(provider).run()
    assert not dashboard.exception
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        ids = con.sql("SELECT customer_id FROM marts.churn_predictions").df().customer_id
    expected = sum(assign_provider(cid) == provider for cid in ids)
    page = next(element.proto.body for element in dashboard.get("html") if "stats-grid" in element.proto.body)
    assert f'{expected:,}</div>' in page
    assert f"{provider} overview" in page
    assert set(dashboard.session_state["visible_customers"].provider) == {provider}


def test_watchlist_identifies_provider_in_customer_report(dashboard):
    dashboard.run()
    dashboard.sidebar.radio[0].set_value("Watchlist").run()
    dashboard.selectbox(key="watchlist_provider").select("BSNL").run()
    assert not dashboard.exception
    report = dashboard.dataframe[0].value
    assert len(report) > 0
    assert set(report["Provider (demo)"]) == {"BSNL"}


def test_live_filters_and_pause_keep_a_consistent_snapshot(dashboard, monkeypatch):
    import time

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        cid = con.sql("SELECT customer_id FROM marts.churn_predictions LIMIT 1").fetchone()[0]
    sim = simulator.Simulator(pd.DataFrame(), seed=3)
    sim._events = [
        simulator.Event(time.time(), cid, "Jio", "payment", "paid"),
        simulator.Event(time.time(), cid, "Jio", "ticket", "help"),
        simulator.Event(time.time(), cid, "Vi", "payment", "paid"),
    ]
    monkeypatch.setattr(simulator, "get_simulator", lambda *args, **kwargs: sim)
    dashboard.run()
    dashboard.sidebar.radio[0].set_value("Live").run()
    assert not dashboard.exception
    dashboard.multiselect(key="live_providers").set_value(["Jio"]).run()
    assert len(dashboard.session_state["live_visible_events"]) == 2
    dashboard.sidebar.toggle[0].set_value(False).run()
    frozen = dashboard.session_state["live_snapshot"][2]
    sim._events.append(simulator.Event(time.time(), cid, "Jio", "ticket", "another"))
    dashboard.selectbox(key="live_feed_mode").select("Negative only").run()
    assert dashboard.session_state["live_snapshot"][2] == frozen
    assert len(dashboard.session_state["live_visible_events"]) == 2
    dashboard.sidebar.toggle[0].set_value(True).run()
    assert len(dashboard.session_state["live_visible_events"]) == 3
    dashboard.multiselect(key="live_providers").set_value([]).run()
    assert dashboard.session_state["live_visible_events"].empty
    assert not dashboard.exception
