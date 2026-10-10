import pandas as pd

from app.simulator import Event, Simulator


def test_window_events_includes_all_event_types_and_respects_time_and_provider():
    sim = Simulator(pd.DataFrame(), seed=1)
    sim._events = [
        Event(399, "old", "Jio", "payment", "old"),
        Event(400, "a", "Jio", "payment", "paid"),
        Event(900, "b", "Vi", "ticket", "help"),
        Event(999, "a", "Jio", "failed_payment", "retry"),
        Event(1001, "future", "Jio", "payment", "future"),
    ]
    frame = sim.window_events(window_minutes=10, now=1000)
    assert frame.customer_id.tolist() == ["a", "b", "a"]
    assert sim.window_events(window_minutes=10, now=1000, operators=["Jio"]).event_type.tolist() == ["failed_payment", "payment"]
    assert sim.window_events(window_minutes=10, now=1000, operators=[]).empty


def test_signal_queue_counts_negative_events_and_ranks_demo_priority():
    from app.live import review_queue

    base = pd.DataFrame({"customer_id": ["a", "b", "c"], "churn_probability": [.71, .98, .2]})
    events = pd.DataFrame([
        vars(Event(4, "a", "Jio", "ticket", "help")),
        vars(Event(3, "b", "Vi", "failed_payment", "retry")),
        vars(Event(2, "c", "BSNL", "payment", "paid")),
        vars(Event(1, "a", "Jio", "payment", "paid")),
    ])
    queue = review_queue(events, base)
    assert queue.customer_id.tolist() == ["b", "a"]
    assert queue.neg_events.tolist() == [1, 1]
    assert queue.priority_score.tolist() == [.99, .75]
    assert queue.event_type.tolist() == ["failed_payment", "ticket"]
    assert review_queue(events.iloc[:0], base).empty
