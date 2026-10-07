"""Central path constants for the telecom-churn-dw project.

Every module resolves paths through here so `uv run python -m etl.extract`
works from any working directory (Makefile, pytest, dbt hooks alike).
"""
from __future__ import annotations

from pathlib import Path

# project root = two levels above this file (etl/paths.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
WAREHOUSE_DIR = PROJECT_ROOT / "warehouse"
DB_PATH = WAREHOUSE_DIR / "telecom_churn.duckdb"
MODELS_DIR = PROJECT_ROOT / "ml" / "models"

# Canonical Kaggle name for the file, whatever its provenance.
RAW_CSV_NAME = "Telco-Customer-Churn.csv"
RAW_CSV_PATH = DATA_RAW / RAW_CSV_NAME
CLEAN_PARQUET_PATH = DATA_PROCESSED / "telco_clean.parquet"

# Verified byte-identical mirror of the Kaggle dataset (IBM's own copy).
SOURCE_URL = (
    "https://raw.githubusercontent.com/IBM/"
    "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)
EXPECTED_MD5 = "3b0bfab28a8101b4e4fdd08025a5c235"


def ensure_dirs() -> None:
    """Create the data/warehouse directories if they don't exist yet."""
    for d in (DATA_RAW, DATA_PROCESSED, WAREHOUSE_DIR, MODELS_DIR):
        d.mkdir(parents=True, exist_ok=True)
