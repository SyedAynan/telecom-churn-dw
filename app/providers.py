"""Stable demo provider assignments; the IBM snapshot has no provider field."""
import hashlib

import pandas as pd

PROVIDERS = {"Jio": "#46a3ff", "Vi": "#ffb938", "Airtel": "#ff4f79", "BSNL": "#22d3bb"}


def assign_provider(customer_id: str) -> str:
    digest = hashlib.sha256(customer_id.encode()).digest()
    return tuple(PROVIDERS)[int.from_bytes(digest[:4], "big") % len(PROVIDERS)]


def attach_providers(base: pd.DataFrame) -> pd.DataFrame:
    result = base.copy()
    result["provider"] = result.customer_id.map(assign_provider)
    # Match the mart's economics before slicing so provider totals reconcile.
    contract_rate = result.groupby("contract_label").churned.transform("mean")
    hazard = (0.5 * result.churn_probability + 0.5 * contract_rate).clip(lower=.02)
    result["addressable_revenue"] = result.monthly_charges * (1 / hazard).clip(upper=24) * result.churn_probability
    return result


def segment_summary(base: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for column, segment in [("contract_label", "contract"), ("payment_method_label", "payment_method"), ("tenure_bucket", "tenure_bucket")]:
        frame = base.groupby(column).churned.mean().reset_index(name="churn_rate")
        frames.append(frame.rename(columns={column: "segment_label"}).assign(segment_type=segment))
    return pd.concat(frames, ignore_index=True)
