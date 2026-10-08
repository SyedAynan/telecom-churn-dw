# Telecom Churn Data Warehouse

A complete mini data platform that tells a telecom company **which customers are about to leave**. The classic IBM/Kaggle Telco Customer Churn dataset (~7,000 customers) is extracted and cleaned by Python ETL, landed in a **DuckDB** data warehouse, modeled with **dbt** as a star schema (staging → core → marts), summarized into analytics marts, and scored by a logistic-regression churn model whose **predictions are written back into the warehouse** — the pattern real ML-in-DW pipelines follow. A **Streamlit** dashboard finishes the story: overall churn rates, a downloadable high-risk watchlist, and the factors that drive churn — with an animated motion layer (count-up KPI tiles with sparklines, staggered bar entrances, a live segment ticker; `prefers-reduced-motion` respected everywhere, no external animation libraries).

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
│                                                                        │
│   core:  dim_contract   dim_service        dim_payment_method  dim_date│
│          fact_customer  fact_customer_services (service bridge)        │
│   marts: mart_customer_360   mart_churn_summary   churn_predictions ◄──┼── ml/score.py
│                                                                        │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                ml/train.py ───┤  logistic regression, AUC + top features,
                               │  model saved with joblib
                ml/score.py ───┘  scores ALL customers, writes predictions
                               back into the warehouse
                               │
                app/dashboard.py (Streamlit)
                  1. Overview   2. Watchlist   3. Factors
```

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (and Git; GNU make ships with Git Bash on Windows).

```bash
uv sync          # venv on pinned Python 3.12 + all dependencies
make all         # extract → transform → load → dbt build → train → score
make dashboard   # Streamlit at http://localhost:8501
make test        # pytest: ETL idempotency, dbt compile, scoring smoke
```

Verified on Windows 11 / Python 3.12.14 / dbt 1.12.5 / DuckDB 1.3.2 — `make all` runs clean from an empty warehouse in under a minute. On this machine the `streamlit` console script is blocked by an Application Control policy, so the Makefile runs `python -m streamlit` instead (identical behavior).

> **Note:** the dashboard holds a read-only DuckDB handle; `make all` / `make etl` / `make train` need write access. Stop the dashboard (Ctrl+C in its terminal) before rebuilding, then restart it — that's ordinary DuckDB single-writer semantics, not a bug.

## Results (real numbers from the built warehouse)

**Model — logistic regression, holdout AUC 0.8351** (25% stratified split, features standardized):

| Rank | Feature | Coefficient | Meaning |
|---|---|---|---|
| 1 | Tenure (months) | −1.209 | strongest protection: each σ of tenure ÷3.3 churn odds |
| 2 | Monthly charges | +0.692 | each σ of bill ×2.0 churn odds |
| 3 | Contract length | −0.644 | long contracts anchor customers |
| 4 | Total charges | +0.559 | low lifetime spend = risk |
| 5 | Add-on services | −0.378 | service depth retains |

**Churn rate by segment** (from `marts.mart_churn_summary`):

| Segment | Churn rate |
|---|---|
| Month-to-month contract | **42.7%** |
| One-year contract | 11.3% |
| Two-year contract | 2.8% |
| Tenure 0–12 months | **47.4%** |
| Tenure 49–72 months | 9.5% |
| Electronic check payment | **45.3%** |
| Automatic payments (bank/credit) | ~16% |
| Monthly charge ≥ $85 | 33.9% |

**Watchlist calibration** — predictions written back to `marts.churn_predictions` and joined to actual outcomes: the **high band (p ≥ 0.75, 98 customers) is 86.7% actual churn**; medium 59.6%; low 14.4%. The top watchlist profile: brand-new customers on month-to-month contracts paying top-of-market rates.

### Dashboard

| | |
|---|---|
| ![Overview](docs/screenshots/overview-motion.png) | ![Watchlist](docs/screenshots/watchlist-motion.png) |

The Watchlist page (right) is the intervention queue: filter by band, contract, tenure, and minimum probability, then download the CSV for the retention team. The Factors page shows the standardized coefficient chart and the dominant risk reasons on the live watchlist (`docs/screenshots/factors-motion.png`).

## Project layout

```
telecom-churn-dw/
├── etl/            extract / transform / load (Python, idempotent)
├── dbt/            dbt project: staging, core (star schema), marts
├── ml/             train.py, score.py (predictions written back to DW)
├── app/            Streamlit dashboard + hand-built SVG chart kit + motion chrome
├── tests/          pytest: ETL idempotency, dbt compile, scoring smoke
├── data/           raw/ + processed/ (gitignored, regenerable)
├── docs/           screenshots
└── warehouse/      telecom_churn.duckdb (gitignored, regenerable)
```

## Data source

Kaggle `blastchar/telco-customer-churn` is the canonical origin, but it requires an account/API key. `etl/extract.py` therefore pulls the **byte-identical IBM mirror** (`IBM/telco-customer-churn-on-icp4d` on GitHub, MD5-verified on every run) — or accepts a manually downloaded Kaggle copy dropped into `data/raw/`. Dataset snapshot period: February 2020 (IBM sample data). `dim_date` months are derived from tenure against a fixed as-of date of 2020-02-01, documented in `dbt/models/core/dim_date.sql`.

## Warehouse conventions

- **Schema-per-layer**: `raw` (landing, typed by ETL) → `staging` (views, renames + standardization + the one business rule) → `core` (star schema, tables) → `marts` (analytics + ML outputs).
- **Grain documented on every model** in its SQL header and YAML: `fact_customer` 1 row/customer, `fact_customer_services` 1 row/(customer, service), `dim_*` 1 row/natural key.
- **Tested keys**: 43 dbt tests — unique + not_null on every key, accepted_values on contract/internet/gender/churn, relationship tests on every fact FK, unique (customer, service) combination on the bridge, plus a singular test guarding the TotalCharges business rule (demonstrated red → green during the build).
- **Business rules live in the warehouse**, not the ETL: ETL types and standardizes; staging owns the `total_charges = 0 for tenure 0` imputation, with a test that fails loudly if it regresses.
- **Predictions live in the warehouse**: `marts.churn_predictions` joins 1:1 to `mart_customer_360`, so BI/SQL users reach churn risk without leaving DuckDB.

## Development

```bash
make etl          # re-run the pipeline into raw
make dbt-build    # rebuild + retest all models
make train        # retrain, refresh AUC
make score        # rescore, overwrite marts.churn_predictions
make clean        # remove warehouse + dbt artifacts (data/ persists)
```
