.DEFAULT_GOAL := help

PY := uv run python -m
DBT := uv run dbt

# These stages share artifacts and must stay ordered, including with make -j.
.NOTPARALLEL:

.PHONY: help extract transform load etl dbt-base dbt-build dbt-finish dbt-test train score dashboard run test all clean

help:
	@echo "telecom-churn-dw — make targets"
	@echo "  make run         one command: build everything, then launch the dashboard"
	@echo "  make etl         extract + transform + load raw data into DuckDB"
	@echo "  make dbt-build   build dbt models (staging -> core -> marts)"
	@echo "  make dbt-finish  second dbt pass — builds marts fed by churn_predictions"
	@echo "  make dbt-test    run dbt tests"
	@echo "  make train       train logistic regression, save model"
	@echo "  make score       score all customers, write marts.churn_predictions"
	@echo "  make dashboard   launch Streamlit dashboard (localhost:8501)"
	@echo "  make test        run pytest suite"
	@echo "  make all         full build: etl + dbt + train + score + dbt-finish (no UI)"
	@echo "  make clean       remove warehouse + dbt artifacts"

extract:
	$(PY) etl.extract

transform:
	$(PY) etl.transform

load:
	$(PY) etl.load

etl: extract transform load

dbt-build:
	$(DBT) build --project-dir dbt --profiles-dir dbt

# The revenue mart reads predictions, which do not exist until scoring.
dbt-base:
	$(DBT) build --project-dir dbt --profiles-dir dbt --exclude mart_revenue_analytics

dbt-finish:
	$(DBT) build --project-dir dbt --profiles-dir dbt --select mart_revenue_analytics

dbt-test:
	$(DBT) test --project-dir dbt --profiles-dir dbt

train:
	$(PY) ml.train

score:
	$(PY) ml.score

dashboard:
	SMTP= SMTP_EMAIL= uv run python -m streamlit run app/dashboard.py --server.headless=true

# `all` is the full pipeline WITHOUT the UI. dbt runs twice on purpose:
# mart_revenue_analytics reads marts.churn_predictions (written by `score`),
# which only exists after train+score — the "predictions live in the
# warehouse" pattern means a cold build needs a finishing pass.
all: etl dbt-base train score dbt-finish

run: all dashboard

test:
	uv run python -m pytest -v

clean:
	rm -rf warehouse/*.duckdb dbt/target dbt/logs
