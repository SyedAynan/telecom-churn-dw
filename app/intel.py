"""Deterministic synthetic dimensions for the demo UI.

The IBM/Kaggle source has no operator, region, or billing dates. To power
the enterprise analytics views we assign each customer an operator, Indian
circle, and billing month deterministically — a fixed seed makes it
reproducible, and every view labels these as SYNTHETIC. Real metrics
(churn %, revenue, model output) are untouched.
"""
from __future__ import annotations

import hashlib

import pandas as pd

# operator_key, name, weight, brand colour, market share hint
OPERATORS = [
    ("airtel", "Airtel", 0.45, "#e40000", "~33%"),
    ("jio",    "Jio",    0.35, "#1e4ed8", "~36%"),
    ("vi",     "Vi",     0.20, "#f5d000", "~15%"),
]

REGIONS = [
    ("delhi", "Delhi NCR", "North"),
    ("mumbai", "Mumbai", "West"),
    ("kolkata", "Kolkata", "East"),
    ("bangalore", "Bangalore", "South"),
    ("chennai", "Chennai", "South"),
    ("hyderabad", "Hyderabad", "South"),
    ("pune", "Pune", "West"),
    ("ahmedabad", "Ahmedabad", "West"),
    ("jaipur", "Jaipur", "North"),
    ("lucknow", "Lucknow", "North"),
]

ZONES = {k: z for k, _, z in REGIONS}
OP_NAMES = {k: n for k, n, *_ in OPERATORS}
OP_COLOURS = {k: c for k, _, _, c, _ in OPERATORS}
REGION_NAMES = {k: n for k, n, _ in REGIONS}


def _stable(text: str, salt: str = "") -> int:
    return int(hashlib.md5(f"{salt}{text}".encode()).hexdigest(), 16)


def assign(customer_ids: pd.Series) -> pd.DataFrame:
    """customer_id -> (operator_key, region_key), deterministic + weighted."""
    import numpy as np
    keys = [k for k, *_ in OPERATORS]
    weights = np.array([w for *_, w, _, _ in OPERATORS], dtype=float)
    weights /= weights.sum()
    cum = np.cumsum(weights)

    def op(cid: str) -> str:
        u = (_stable(cid, "op") % 10000) / 10000.0
        return keys[int(np.searchsorted(cum, u))]

    def reg(cid: str) -> str:
        return REGIONS[_stable(cid, "reg") % len(REGIONS)][0]

    return pd.DataFrame({
        "customer_id": customer_ids,
        "operator_key": [op(c) for c in customer_ids],
        "region_key": [reg(c) for c in customer_ids],
    })


def operator_of_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add operator_name/region_name display columns to a scored frame."""
    m = assign(df["customer_id"]).set_index("customer_id")
    df = df.copy()
    df["operator_key"] = df.customer_id.map(m.operator_key)
    df["operator"] = df.operator_key.map(OP_NAMES)
    df["region_key"] = df.customer_id.map(m.region_key)
    df["region"] = df.region_key.map(REGION_NAMES)
    df["zone"] = df.region_key.map(ZONES)
    return df
