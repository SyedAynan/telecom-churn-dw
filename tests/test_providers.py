import pandas as pd


def test_provider_assignment_is_stable_and_includes_all_four_networks():
    from app.providers import PROVIDERS, assign_provider

    ids = [f"customer-{i}" for i in range(100)]
    assigned = {cid: assign_provider(cid) for cid in ids}
    assert set(assigned.values()) == set(PROVIDERS) == {"Jio", "Vi", "Airtel", "BSNL"}
    assert {cid: assign_provider(cid) for cid in reversed(ids)} == assigned


def test_live_events_keep_the_same_provider_as_customer_profiles():
    from app.providers import assign_provider
    from app.simulator import Simulator

    customers = pd.DataFrame({"customer_id": [f"customer-{i}" for i in range(100)], "churn_probability": [.8] * 100})
    sim = Simulator(customers, seed=4)
    events = [event for _ in range(4) for event in sim._tick()]
    assert events
    assert all(event.operator == assign_provider(event.customer_id) for event in events)
