"""Train the churn model on mart_customer_360 and save it with joblib.

Kept deliberately simple per the project brief: logistic regression on
numeric features, stratified train/test split (the dataset is a single
Feb-2020 snapshot — no event dates, so a time-based split is impossible;
stratified random split keeps churn prevalence equal on both sides).
Prints AUC + top features. Model saved to ml/models/churn_logreg.joblib.
"""
from __future__ import annotations

import json

import duckdb
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from etl.paths import DB_PATH, MODELS_DIR, ensure_dirs
from ml.features import FEATURE_COLUMNS, build_matrix, churn_flag, load_360

RANDOM_STATE = 42


def train() -> dict:
    ensure_dirs()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        df = load_360(con)
    finally:
        con.close()

    X = build_matrix(df)
    y = churn_flag(df)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ])
    pipe.fit(X_tr, y_tr)

    auc = roc_auc_score(y_te, pipe.predict_proba(X_te)[:, 1])
    n_churn = int(y.sum())
    churn_rate = float(y.mean())

    # feature importance: |coefficient| on the standardized scale
    coefs = pipe.named_steps["clf"].coef_[0]
    top = (
        pd.DataFrame({"feature": FEATURE_COLUMNS, "coef": coefs})
        .assign(abs_coef=lambda d: d["coef"].abs())
        .sort_values("abs_coef", ascending=False)
    )

    path = MODELS_DIR / "churn_logreg.joblib"
    joblib.dump(
        {"pipeline": pipe, "feature_columns": FEATURE_COLUMNS,
         "auc": auc, "train_rows": len(X_tr)},
        path,
    )
    # BI needs coefficients, not an executable sklearn object or native DLLs.
    metadata = {"feature_columns": FEATURE_COLUMNS, "coefficients": coefs.tolist(),
                "auc": float(auc), "train_rows": len(X_tr)}
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"[train] rows={len(df)}  churners={n_churn} ({churn_rate:.1%})")
    print(f"[train] holdout AUC = {auc:.4f}")
    print("[train] top features (standardized coefficient, sign = churn direction):")
    for _, r in top.head(8).iterrows():
        direction = "+" if r["coef"] > 0 else "-"
        print(f"    {direction} {r['feature']:24s} {r['coef']:+.3f}")
    print(f"[train] model saved to {path}")
    return {"auc": auc, "n_rows": len(df), "model_path": str(path)}


if __name__ == "__main__":
    train()
