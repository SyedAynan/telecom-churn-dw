# Telecom Churn Data Warehouse

A complete mini data platform that tells a telecom company **which customers are about to leave**. The classic IBM/Kaggle Telco Customer Churn dataset (~7,000 customers) is extracted and cleaned by Python ETL, landed in a **DuckDB** data warehouse, modeled with **dbt** as a star schema (staging → core → marts), summarized into analytics marts, and scored by a logistic-regression churn model whose **predictions are written back into the warehouse** — the pattern real ML-in-DW pipelines follow. A **Streamlit** dashboard finishes the story: overall churn rates, a downloadable high-risk watchlist, and the factors that drive churn.

## Architecture

```
 Kaggle (canonical) / IBM GitHub mirror
        │
        ▼
 etl/extract.py ────────────────► data/raw/Telco-Customer-Churn.csv   (.gitignored)
        │
 etl/transform.py  clean: TotalCharges blanks, yes/no flags, types
        │                          ▼
        │              data/processed/telco_clean.parquet           (.gitignored)
        ▼
 etl/load.py ─────────────────► DuckDB · raw schema (idempotent)
        │
        ▼
┌──────────────────── warehouse/telecom_churn.duckdb ────────────────────┐
│                                                                        │
│   raw ──dbt──► staging ──► core (star schema) ──► marts                │
│                                                                       │
│   core:  dim_contract   dim_service        dim_payment_method  dim_date │
│          fact_customer  fact_customer_services (service bridge)        │
│   marts: mart_customer_360   mart_churn_summary                        │
│                                                                        │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                ml/train.py ───┤  logistic regression, AUC + top features,
                               │  model saved with joblib
                ml/score.py ───┤  scores ALL customers, writes
                               ▼  marts.churn_predictions  ◄── write-back
                               │
                app/dashboard.py (Streamlit)
                  1. Overview   2. Watchlist   3. Factors
```

## Quick start

```bash
uv sync        # create venv (Python 3.12, pinned) + install deps
make all       # extract → transform → load → dbt build → train → score
make dashboard # Streamlit at http://localhost:8501
make test      # pytest
```

Requires [uv](https://docs.astral.sh/uv/) and Git. GNU `make` for the Makefile targets (ships with Git Bash on Windows). No API keys, no services — everything runs locally and free.

## Project layout

```
telecom-churn-dw/
├── etl/            extract / transform / load (Python, idempotent)
├── dbt/            dbt project: staging, core (star schema), marts
├── ml/             train.py, score.py (predictions written back to DW)
├── app/            Streamlit dashboard
├── tests/          pytest: ETL idempotency, dbt compile, scoring smoke
├── data/           raw/ + processed/ (gitignored, regenerable)
└── warehouse/      telecom_churn.duckdb (gitignored, regenerable)
```

## Data source

Kaggle `blastchar/telco-customer-churn` is the canonical origin, but it requires an account/API key. `etl/extract.py` therefore pulls the **byte-identical IBM mirror** (`IBM/telco-customer-churn-on-icp4d` on GitHub, MD5 `3b0bfab2…`) and verifies integrity on every run. Drop a manually downloaded Kaggle copy into `data/raw/` and the script will use it as-is.

## Notes

- Dataset snapshot period: February 2020 (IBM sample data). `dim_date` months are derived from tenure against a fixed as-of date, documented in the dbt models.
- Predictions land in `marts.churn_predictions` so BI/SQL users can join them to customer 360 without leaving the warehouse.
