"""Build the published pipeline in isolation, starting without a warehouse."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb

from etl.paths import PROJECT_ROOT, RAW_CSV_PATH


def test_make_all_builds_from_empty_warehouse(tmp_path: Path):
    for directory in ("etl", "ml", "dbt"):
        shutil.copytree(
            PROJECT_ROOT / directory, tmp_path / directory,
            ignore=shutil.ignore_patterns(
                "__pycache__", "target", "logs", "*.joblib", "*.json",
            ),
        )
    shutil.copy2(PROJECT_ROOT / "Makefile", tmp_path / "Makefile")
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    shutil.copy2(RAW_CSV_PATH, raw_dir / RAW_CSV_PATH.name)

    result = subprocess.run(
        ["make", "-j4", "all", f'PY="{sys.executable}" -m',
         f'DBT="{sys.executable}" -m dbt.cli.main'],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=300,
    )
    assert result.returncode == 0, result.stdout[-6000:] + result.stderr[-2000:]
    with duckdb.connect(str(tmp_path / "warehouse" / "telecom_churn.duckdb"), read_only=True) as con:
        assert con.sql("SELECT COUNT(*) FROM marts.churn_predictions").fetchone()[0] == 7043
        segments = con.sql("""
            SELECT segment_type, SUM(n_customers), COUNT(addressable_revenue)
            FROM marts.mart_revenue_analytics GROUP BY segment_type ORDER BY segment_type
        """).fetchall()
    assert segments == [("contract", 7043, 3), ("risk_band", 7043, 3)]
