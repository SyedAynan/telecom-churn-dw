.DEFAULT_GOAL := help

PY := uv run python -m
DBT := uv run dbt

.PHONY: help extract transform load etl dbt-build dbt-test train score dashboard test all clean

help:
	@echo "telecom-churn-dw — make targets"
	@echo "  make etl         extract + transform + load raw data into DuckDB"
	@echo "  make dbt-build   build dbt models (staging -> core -> marts)"
	@echo "  make dbt-test    run dbt tests"
	@echo "  make train       train logistic regression, save model"
	@echo "  make score       score all customers, write marts.churn_predictions"
	@echo "  make dashboard   launch Streamlit dashboard (localhost:8501)"
	@echo "  make test        run pytest suite"
	@echo "  make all         etl + dbt-build + train + score"
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

dbt-test:
	$(DBT) test --project-dir dbt --profiles-dir dbt

train:
	$(PY) ml.train

score:
	$(PY) ml.score

dashboard:
	SMTP= SMTP_EMAIL= uv run python -m streamlit run app/dashboard.py --server.headless=true

test:
	uv run pytest -v

all: etl dbt-build train score

clean:
	rm -rf warehouse/*.duckdb dbt/target dbt/logs
