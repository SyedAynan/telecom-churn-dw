"""Safe model metadata for the Factors page.

Loading a joblib pipeline imports scikit-learn native extensions. Some managed
Windows installations block those DLLs even though the warehouse predictions
and dashboard can run normally. The Factors page uses this small fallback so a
blocked optional visualization cannot take down the application.
"""
from __future__ import annotations

import json
from pathlib import Path

FEATURE_LABELS = {
    "tenure_months": "Tenure (months)", "monthly_charges": "Monthly charges",
    "total_charges": "Total charges", "is_female": "Female",
    "is_senior": "Senior citizen", "has_partner": "Has partner",
    "has_dependents": "Has dependents", "paperless_billing": "Paperless billing",
    "contract_months": "Contract length", "is_automatic_payment": "Automatic payment",
    "n_internet": "Internet service", "n_addons": "Add-on services",
}

# Rounded coefficients documented in README.md; only these five are recorded.
# They are a reference profile, not a substitute for freshly exported metadata.
FEATURE_COEFFICIENTS = {
    "tenure_months": -1.209, "monthly_charges": 0.692, "contract_months": -0.644,
    "total_charges": 0.559, "n_addons": -0.378,
}


def fallback_profile() -> tuple[list[str], list[float], str]:
    names = list(FEATURE_COEFFICIENTS)
    return names, [FEATURE_COEFFICIENTS[name] for name in names], "README reference: five rounded coefficients; current model metadata unavailable"


def load_profile(model_path: Path) -> tuple[list[str], list[float], str]:
    """Read plain JSON only. The dashboard never unpickles or imports sklearn."""
    try:
        metadata_path = model_path.with_suffix(".json")
        if metadata_path.stat().st_mtime_ns < model_path.stat().st_mtime_ns:
            return fallback_profile()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        names, values = metadata["feature_columns"], metadata["coefficients"]
        if not names or len(names) != len(values):
            return fallback_profile()
        return names, [float(v) for v in values], "Exported trained model coefficients"
    except (OSError, ValueError, KeyError, TypeError):
        return fallback_profile()
