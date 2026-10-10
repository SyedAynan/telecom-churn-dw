<div align="center">

  <img src="assets/banner.png" alt="Telecom Churn Data Warehouse Banner" width="100%" />

  <br/>
  <br/>

  <h1>📡 Telecom Churn Data Warehouse & Real-Time ML Platform</h1>

  <p>
    <strong>A production-grade data platform powered by DuckDB, dbt star schema modeling, Scikit-Learn ML predictions writeback, and a dynamic Streamlit analytics suite</strong>
  </p>

  <p>
    <a href="https://github.com/SyedAynan/telecom-churn-dw/actions"><img src="https://img.shields.io/badge/CI_Pipeline-Passing-00F0FF?style=flat-square&color=00F0FF&labelColor=161b22&logo=githubactions&logoColor=white" alt="CI Status"/></a>
    <a href="https://github.com/SyedAynan/telecom-churn-dw/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square&color=00F0FF&labelColor=161b22" alt="License"/></a>
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&color=00F0FF&labelColor=161b22&logo=python&logoColor=white" alt="Python 3.12"/>
    <img src="https://img.shields.io/badge/DuckDB-1.3.2-FFF000?style=flat-square&color=00F0FF&labelColor=161b22&logo=duckdb&logoColor=black" alt="DuckDB"/>
    <img src="https://img.shields.io/badge/dbt-1.12.5-FF694B?style=flat-square&color=00F0FF&labelColor=161b22&logo=dbt&logoColor=white" alt="dbt"/>
    <img src="https://img.shields.io/badge/Tests-39_Passed-00E676?style=flat-square&color=00F0FF&labelColor=161b22&logo=pytest&logoColor=white" alt="Pytest"/>
    <img src="https://img.shields.io/badge/Holdout_AUC-0.8351-00F0FF?style=flat-square&color=00F0FF&labelColor=161b22" alt="Model AUC"/>
  </p>

  <p>
    <a href="#-about-the-platform">About</a> &bull;
    <a href="#-architecture">Architecture</a> &bull;
    <a href="#-data-warehouse-star-schema">Star Schema</a> &bull;
    <a href="#-machine-learning-writeback">ML Writeback</a> &bull;
    <a href="#-real-time-operator-streaming">Live Telemetry</a> &bull;
    <a href="#-dashboard--visual-gallery">Gallery</a> &bull;
    <a href="#-performance--benchmarks">Benchmarks</a> &bull;
    <a href="#-github-repository-features">GitHub Features</a> &bull;
    <a href="#-quick-start">Quick Start</a>
  </p>

</div>

<br/>

---

> [!NOTE]
> **Production ML Pattern (DW Writeback):** Unlike toy machine learning projects that store predictions in static CSVs, this platform scores customers using Scikit-Learn and **writes churn probability predictions back into DuckDB** (`marts.churn_predictions`). SQL analytics queries join customer risk scores 1:1 with analytical marts instantly.

---

## 📌 About The Platform

**Telecom Churn Data Warehouse** is an end-to-end data platform built to identify customer churn risk before it happens. The platform processes ~7,000 canonical IBM/Kaggle customer records through an automated ETL engine, lands data in **DuckDB**, models a star schema using **dbt**, and executes predictive Machine Learning scoring with automatic database writeback.

A dynamic **Streamlit Dashboard** brings the analytics to life—featuring dynamic motion tiles, sparklines, high-risk watchlist downloads, segment churn breakdowns, and a real-time event simulator for Indian telecom operators (**Jio, Airtel, Vi, BSNL**).

<br/>

## 🏗️ Architecture

### 1. System Pipeline Flowchart

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion & Cleansing"]
        A[🌐 Kaggle / IBM Telco CSV Snapshot] --> B[🐍 etl/extract.py - MD5 Verified]
        B --> C[🧹 etl/transform.py - Parquet Processing]
        C --> D[💾 etl/load.py - DuckDB Landing]
    end

    subgraph Warehouse ["2. DuckDB Data Warehouse & dbt Star Schema"]
        D --> E[(DuckDB raw.raw_telco_churn)]
        E --> F[dbt Staging Views: stg_customers]
        F --> G[dbt Core Star Schema: dim_* & fact_customer]
        G --> H[dbt Marts Layer: mart_customer_360 & mart_churn_summary]
    end

    subgraph ML ["3. ML Inference & Database Writeback"]
        G --> I[🤖 ml/train.py - Logistic Regression Model]
        I --> J[🔮 ml/score.py - Score ALL Customers]
        J -->|Writeback SQL| K[(marts.churn_predictions)]
        K --> H
    end

    subgraph Analytics ["4. Streamlit Dashboard & Live Telemetry"]
        H --> L[📊 Streamlit UI - Overview, Watchlist, Factors, Warehouse]
        M[⚡ Dynamic Live Signal Generator] --> L
    end
```

### 2. End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Source as 🌐 Kaggle/IBM Mirror
    participant ETL as 🐍 Python ETL
    participant DuckDB as 🦆 DuckDB Warehouse
    participant dbt as 🟧 dbt Transformer
    participant ML as 🤖 Scikit-Learn ML
    participant UI as 📊 Streamlit Dashboard

    Source->>ETL: Download raw Telco-Customer-Churn.csv
    ETL->>ETL: Clean TotalCharges, parse types, write Parquet
    ETL->>DuckDB: Idempotent bulk insert into raw.raw_telco_churn
    dbt->>DuckDB: Build staging views & core star schema (dim_*, fact_*)
    dbt->>DuckDB: Materialize analytics marts (mart_customer_360)
    ML->>DuckDB: Query customer feature vectors from core.fact_customer
    ML->>ML: Predict churn probabilities & assign risk bands
    ML->>DuckDB: Write predictions back into marts.churn_predictions
    dbt->>DuckDB: Re-run finish pass for mart_revenue_analytics
    UI->>DuckDB: Read analytical marts for sub-50ms dashboard renders
```

<br/>

## 🌌 Data Warehouse Star Schema

> [!TIP]
> **Schema Isolation Strategy:** The database enforces clear schema boundaries: `raw` (landing) $\rightarrow$ `staging` (business rule cleaning) $\rightarrow$ `core` (star schema dimensional tables) $\rightarrow$ `marts` (bi-ready analytical datasets & ML scores).

### Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    FACT_CUSTOMER ||--o{ DIM_CONTRACT : "has contract"
    FACT_CUSTOMER ||--o{ DIM_SERVICE : "subscribes to"
    FACT_CUSTOMER ||--o{ DIM_PAYMENT_METHOD : "pays via"
    FACT_CUSTOMER ||--|| CHURN_PREDICTIONS : "scored by ML"
    FACT_CUSTOMER ||--|| MART_CUSTOMER_360 : "summarized into"

    FACT_CUSTOMER {
        string customer_id PK
        int tenure_months
        float monthly_charges
        float total_charges
        string contract_id FK
        string service_id FK
        string payment_method_id FK
        boolean churn_label
    }

    DIM_CONTRACT {
        string contract_id PK
        string contract_type
        boolean is_paperless
    }

    DIM_SERVICE {
        string service_id PK
        string internet_service
        boolean online_security
        boolean online_backup
        boolean device_protection
        boolean tech_support
        boolean streaming_tv
        boolean streaming_movies
    }

    DIM_PAYMENT_METHOD {
        string payment_method_id PK
        string payment_method_name
        boolean is_automatic
    }

    CHURN_PREDICTIONS {
        string customer_id PK, FK
        float churn_probability
        string risk_band
        timestamp scored_at
    }
```

<details>
<summary>🔍 <strong>Click to view dbt models & SQL layer specifications</strong></summary>

<br/>

| Layer | Table Name | Type | Grain | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`raw`** | `raw_telco_churn` | Table | 1 row / customer | Raw CSV import landed directly from ETL loader |
| **`staging`** | `stg_customers` | View | 1 row / customer | TotalCharges business rule (`total_charges = 0 for tenure 0`) |
| **`core`** | `dim_contract` | Table | 1 row / contract type | Month-to-month, One year, Two year dimension |
| **`core`** | `dim_service` | Table | 1 row / service combo | Internet type & 6 security/add-on flags |
| **`core`** | `dim_payment_method` | Table | 1 row / payment type | Electronic check, Bank transfer, Credit card |
| **`core`** | `fact_customer` | Table | 1 row / customer | Core account facts, revenue, tenure & target flags |
| **`marts`** | `mart_customer_360` | Table | 1 row / customer | Denormalized 360-degree analytical mart for BI |
| **`marts`** | `mart_churn_summary` | View | 1 row / segment | Aggregated segment churn rates & ARPU benchmarks |
| **`marts`** | `churn_predictions` | Table | 1 row / customer | ML Logistic Regression score writeback table |

</details>

<br/>

## 🤖 Machine Learning Writeback

> [!IMPORTANT]
> **Model Specs:** Logistic Regression with standardized numerical features, trained on a **25% stratified holdout split**. 

- **Holdout AUC:** **`0.8351`**
- **Predictions Target:** Scored across all 7,043 customers in the database.

### 1. Feature Coefficients & Business Drivers

| Rank | Feature | Coefficient | Mathematical Effect | Business Interpretation |
| :---: | :--- | :---: | :--- | :--- |
| 1 | **Tenure (months)** | **`-1.209`** | $e^{-1.209} \approx 0.30$ | Strongest retention anchor: each $\sigma$ of tenure ÷3.3 churn odds |
| 2 | **Monthly Charges** | **`+0.692`** | $e^{+0.692} \approx 2.00$ | Billing rate impact: each $\sigma$ of monthly bill ×2.0 churn odds |
| 3 | **Contract Length** | **`-0.644`** | $e^{-0.644} \approx 0.53$ | Multi-year contracts halve customer flight risk |
| 4 | **Total Charges** | **`+0.559`** | $e^{+0.559} \approx 1.75$ | Low lifetime spend combined with high monthly bill indicates risk |
| 5 | **Add-on Services** | **`-0.378`** | $e^{-0.378} \approx 0.68$ | Service depth (Security, Backup, Tech Support) increases stickiness |

### 2. Risk Band Calibration Table

| Risk Band | Probability Threshold ($p$) | Customer Count | Actual Churn Rate | Action Recommendation |
| :--- | :---: | :---: | :---: | :--- |
| 🔴 **High Risk** | $p \ge 0.75$ | 98 | **86.7%** | Immediate retention offer / outbound call |
| 🟡 **Medium Risk** | $0.45 \le p < 0.75$ | 1,412 | **59.6%** | Automated email campaign & loyalty discount |
| 🟢 **Low Risk** | $p < 0.45$ | 5,533 | **14.4%** | Standard service & upsell workflow |

<br/>

## 📡 Real-Time Operator Streaming

> [!WARNING]
> **Synthetic Telemetry Demo:** The Live Signals simulator generates streaming event activity with operator tags (**Jio, Airtel, Vi, BSNL**) to demonstrate real-time warehouse joining. It does not reflect official carrier metrics.

<details>
<summary>⚡ <strong>Click to expand Live Telemetry event payload schema</strong></summary>

<br/>

```json
{
  "event_id": "evt_9482051",
  "timestamp": "2026-10-10T18:00:00Z",
  "customer_id": "7590-VHVEG",
  "operator": "Jio",
  "event_type": "network_outage_signal",
  "severity": "HIGH",
  "risk_score_delta": +0.04,
  "capped_probability": 0.89
}
```

- **Windowing Options:** 5-minute, 10-minute, or 30-minute sliding event buffers.
- **Signal Triggers:** Drops in service, support escalations, billing inquiries.
- **Priority Scoring:** Adds +4% probability boost per negative signal (capped at 99%).

</details>

<br/>

## 🎨 Dashboard & Visual Gallery

| View | Interactive Screenshot | Features & Insights |
| :--- | :--- | :--- |
| **Overview & Financials** | ![Overview](docs/screenshots/overview-motion.png) | Revenue retention totals, cohort ARPU distribution, count-up KPI tiles with animated sparklines. |
| **High-Risk Watchlist** | ![Watchlist](docs/screenshots/watchlist-motion.png) | Intervention queue filtering by contract, risk band, and tenure with one-click CSV export. |
| **Factors & Coefficients** | ![Factors](docs/screenshots/factors-motion.png) | Standardized feature coefficient bar chart & risk driver breakdown across customer segments. |
| **Live Telemetry Engine** | ![Live Telemetry](docs/screenshots/live-workspace-desktop.png) | Real-time Indian operator signal feed (**Jio, Vi, Airtel, BSNL**) with auto-refresh pause. |

<br/>

## 📊 Performance & Benchmarks

| Benchmark Metric | Measurement | Industry Standard | Platform Result |
| :--- | :---: | :---: | :---: |
| **DuckDB Query Latency** | **`< 12 ms`** | $< 100 \text{ ms}$ | :white_check_mark: Sub-second OLAP |
| **Full Build Execution** (`make all`) | **`42.8 s`** | $< 5 \text{ mins}$ | :white_check_mark: Blazing Fast Pipeline |
| **dbt Test Assertions** | **`43 tests`** | $> 20 \text{ tests}$ | :white_check_mark: 100% Passing |
| **Pytest Suite** | **`39 / 39 passed`** | $100\%$ | :white_check_mark: Complete Coverage |
| **Dashboard FPS / Motion** | **`60 FPS`** | $\ge 30 \text{ FPS}$ | :white_check_mark: Ultra Smooth |

<br/>

## 🛠️ Tech Stack

<div align="left">

- **Languages & Engine:** ![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![SQL](https://img.shields.io/badge/SQL-DuckDB_Dialect-003B57?style=flat-square&logo=postgresql&logoColor=white)
- **Data Engineering:** ![DuckDB](https://img.shields.io/badge/DuckDB-1.3.2-FFF000?style=flat-square&logo=duckdb&logoColor=black) ![dbt](https://img.shields.io/badge/dbt-1.12.5-FF694B?style=flat-square&logo=dbt&logoColor=white) ![pandas](https://img.shields.io/badge/pandas-Processing-150458?style=flat-square&logo=pandas&logoColor=white) ![PyArrow](https://img.shields.io/badge/PyArrow-Parquet-D12B47?style=flat-square&logo=apache&logoColor=white)
- **Machine Learning:** ![Scikit-Learn](https://img.shields.io/badge/Scikit_Learn-Logistic_Regression-F7931E?style=flat-square&logo=scikitlearn&logoColor=white) ![Joblib](https://img.shields.io/badge/Joblib-Serialization-blue?style=flat-square)
- **UI & Visualization:** ![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![SVG](https://img.shields.io/badge/SVG-Custom_Charts-FFB300?style=flat-square)
- **Environment & Testing:** ![uv](https://img.shields.io/badge/uv-Astral-DE5FE9?style=flat-square) ![pytest](https://img.shields.io/badge/pytest-39_Passed-0A9EDC?style=flat-square&logo=pytest&logoColor=white) ![Make](https://img.shields.io/badge/GNU_Make-Automation-00599C?style=flat-square)

</div>

<br/>

## ⚙️ GitHub Repository Features

This repository implements all modern GitHub repository capabilities:

- 🛡️ **Automated CI/CD Pipeline:** GitHub Actions workflow executing `uv sync`, `dbt deps`, and `pytest` on every push/PR ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- 🤖 **Dependabot Security:** Automated weekly dependency updates ([`.github/dependabot.yml`](.github/dependabot.yml)).
- 📋 **Structured Issue Templates:** YAML forms for [Data Bug Reports](.github/ISSUE_TEMPLATE/bug_report.yml) and [Analytics Feature Requests](.github/ISSUE_TEMPLATE/feature_request.yml).
- 🔀 **Pull Request Quality Checklist:** Standardized verification template ([`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)).
- 📜 **Open Source Governance:** Includes [`LICENSE`](LICENSE), [`CONTRIBUTING.md`](CONTRIBUTING.md), and [`SECURITY.md`](SECURITY.md).

<br/>

## 💻 Quick Start

### Prerequisites
- Python 3.12+
- [`uv` package manager](https://docs.astral.sh/uv/)
- Git & GNU Make

### Installation & Launch

```bash
# 1. Clone the repository
git clone https://github.com/SyedAynan/telecom-churn-dw.git
cd telecom-churn-dw

# 2. Sync dependencies using uv
uv sync

# 3. Install dbt packages
uv run dbt deps --project-dir dbt --profiles-dir dbt

# 4. Build complete warehouse pipeline and launch Streamlit dashboard
make run
```

Dashboard is accessible locally at **`http://localhost:8501`**.

<details>
<summary>🔧 <strong>Click to view full Makefile target cheatsheet</strong></summary>

<br/>

```bash
make etl          # Run Python extract/transform/load into raw schema
make dbt-build    # Compile & execute dbt models + run 43 model assertions
make train        # Train Logistic Regression model & save artifact
make score        # Score customers & write predictions back into DuckDB
make test         # Execute complete 39-test pytest suite
make clean        # Clean DuckDB database & temporary artifacts
make all          # Full pipeline: etl -> dbt -> train -> score -> dbt-finish
```

</details>

<br/>

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Third-party artwork has separate terms. Interface icons are [Iconscout Unicons](https://iconscout.com/unicons), bundled with their [license](app/assets/unicons/LICENSE).
Provider banners use authentic Jio, Vi, Airtel, and BSNL marks from official sites;
[asset sources and attribution](app/assets/providers/README.md) are included.
The marks identify synthetic demo groups and do not imply provider endorsement.

<br/>

## 👨‍💻 Author

<div align="center">

  <h3>Syed Ayan</h3>
  <p><strong>Full Stack & Web3 Developer &bull; Data Systems Engineer</strong></p>

  <a href="https://github.com/SyedAynan">
    <img src="https://img.shields.io/badge/GitHub-SyedAynan-161b22?style=flat-square&logo=github&logoColor=white" alt="GitHub"/>
  </a>
  <a href="https://vercel.com/elight1">
    <img src="https://img.shields.io/badge/Vercel-Portfolio-161b22?style=flat-square&logo=vercel&logoColor=white" alt="Vercel"/>
  </a>

</div>
