from pathlib import Path


def test_factors_profile_falls_back_when_sklearn_native_dll_is_blocked(monkeypatch):
    import builtins
    from app.model_insights import load_profile, FEATURE_COEFFICIENTS

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "joblib":
            raise ImportError("DLL load failed while importing _isfinite")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    names, values, status = load_profile(Path("missing.joblib"))
    assert names == list(FEATURE_COEFFICIENTS)
    assert len(values) == len(names)
    assert "fallback" in status.lower() or "unavailable" in status.lower()


def test_factors_reads_exported_metadata_without_loading_native_model(tmp_path, monkeypatch):
    import json
    import joblib
    from app.model_insights import load_profile

    def blocked(*args, **kwargs):
        raise AssertionError("Dashboard must never deserialize a model")

    monkeypatch.setattr(joblib, "load", blocked)
    model = tmp_path / "churn_logreg.joblib"
    model.write_bytes(b"model artifact is not read by the dashboard")
    metadata = model.with_suffix(".json")
    metadata.write_text(json.dumps({"feature_columns": ["tenure_months"], "coefficients": [-1.25]}))
    assert load_profile(model) == (["tenure_months"], [-1.25], "Exported trained model coefficients")
    metadata.write_text("{incomplete")
    assert "unavailable" in load_profile(model)[2]
