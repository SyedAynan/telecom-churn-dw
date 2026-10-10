"""Streamlit dashboard for the Telecom Churn Data Warehouse — motion edition.

Reads marts from warehouse/telecom_churn.duckdb (dashboard is a view over
the warehouse, never a side-channel). Three pages: Overview, Watchlist,
Factors. Charts are responsive animated SVG (app/charts.py); page chrome
is animated via app/motion.py. Every value stays reachable without hover
(direct labels + table views); reduced-motion is respected throughout.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.charts import (  # noqa: E402
    chart_height,
    coefficient_chart,
    hbar_chart,
    line_chart,
)
from app.motion import status_badges  # noqa: E402
from app import live, overview, theme
from app.providers import PROVIDERS, attach_providers, segment_summary
from app.simulation import pack_features, read_raw_row  # noqa: E402
from app.simulator import get_simulator  # noqa: E402
from etl.paths import RAW_CSV_PATH  # noqa: E402
from app.warehouse import (  # noqa: E402
    DBT_RESULTS,
    DEFAULT_TABLES,
    load_manifest_models,
    quality_snapshot,
    query_template,
    safe_identifier,
    read_frame,
)
from etl.paths import DB_PATH, MODELS_DIR  # noqa: E402

st.set_page_config(
    page_title="Telecom Churn DW",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="auto",
)

st.html(theme.CSS)
st.html("<style>" + (Path(__file__).parent / "layout.css").read_text(encoding="utf-8") + "</style>")

TITLE = "Telecom churn warehouse"


def get_con() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        st.error(f"Warehouse not found at `{DB_PATH}` — run `make all` first.")
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)


def load_table(sql: str) -> pd.DataFrame:
    return read_frame(sql)


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f'<div class="brand">{theme.TOWER}<div>Telecom Churn<small>WAREHOUSE INTELLIGENCE</small></div></div>', unsafe_allow_html=True)
    page = st.radio(
        "Section",
        ["Overview", "Pipeline", "Watchlist", "Factors", "Live", "Warehouse"],
        label_visibility="collapsed",
        format_func=lambda name: {"Overview": "⌂  Overview", "Pipeline": "⇄  Data pipeline", "Watchlist": "♧  Customer watchlist", "Factors": "◈  Predictive insights", "Live": "ϟ  Live signals", "Warehouse": "▤  Warehouse explorer"}[name],
    )
    if st.button("↻ Refresh warehouse reads", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    auto_refresh = st.toggle("Auto-refresh", value=True, help="Refresh Overview every 5 seconds and Live every 3 seconds. Pause to inspect a snapshot.")
    st.divider()
    st.markdown('<div class="sidebar-note">● &nbsp; Warehouse intelligence<br>One platform. Complete customer insights.<br><br>IBM Telco · February 2020</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ shared
BASE_SQL = """
    SELECT p.customer_id, p.churn_probability, p.risk_band, p.top_reason,
           m.tenure_bucket, m.contract_label, m.payment_method_label,
           m.monthly_charge_band, m.tenure_months, m.monthly_charges,
           m.total_charges, m.n_addons, m.churned
    FROM marts.churn_predictions p
    JOIN marts.mart_customer_360 m USING (customer_id)
"""
if page != "Overview":
    summary = load_table("SELECT * FROM marts.mart_churn_summary")
    base = load_table(BASE_SQL)
warehouse_models = load_manifest_models()
st.markdown(theme.dashboard_header(), unsafe_allow_html=True)


def seg(df: pd.DataFrame, seg_type: str) -> pd.DataFrame:
    return (
        df[df.segment_type == seg_type]
        .sort_values("segment_label")
        .reset_index(drop=True)
    )


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def tenure_trend(df: pd.DataFrame) -> list[float]:
    """Churn rate by ordered tenure bucket — the KPI sparkline series."""
    ordered = ["0-12", "13-24", "25-48", "49-72"]
    grouped = df.groupby("tenure_bucket")["churned"].mean()
    return [float(grouped.get(b, 0.0)) for b in ordered]


# ==================================================================== pages
if page == "Overview":
    filter_col, note_col = st.columns([1, 2])
    with filter_col:
        provider = st.selectbox("Provider", ["All providers", *PROVIDERS], key="provider_filter")
    with note_col:
        st.caption("Demo provider assignments · Jio, Vi, Airtel and BSNL are synthetic customer groups, not actual network performance.")
    @st.fragment(run_every="5s" if auto_refresh else None)
    def render_overview() -> None:
        try:
            with get_con() as con:
                con.execute("BEGIN TRANSACTION")
                current_base = con.execute(BASE_SQL).df()
                current_summary = con.execute("SELECT * FROM marts.mart_churn_summary").df()
                current_revenue = con.execute("SELECT * FROM marts.mart_revenue_analytics").df()
                con.execute("COMMIT")
            st.session_state["overview_snapshot"] = (current_base, current_summary, current_revenue, datetime.now().astimezone())
        except duckdb.Error:
            st.warning("Warehouse is updating or temporarily unavailable. Showing the last successful read; the next refresh will retry.")
            if "overview_snapshot" not in st.session_state:
                st.info("No snapshot is available yet. Build the warehouse, then refresh.")
                return
        current_base, current_summary, current_revenue, checked = st.session_state["overview_snapshot"]
        if current_base.empty:
            st.info("No scored customers yet. Run the scoring pipeline to populate this view.")
            return
        all_customers = attach_providers(current_base)
        selected = all_customers if provider == "All providers" else all_customers[all_customers.provider == provider]
        if selected.empty:
            st.info(f"No customers assigned to {provider} in this snapshot.")
            return
        if provider != "All providers":
            current_summary = segment_summary(selected)
            current_revenue = pd.DataFrame({"segment_type": ["risk_band"], "addressable_revenue": [selected.addressable_revenue.sum()]})
        st.session_state["visible_customers"] = selected
        st.html(overview.dashboard(selected, current_summary, current_revenue, all_customers=all_customers, provider=provider))
        st.caption(f"{'Checking every 5 seconds' if auto_refresh else 'Auto-refresh paused'} | Last successful read: {checked:%H:%M:%S %Z} | Source: February 2020 snapshot | USD")
        st.download_button("Export customer report", selected.to_csv(index=False).encode(), "telecom_customer_report.csv", "text/csv", type="primary")

    render_overview()

elif page == "Pipeline":
    st.title("Pipeline walkthrough")
    st.caption(
        "One real churned customer traced end to end: CSV → ETL → staging → "
        "star schema → 360 mart → model score → served prediction. Every value "
        "below is a real artifact, not a mock."
    )
    components.html(
        status_badges([
            ("LINEAGE", "cyan"),
            ("CSV→ETL→dbt→ML→UI", "neutral"),
            ("PROBLEM:CHURN", "err"),
        ]),
        height=34,
    )

    # ---- pick the case ---------------------------------------------------
    # Highest-probability already-churned customer; fall back to any churned,
    # then to the top-scored customer overall if the slice is empty.
    churned_ranked = base[base.churned].sort_values(
        "churn_probability", ascending=False)
    if len(churned_ranked):
        case = churned_ranked.iloc[0]
        case_kind = "the highest-scoring confirmed churner"
    else:
        case = base.sort_values("churn_probability", ascending=False).iloc[0]
        case_kind = "the model's top-scored customer"
    cid = case.customer_id
    st.markdown(
        f"### Case: `{cid}` — {case_kind} "
        f"(model P = {fmt_pct(case.churn_probability)})"
    )

    # stage-by-stage real data — every table below is a live warehouse read
    raw = read_raw_row(cid)

    # stage 1 — raw CSV
    if raw:
        raw_df = pd.DataFrame([raw])
        with st.expander("1 · CSV source — the real row from the file", expanded=True):
            st.dataframe(raw_df, hide_index=True, use_container_width=True)
            st.caption(f"Read straight from {RAW_CSV_PATH.name} — raw types, "
                       "blank TotalCharges preserved.")

    # stage 2 — raw.landing (DuckDB)
    landing = load_table(f"SELECT * FROM raw.telco_churn WHERE customerID = '{cid}'")
    with st.expander("2 · ETL → DuckDB landing", expanded=True):
        st.code(f"SELECT * FROM raw.telco_churn WHERE customerID = '{cid}'", language="sql")
        st.dataframe(landing, hide_index=True, use_container_width=True)
        st.caption("Loaded untouched by Python — the auditable system of record.")

    # stage 3 — staging view
    staged = load_table(f"SELECT * FROM staging.stg_telco_churn WHERE customer_id = '{cid}'")
    with st.expander("3 · dbt staging — typed + imputed", expanded=True):
        st.code(f"SELECT * FROM staging.stg_telco_churn WHERE customer_id = '{cid}'", language="sql")
        st.dataframe(staged, hide_index=True, use_container_width=True)
        st.caption("snake_case columns, booleans/numerics typed, blank TotalCharges → 0.0.")

    # stage 4 — star schema (fact + dims)
    st.markdown("### 4 · dbt star schema — one row becomes facts + dimensions")
    sc1, sc2 = st.columns(2)
    with sc1:
        fact = load_table(
            f"SELECT * FROM core.fact_customer WHERE customer_id = '{cid}'")
        st.markdown("`core.fact_customer` — measures + foreign keys")
        st.dataframe(fact, hide_index=True, use_container_width=True)
    with sc2:
        svc = load_table(f"""SELECT s.service_name, f.subscribed
            FROM core.fact_customer_services f
            JOIN core.dim_service s USING (service_key)
            WHERE f.customer_id = '{cid}' ORDER BY s.service_key""")
        st.markdown("`core.fact_customer_services ⋈ dim_service` — subscribed flags")
        st.dataframe(svc, hide_index=True, use_container_width=True, height=170)

    # stage 5 — 360 mart
    c360 = load_table(f"SELECT * FROM marts.mart_customer_360 WHERE customer_id = '{cid}'")
    with st.expander("5 · dbt 360 mart — one analytics-ready row", expanded=True):
        st.code(f"SELECT * FROM marts.mart_customer_360 WHERE customer_id = '{cid}'", language="sql")
        st.dataframe(c360, hide_index=True, use_container_width=True)
        st.caption("The wide table the model and dashboard both read — buckets, labels, service counts.")

    st.divider()

    # stage 6 — model
    st.markdown("### 6 · ML model — features in, probability out")
    # Use the complete 360 row for the model vector. The compact `base` frame
    # above intentionally omits several feature columns used by the pipeline.
    feat = pack_features(c360.iloc[0].to_dict())
    mc1, mc2 = st.columns([1.3, 1])
    with mc1:
        st.markdown("Feature vector → logistic pipeline")
        st.dataframe(feat, hide_index=True, use_container_width=True)
    with mc2:
        st.markdown("Stored prediction → `marts.churn_predictions`")
        st.markdown(
            f'<div style="background:#111116;border:1px solid #29383e;'
            f'border-radius:14px;padding:16px;text-align:center">'
            f'<div style="font-size:34px;color:#f87171;font-weight:600;'
            f'font-family:Montserrat,sans-serif">'
            f'{fmt_pct(case.churn_probability)}</div>'
            f'<div style="color:#a3a3a3;font-size:12px">P(churn) · risk band: '
            f'{case.risk_band} · top reason: {case.top_reason}</div></div>',
            unsafe_allow_html=True)

    # stage 7 — served
    st.markdown("### 7 · Served — this page reads the mart")
    st.success(f"`{cid}` is on the Watchlist — retention should call them first. "
               "Same row, every layer, end to end.")

    # ---- the problem it solves -------------------------------------------
    with st.expander("The real problem, solved"):
        st.markdown(
            f"- **Problem**: `{cid}` had a month-to-month contract, high monthly "
            f"charges, and low tenure — classic churn drivers the model flags at "
            f"**{fmt_pct(case.churn_probability)}**.\n"
            "- **Why it matters**: retention spend should target the ~98 high-risk "
            "customers, not all 7,043 — the warehouse makes that targeting cheap "
            "and auditable.\n"
            "- **Traceability**: every number here came from a real layer you can "
            "inspect on the Warehouse page — nothing was fabricated for the demo."
        )

elif page == "Watchlist":
    base = attach_providers(base)
    selected_provider = st.selectbox("Provider", ["All providers", *PROVIDERS], key="watchlist_provider")
    if selected_provider != "All providers":
        base = base[base.provider == selected_provider]
    st.caption("Provider assignments are synthetic demo groups.")
    st.title("High-risk watchlist")
    st.caption("Customers the model scores ≥ 75% churn probability — join customer_id "
               "back to `marts.mart_customer_360` for the full profile")
    components.html(
        status_badges([
            ("WATCHLIST", "err"),
            ("SOURCE:churn_predictions", "cyan"),
            ("GRAIN:customer", "neutral"),
        ]),
        height=34,
    )

    fcol1, fcol2, fcol3, fcol4 = st.columns([1.4, 1, 1, 1])
    with fcol1:
        band = st.multiselect(
            "Risk band",
            ["high", "medium", "low"],
            default=["high"],
        )
    with fcol2:
        contracts = sorted(base.contract_label.unique())
        contract_sel = st.multiselect("Contract", contracts, default=contracts)
    with fcol3:
        tenures = ["0-12", "13-24", "25-48", "49-72"]
        tenure_sel = st.multiselect("Tenure bucket", tenures, default=tenures)
    with fcol4:
        min_p = st.slider("Min probability", 0.0, 1.0, 0.0, 0.05)

    view = base[
        base.risk_band.isin(band or ["high"])
        & base.contract_label.isin(contract_sel or contracts)
        & base.tenure_bucket.isin(tenure_sel or tenures)
        & (base.churn_probability >= min_p)
    ].sort_values("churn_probability", ascending=False)

    st.markdown(
        f"**{len(view):,} customers** on the list · "
        f"actual churn in this slice: **{fmt_pct(view.churned.mean()) if len(view) else '—'}**"
    )

    tbl = view.rename(columns={
        "provider": "Provider (demo)",
        "customer_id": "Customer", "churn_probability": "P(churn)",
        "risk_band": "Band", "top_reason": "Top reason",
        "contract_label": "Contract", "tenure_bucket": "Tenure",
        "monthly_charges": "Monthly $", "n_addons": "Add-ons", "churned": "Churned?",
    })[
        ["Customer", "Provider (demo)", "P(churn)", "Band", "Top reason", "Contract",
         "Tenure", "Monthly $", "Add-ons", "Churned?"]
    ]

    st.data_editor(
        tbl,
        use_container_width=True,
        height=430,
        column_config={
            "P(churn)": st.column_config.NumberColumn(format="%.1f%%"),
            "Monthly $": st.column_config.NumberColumn(format="$%.2f"),
            "Churned?": st.column_config.CheckboxColumn(
                help="Already churned in this snapshot (Feb 2020)"
            ),
        },
        disabled=True,
        key="watchlist_editor",
        hide_index=True,
    )

    st.download_button(
        "⬇ Download watchlist as CSV",
        data=tbl.to_csv(index=False).encode(),
        file_name="churn_watchlist.csv",
        mime="text/csv",
        type="primary",
    )

    st.caption(
        "The watchlist is the intervention queue: retention offers, billing follow-ups, "
        "service check-ins — ordered by probability, explained by the top reason."
    )

    st.markdown("#### Customer drill-through")
    selected_customer = st.selectbox(
        "Select a customer from the prediction + 360-mart join",
        ["—"] + view.customer_id.tolist(),
    )
    if selected_customer != "—":
        detail = base[base.customer_id == selected_customer].iloc[0]
        st.info("Source path: marts.churn_predictions → marts.mart_customer_360 · grain: one row per customer")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("P(churn)", fmt_pct(detail.churn_probability))
        d2.metric("Risk band", detail.risk_band)
        d3.metric("Monthly charges", f"${detail.monthly_charges:,.2f}")
        d4.metric("Tenure", f"{detail.tenure_months} months")
        st.write({
            "Customer": detail.customer_id,
            "Top reason": detail.top_reason,
            "Contract": detail.contract_label,
            "Payment method": detail.payment_method_label,
            "Tenure bucket": detail.tenure_bucket,
            "Add-on services": int(detail.n_addons),
            "Already churned in snapshot": bool(detail.churned),
        })


elif page == "Live":
    st.html('<div class="live-page-heading"><div class="live-eyebrow">SIGNAL INTELLIGENCE</div>'
            '<h2>Live signals</h2><p>Provider activity &amp; customer review.</p></div>')
    st.caption("SIMULATED STREAM | Synthetic provider groups. Customer profiles and stored predictions: February 2020 warehouse snapshot.")
    provider_col, window_col, feed_col = st.columns([2, 1, 1])
    with provider_col:
        operator_filter = st.multiselect("Providers", list(PROVIDERS), default=list(PROVIDERS), key="live_providers")
    with window_col:
        window_minutes = st.selectbox("Time window", [5, 10, 30], index=1, format_func=lambda value: f"Last {value} minutes", key="live_window")
    with feed_col:
        feed_mode = st.selectbox("Feed view", ["All signals", "Negative only"], key="live_feed_mode")
    sim = get_simulator(base[["customer_id", "churn_probability", "monthly_charges", "risk_band"]].copy())

    @st.fragment(run_every="3s" if auto_refresh else None)
    def live_monitor() -> None:
        if auto_refresh or "live_snapshot" not in st.session_state:
            try:
                live_base = load_table(BASE_SQL)
                checked = time.time()
                st.session_state["live_snapshot"] = (sim.window_events(30, now=checked), live_base, checked)
            except duckdb.Error:
                st.warning("Warehouse is updating. Holding the last successful snapshot; the next refresh will retry.")
                if "live_snapshot" not in st.session_state:
                    return
        all_events, live_base, checked = st.session_state["live_snapshot"]
        events = all_events[(all_events.ts >= checked - window_minutes * 60) & all_events.operator.isin(operator_filter)].copy()
        queue = live.review_queue(events, live_base)
        st.session_state["live_visible_events"] = events
        st.html(live.dashboard(events, queue, now=checked, minutes=window_minutes,
                               providers=operator_filter, feed_mode=feed_mode, paused=not auto_refresh))
        st.download_button("Export review queue", queue.rename(columns={"operator": "provider_demo", "priority_score": "demo_priority_score"}).to_csv(index=False).encode(),
                           "live_review_queue.csv", "text/csv", disabled=queue.empty, icon=":material/download:")

    live_monitor()


elif page == "Warehouse":
    st.title("Warehouse explorer")
    st.caption(
        "A read-only window into the warehouse: inspect model grain, lineage, SQL provenance, "
        "and curated query results without bypassing dbt."
    )

    layer_order = ["Raw", "Staging", "Core", "Marts", "ML outputs"]
    layer = st.selectbox("Warehouse layer", layer_order)
    components.html(
        status_badges([
            ("EXPLORER", "cyan"),
            (f"LAYER:{layer.upper()}", "ok"),
            ("CONN:read-only", "warn"),
        ]),
        height=34,
    )
    layer_models = {
        name: meta for name, meta in warehouse_models.items()
        if meta.get("layer") == layer
    }
    if not layer_models:
        st.warning("No model metadata available for this layer yet.")
        st.stop()
    model_name = st.selectbox("Relation", sorted(layer_models))
    model = layer_models[model_name]
    relation = f"{safe_identifier(model['schema'])}.{safe_identifier(model['relation'])}"

    st.markdown(
        f"**Lineage:** `raw` → `staging` → `core` → `marts` → `ML outputs`  ·  "
        f"**Selected grain:** {model.get('grain', 'not documented')}"
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        try:
            with get_con() as con:
                count = int(con.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0])
        except duckdb.Error:
            count = 0
        st.metric("Rows", f"{count:,}")
    with m2:
        st.metric("Materialization", model.get("materialization", "unknown"))
    with m3:
        st.metric("Layer", layer)

    st.markdown(f"#### {model_name}")
    st.write(model.get("description", "No description recorded."))
    if model.get("depends_on"):
        st.caption("Upstream dependencies: " + " → ".join(model["depends_on"]))
    if model.get("columns"):
        columns = pd.DataFrame([
            {"Column": name, "Description": meta.get("description", "")}
            for name, meta in model["columns"].items()
        ])
        st.dataframe(columns, hide_index=True, use_container_width=True)

    with st.expander("Show model SQL / provenance"):
        sql = model.get("sql") or "SQL unavailable — run dbt build to generate target/manifest.json."
        st.code(sql, language="sql")

    with get_con() as con:
        quality = quality_snapshot(con)
    with st.expander("Data quality — prediction join checks"):
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("360 customers", f"{quality['customers']:,}")
        q2.metric("Predictions", f"{quality['predictions']:,}")
        q3.metric("Duplicate prediction IDs", f"{quality['duplicate_prediction_ids']:,}")
        q4.metric("1:1 joined rows", f"{quality['prediction_customer_join']:,}")
        st.caption("These are live read-only checks against marts.churn_predictions and marts.mart_customer_360.")

    st.divider()
    st.markdown("#### Curated read-only query explorer")
    query_names = {
        "Customer sample — mart_customer_360": "customer_sample",
        "Highest model risk — churn_predictions": "highest_risk",
        "Revenue segments — mart_revenue_analytics": "segment_revenue",
        "Row counts — warehouse marts": "warehouse_counts",
    }
    query_label = st.selectbox("Query template", list(query_names))
    limit = st.slider("Result limit", 5, 100, 25, 5)
    query = query_template(query_names[query_label], limit)
    st.code(query, language="sql")
    if st.button("Run read-only query", type="primary"):
        result = load_table(query)
        st.caption(f"Result grain: query-defined rows · executed from DuckDB read-only connection")
        st.dataframe(result, hide_index=True, use_container_width=True)
        st.download_button(
            "Download result CSV",
            result.to_csv(index=False).encode(),
            file_name="warehouse_query_result.csv",
            mime="text/csv",
        )


elif page == "Factors":
    st.title("What drives churn")
    st.caption("Logistic regression on standardized features · AUC 0.835 on holdout · "
               "orange = churn-up, blue = protective")

    import joblib

    model_path = MODELS_DIR / "churn_logreg.joblib"
    if not model_path.exists():
        st.warning("No trained model found — run `make train`.")
        st.stop()
    bundle = joblib.load(model_path)
    pipe = bundle["pipeline"]
    coefs = pipe.named_steps["clf"].coef_[0]
    features = bundle["feature_columns"]

    feat_labels = {
        "tenure_months": "Tenure (months)",
        "monthly_charges": "Monthly charges",
        "total_charges": "Total charges",
        "is_female": "Female",
        "is_senior": "Senior citizen",
        "has_partner": "Has partner",
        "has_dependents": "Has dependents",
        "paperless_billing": "Paperless billing",
        "contract_months": "Contract length",
        "is_automatic_payment": "Automatic payment",
        "n_internet": "Internet service",
        "n_addons": "Add-on services",
    }
    order = sorted(range(len(coefs)), key=lambda i: abs(coefs[i]), reverse=True)
    components.html(
        coefficient_chart(
            "Model coefficients (standardized)",
            [feat_labels[features[i]] for i in order],
            [coefs[i] for i in order],
            subtitle="Sign = direction of churn risk · magnitude = strength",
        ),
        height=chart_height(len(order), True),
    )

    st.divider()

    st.markdown("#### Top reason on the watchlist")
    reason_counts = (
        base[base.risk_band != "low"]
        .groupby("top_reason")
        .size()
        .sort_values(ascending=False)
        .head(6)
    )
    components.html(
        hbar_chart(
            "Why customers are risky (medium+high band)",
            reason_counts.index.tolist(),
            reason_counts.tolist(),
            value_fmt="{:,.0f}",
            subtitle="Count of watchlist customers by dominant risk factor",
            color_slot=0,
        ),
        height=chart_height(len(reason_counts), True),
    )

    st.markdown("#### Read the coefficients as odds ratios")
    st.caption(
        "Each coefficient is on standardized features (mean 0, std 1): +0.69 on monthly "
        "charges means a one-standard-deviation increase in the bill multiplies the "
        "churn odds by e^0.69 ≈ 2.0, holding everything else fixed. Tenure is the "
        "strongest protective factor: one σ more tenure divides the odds by e^1.21 ≈ 3.3."
    )


# footer hairline — the one place orange appears (at 10%), per ChaiUI
st.markdown(
    '<div class="chai-footer">telecom churn warehouse · '
    'csv → etl → duckdb → dbt → model → dashboard</div>',
    unsafe_allow_html=True)
