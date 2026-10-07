"""dbt models compile (parse-level check; no warehouse mutation here)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt"


def test_dbt_models_compile():
    proc = subprocess.run(
        ["dbt", "compile",
         "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0 and "Failed to spawn" in (proc.stderr or ""):
        pytest.skip("dbt CLI script not spawnable in this environment")
    assert proc.returncode == 0, f"dbt compile failed:\n{proc.stdout[-2000:]}"
