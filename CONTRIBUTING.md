# Contributing to Telecom Churn Data Warehouse

Thank you for contributing to the **Telecom Churn Data Warehouse** project! We welcome code improvements, dbt model enhancements, ML feature additions, and bug fixes.

## 🛠️ Local Development Setup

1. **Fork & Clone** the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/telecom-churn-dw.git
   cd telecom-churn-dw
   ```
2. **Environment Setup**:
   ```bash
   uv sync
   uv run dbt deps --project-dir dbt --profiles-dir dbt
   ```
3. **Run Pipeline & Tests**:
   ```bash
   make all
   make test
   ```

## 📐 Guidelines

- Maintain schema layer isolation (`raw` → `staging` → `core` → `marts`).
- Ensure all new dbt models include doc headers, grain definitions, and YAML column tests.
- Run `make test` to verify ETL idempotency, model scoring, and dbt compilation before submitting a PR.

Thank you for helping elevate this data platform!
