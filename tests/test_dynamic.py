import pandas as pd


def test_demo_snapshot_changes_each_second_without_mutating_source():
    from app.dynamic import customer_snapshot

    source = pd.DataFrame({
        "customer_id": [f"c{i}" for i in range(500)],
        "churned": [False, True] * 250,
        "churn_probability": [.2, .8] * 250,
        "risk_band": ["low", "high"] * 250,
        "monthly_charges": [70.] * 500,
    })
    original = source.copy(deep=True)
    first = customer_snapshot(source, 100)
    second = customer_snapshot(source, 101)
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_frame_equal(first, customer_snapshot(source, 100))
    assert not first.churned.equals(second.churned)
    assert not first.monthly_charges.equals(second.monthly_charges)
    assert not first.churn_probability.equals(second.churn_probability)
    assert first.customer_id.equals(source.customer_id)
    assert first.churn_probability.between(0, 1).all()
    assert first.monthly_charges.ge(0).all()
    assert (first.loc[first.churn_probability >= .75, "risk_band"] == "high").all()
    assert first.data_source.eq("Simulated live demo").all()
