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
uv run dbt deps --project-dir dbt --profiles-dir dbt  # install pinned dbt_utils
make run         # build everything, then launch the dashboard at localhost:8501
make test        # pytest: ETL idempotency, dbt compile, scoring smoke
```

`make run` = `make all` + `make dashboard`. `make all` runs the full pipeline
(extract → transform → load → dbt → train → score → a second dbt pass) without
the UI — the extra dbt pass is deliberate: `mart_revenue_analytics` reads
`marts.churn_predictions`, which only exists after `score`, so a cold build
first builds the base models with `dbt-base`, then builds only the revenue
mart with `dbt-finish` after scoring. Stages remain sequential with `make -j`.
Prefer separate steps? `make all`, then
`make dashboard` works identically.

Verified on Windows 11 / Python 3.12.14 / dbt 1.12.5 / DuckDB 1.3.2 — `make all` runs clean from an empty warehouse in under a minute. On this machine the `streamlit` console script is blocked by an Application Control policy, so the Makefile runs `python -m streamlit` instead (identical behavior).

The dashboard closes its read connections after each query. Overview polls every
five seconds and retains the last successful snapshot while a writer holds the
database. Pause auto-refresh before a full rebuild to avoid reader/writer lock
races, then resume when the pipeline finishes.

## Dashboard interactions

The dashboard is intentionally a warehouse UI, not only a chart page:

- **Overview** reads curated marts and exposes revenue economics by segment.
  Its retention-value total uses one segment family so customers are counted once.
- **Pipeline** traces one customer from the source CSV through the warehouse and
  shows the complete feature vector used by the scoring model.
- **Watchlist** filters the scored prediction mart, downloads the intervention queue,
  and drills through a selected customer from `churn_predictions` into the
  one-row-per-customer `mart_customer_360` mart.
- **Live** simulates a realtime landing stream with Indian operator dimensions
  (**Jio, Vi, Airtel, BSNL**), filters events by operator, and joins negative signals
  back to warehouse-backed customer predictions. The operator field is synthetic
  demo data; it is not present in the static IBM source snapshot.
  Provider cards, volume timeline, event mix, and customer review queue share a
  5-, 10-, or 30-minute window. The feed can show only negative signals;
  clearing the provider selection shows no events or signals. Export the queue
  as CSV. Demo priority adds four percentage points per negative event to the
  stored model probability (capped at 99%); it is not a new model prediction.
  Pausing auto-refresh freezes the snapshot while filters remain usable.
- **Warehouse** exposes the layer path (`raw → staging → core → marts → ML outputs`),
  model grain, materialization, row counts, dbt descriptions/dependencies/SQL,
  live prediction join-quality checks, and bounded read-only query templates.
  The query explorer never executes user-entered SQL.
- **Provider comparison** shows stable demo assignments for Jio, Vi, Airtel, and
  BSNL. The Overview selector filters its KPIs, charts, customer sample, and CSV;
  Watchlist and Live also support provider filters. These are synthetic customer
  groups, not measurements of actual provider performance.
- **Auto-refresh** checks Overview every five seconds and Live every three
  seconds; use the sidebar toggle to pause. The last successful read time is shown
  below Overview. Manual refresh reloads data; it does not run the pipeline.


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

The current dashboard uses a responsive neon-black grid, provider comparison,
five KPI cards, segment charts, and retention insights. Cards reflow with available
width; tables and detailed charts scroll within their cards on phones.
[Desktop preview](docs/screenshots/premium-1640.png) ·
[Mobile preview](docs/screenshots/premium-390.png).

Dashboard icons use [Iconscout Unicons](https://iconscout.com/unicons), stored
locally in `app/assets/unicons` with the IconScout Simple License. Provider
banners use styled wordmarks with demo cohort metrics and selection highlighting.

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

The test suite includes an isolated `make -j4 all` build from an empty warehouse,
dashboard navigation across all six pages, model-feature parity, revenue totals,
and operator-filtered stream reads. The build test reuses the downloaded CSV and
installed dbt packages and creates its warehouse and model in a temporary directory.
