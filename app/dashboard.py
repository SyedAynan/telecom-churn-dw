"""Streamlit dashboard for the Telecom Churn Data Warehouse.

Reads marts from warehouse/telecom_churn.duckdb — the dashboard is a view
over the warehouse, never a side-channel. Three pages: Overview, Watchlist,
Factors. Charts are custom HTML/SVG (app/charts.py) built to the dataviz
spec; everything carries a table view or direct labels so no value is
gated behind hover.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.charts import coefficient_chart, hbar_chart, risk_meter, style_kpi  # noqa: E402
from etl.paths import DB_PATH, MODELS_DIR  # noqa: E402

st.set_page_config(
    page_title="Telecom Churn DW",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

TITLE = "Telecom Churn Data Warehouse"


@st.cache_resource
def get_con() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        st.error(f"Warehouse not found at `{DB_PATH}` — run `make all` first.")
        st.stop()
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=60)
def load_table(sql: str) -> pd.DataFrame:
    return get_con().sql(sql).df()


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"## 📡 {TITLE}")
    st.caption("ETL → DuckDB star schema (dbt) → churn model → predictions written back")
    st.divider()
    page = st.radio(
        "Section",
        ["Overview", "Watchlist", "Factors"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Warehouse: `warehouse/telecom_churn.duckdb` (read-only)")
    st.caption("Run `make all` to refresh: ETL → dbt → train → score")

# ------------------------------------------------------------------ shared
summary = load_table("SELECT * FROM marts.mart_churn_summary")
base = load_table("""
    SELECT p.customer_id, p.churn_probability, p.risk_band, p.top_reason,
           m.tenure_bucket, m.contract_label, m.payment_method_label,
           m.monthly_charge_band, m.tenure_months, m.monthly_charges,
           m.total_charges, m.n_addons, m.churned
    FROM marts.churn_predictions p
    JOIN marts.mart_customer_360 m USING (customer_id)
""")


def seg(df: pd.DataFrame, seg_type: str) -> pd.DataFrame:
    return (
        df[df.segment_type == seg_type]
        .sort_values("segment_label")
        .reset_index(drop=True)
    )


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


# ==================================================================== pages
if page == "Overview":
    st.title("Churn overview")
    st.caption("February 2020 snapshot · 7,043 customers · source: IBM/Kaggle Telco churn")

    overall = base["churned"].mean()
    n_high = int((base["risk_band"] == "high").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        components.html(style_kpi("Overall churn rate", fmt_pct(overall)), height=78)
    with c2:
        components.html(
            style_kpi("Churned customers", f"{int(base.churned.sum()):,}"), height=78
        )
    with c3:
        components.html(
            style_kpi(
                "High-risk watchlist", f"{n_high}",
                delta="model p ≥ 75%", delta_good=False,
            ),
            height=78,
        )
    with c4:
        components.html(
            style_kpi("Avg monthly revenue", f"${base.monthly_charges.mean():.2f}"), height=78
        )

    st.divider()

    left, right = st.columns(2)
    with left:
        s = seg(summary, "contract")
        components.html(
            hbar_chart(
                "Churn rate by contract type",
                s.segment_label.tolist(),
                s.churn_rate.tolist(),
                subtitle="Month-to-month churns 15× more than two-year",
                color_slot=0,
            ),
            height=170,
        )
        s = seg(summary, "tenure_bucket")
        components.html(
            hbar_chart(
                "Churn rate by tenure bucket (months)",
                s.segment_label.tolist(),
                s.churn_rate.tolist(),
                subtitle="Risk halves every year of tenure",
                color_slot=1,
            ),
            height=170,
        )
    with right:
        s = seg(summary, "payment_method")
        components.html(
            hbar_chart(
                "Churn rate by payment method",
                s.segment_label.tolist(),
                s.churn_rate.tolist(),
                subtitle="Manual payment methods churn ~3× automatic",
                color_slot=0,
            ),
            height=170,
        )
        s = seg(summary, "monthly_charge_band")
        components.html(
            hbar_chart(
                "Churn rate by monthly charge band",
                s.segment_label.tolist(),
                s.churn_rate.tolist(),
                subtitle="Heavier monthly bills, heavier churn",
                color_slot=1,
            ),
            height=170,
        )

    with st.expander("Table view — full churn summary (all segments)"):
        st.dataframe(summary, use_container_width=True, height=260)


elif page == "Watchlist":
    st.title("High-risk watchlist")
    st.caption("Customers the model scores ≥ 75% churn probability — join customer_id "
               "back to `marts.mart_customer_360` for the full profile")

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
        "customer_id": "Customer", "churn_probability": "P(churn)",
        "risk_band": "Band", "top_reason": "Top reason",
        "contract_label": "Contract", "tenure_bucket": "Tenure",
        "monthly_charges": "Monthly $", "n_addons": "Add-ons", "churned": "Churned?",
    })[
        ["Customer", "P(churn)", "Band", "Top reason", "Contract",
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


else:  # Factors
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
        height=460,
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
        height=240,
    )

    st.markdown("#### Read the coefficients as odds ratios")
    st.caption(
        "Each coefficient is on standardized features (mean 0, std 1): +0.69 on monthly "
        "charges means a one-standard-deviation increase in the bill multiplies the "
        "churn odds by e^0.69 ≈ 2.0, holding everything else fixed. Tenure is the "
        "strongest protective factor: one σ more tenure divides the odds by e^1.21 ≈ 3.3."
    )
