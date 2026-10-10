"""Bounded, reproducible demo scenarios; never writes to the warehouse."""
import time
import numpy as np
import pandas as pd


def current_second() -> int:
    return int(time.time())


def customer_snapshot(base: pd.DataFrame, second: int) -> pd.DataFrame:
    """All views of the same second share one scenario, independent of row order.

    Accelerated demo: resample 3% of historical outcomes, adjust monthly bills
    by up to 3%, and vary scores by up to 4 percentage points. These values
    illustrate dashboard changes; they are neither real events nor ML inference.
    """
    result = base.copy()
    keys = pd.util.hash_pandas_object(result.customer_id, index=False).to_numpy(dtype="uint64")
    # Sort before drawing so row order cannot change the shared scenario.
    rng = np.random.default_rng(second)
    order = np.argsort(keys)
    draws = np.empty((len(result), 3))
    draws[order] = rng.random((len(result), 3))
    result["churned"] = result.churned.astype(bool) ^ (draws[:, 0] < .03)
    result["monthly_charges"] = (result.monthly_charges * (1 + (draws[:, 1] - .5) * .06)).round(2)
    result["churn_probability"] = (result.churn_probability + (draws[:, 2] - .5) * .08).clip(0, .99)
    result["risk_band"] = np.select([result.churn_probability >= .75, result.churn_probability >= .5], ["high", "medium"], default="low")
    result["data_source"] = "Simulated live demo"
    result["simulation_second"] = second
    return result
