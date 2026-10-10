"""Realtime event simulator for the Live page.

A background thread that generates a stream of telecom events (payments,
failed payments, support tickets, usage alerts, plan changes, cancellation
notices) conditioned on each customer's model churn risk. Events land in
warehouse/realtime.duckdb — a separate database attached read-only by the
dashboard — so the main warehouse keeps clean single-writer semantics
(the simulator owns realtime.duckdb; nothing else writes it).

Why a simulator: the source dataset is a static Feb-2020 snapshot, but the
architecture (event stream -> landing store -> dashboard) is exactly what
a real deployment would use; swapping the generator for a Kafka topic or
webhook feed would not change anything downstream.

Risk conditioning (the teachable part): event mix is biased by model
score. High-risk customers fail payments and open tickets at higher
rates; cancellation notices only fire for modeled risk >= 0.5. Live
"new signal" = count of negative events in a rolling window per
customer (negative events push live risk up; nothing pushes it down
except time).
"""
from __future__ import annotations

import random
import threading
import time
import uuid
from dataclasses import dataclass

import duckdb
import pandas as pd

from etl.paths import WAREHOUSE_DIR
from app.providers import PROVIDERS, assign_provider

REALTIME_DB = WAREHOUSE_DIR / "realtime.duckdb"

# Events are generated about every EVENT_INTERVAL_SECONDS (jittered),
# several customers per tick.
EVENT_INTERVAL_SECONDS = 2.0
BATCH_CUSTOMERS = (6, 14)          # random range of customers touched per tick

# base rates per tick-share; negative events get a risk multiplier
EVENT_TYPES = {
    # type:        (is_negative, base_share, risk_multiplier)
    "payment":         (False, 0.40, 0.0),
    "failed_payment":  (True,  0.06, 3.5),
    "ticket":          (True,  0.08, 4.0),
    "usage_alert":     (True,  0.07, 3.0),
    "plan_change":     (False, 0.11, 0.0),
    "cancellation":    (True,  0.02, 6.0),   # gated: only risk >= 0.5 fires
}
NEGATIVE_EVENT_WINDOW_MINUTES = 10


@dataclass
class Event:
    ts: float          # unix seconds
    customer_id: str
    operator: str
    event_type: str
    detail: str


DETAILS = {
    "payment":          "auto-payment processed",
    "failed_payment":   "card declined (retry scheduled)",
    "ticket":           "billing dispute opened",
    "usage_alert":      "data cap 90% reached",
    "plan_change":      "downgraded to a lighter plan",
    "cancellation":     "requested cancellation — retention call due",
}

OPERATORS = tuple(PROVIDERS)


def _risk_multiplier(p: float, event_type: str) -> float:
    _, _, mult = EVENT_TYPES[event_type]
    return 1.0 + (p - 0.26) * mult      # 0.26 = dataset mean churn propensity


class Simulator:
    """Owns realtime.duckdb and the generator thread."""

    def __init__(self, customers: pd.DataFrame, seed: int | None = None):
        # customers: customer_id, churn_probability, monthly_charges, risk_band
        self.customers = customers
        # seed=None -> unique stream every launch; pass an int for replayability.
        self.rng = random.Random(seed if seed is not None else uuid.uuid4().int >> 96)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._events: list[Event] = []      # in-memory mirror for quick reads

    # ------------------------------------------------------------ store
    def _connect(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect(str(REALTIME_DB))
        con.sql("""
            CREATE TABLE IF NOT EXISTS events (
                ts            TIMESTAMP,
                customer_id   VARCHAR,
                operator      VARCHAR,
                event_type    VARCHAR,
                is_negative   BOOLEAN,
                detail        VARCHAR
            )
        """)
        columns = con.sql("DESCRIBE events").df()["column_name"].tolist()
        if "operator" not in columns:
            con.sql("ALTER TABLE events ADD COLUMN operator VARCHAR DEFAULT 'Jio'")
        return con

    def reset(self) -> None:
        """Drop history and restart from a clean slate (test/helper)."""
        if REALTIME_DB.exists():
            con = duckdb.connect(str(REALTIME_DB))
            con.sql("DROP TABLE IF EXISTS events")
            con.close()
        with self._lock:
            self._events.clear()

    # ---------------------------------------------------------- generate
    def _tick(self) -> list[Event]:
        n = min(self.rng.randint(*BATCH_CUSTOMERS), len(self.customers))
        if n == 0:
            return []
        sampled = self.customers.sample(n, random_state=self.rng.randint(0, 1 << 30))
        events: list[Event] = []
        for row in sampled.itertuples(index=False):
            p = float(row.churn_probability)
            # weighted choice: base shares, negative events scaled by risk
            types = list(EVENT_TYPES)
            weights = []
            for et in types:
                _, base, mult = EVENT_TYPES[et]
                if et == "cancellation" and p < 0.5:
                    weights.append(0.0)          # gate: not risky enough
                elif mult:
                    weights.append(base * _risk_multiplier(p, et))
                else:
                    weights.append(base)
            et = self.rng.choices(types, weights=weights, k=1)[0]
            operator = assign_provider(row.customer_id)
            events.append(Event(time.time(), row.customer_id, operator, et, DETAILS[et]))
        return events

    def _persist(self, events: list[Event]) -> None:
        if not events:
            return
        df = pd.DataFrame([
            {"ts": pd.Timestamp.fromtimestamp(e.ts), "customer_id": e.customer_id,
             "operator": e.operator, "event_type": e.event_type,
             "is_negative": EVENT_TYPES[e.event_type][0],
             "detail": e.detail}
            for e in events
        ])
        con = self._connect()
        try:
            con.register("new_events", df)
            con.sql("""
                INSERT INTO events (ts, customer_id, operator, event_type, is_negative, detail)
                SELECT ts, customer_id, operator, event_type, is_negative, detail
                FROM new_events
            """)
            con.unregister("new_events")
        finally:
            con.close()
        with self._lock:
            self._events.extend(events)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="churn-sim")
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._persist(self._tick())
            except duckdb.IOException:
                # another process holds realtime.duckdb (two dashboards open)
                pass
            time.sleep(EVENT_INTERVAL_SECONDS * (0.7 + 0.6 * self.rng.random()))

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    # -------------------------------------------------------------- read
    def window_events(
        self, window_minutes: int = 10, *, now: float | None = None,
        operators: list[str] | None = None,
    ) -> pd.DataFrame:
        """One consistent rolling snapshot, including neutral and negative events."""
        now = time.time() if now is None else now
        with self._lock:
            take = [e for e in self._events
                    if now - window_minutes * 60 <= e.ts <= now
                    and (operators is None or e.operator in operators)]
        return pd.DataFrame(
            [vars(e).copy() for e in take],
            columns=["ts", "customer_id", "operator", "event_type", "detail"],
        ).sort_values("ts", ascending=False, kind="stable").reset_index(drop=True)

    def recent(self, n: int = 40, operators: list[str] | None = None) -> pd.DataFrame:
        """Most recent n matching events, newest first; None selects all operators."""
        with self._lock:
            take = [e for e in self._events if operators is None or e.operator in operators]
            take = take[-n:] if n > 0 else []
        df = pd.DataFrame([
            {"ts": e.ts, "customer_id": e.customer_id,
             "operator": e.operator, "event_type": e.event_type, "detail": e.detail}
            for e in take
        ], columns=["ts", "customer_id", "operator", "event_type", "detail"])
        return df.iloc[::-1].reset_index(drop=True)

    def live_negative_counts(
        self,
        window_minutes: int = NEGATIVE_EVENT_WINDOW_MINUTES,
        operators: list[str] | tuple[str, ...] | None = None,
    ) -> pd.DataFrame:
        """customer_id -> negative events inside the rolling window."""
        cutoff = time.time() - window_minutes * 60
        with self._lock:
            take = [e for e in self._events if e.ts >= cutoff]
        if operators is not None:
            allowed = set(operators)
            take = [e for e in take if e.operator in allowed]
        rows = [
            {"customer_id": e.customer_id, "neg_events": 1}
            for e in take if EVENT_TYPES[e.event_type][0]
        ]
        if not rows:
            return pd.DataFrame(columns=["customer_id", "neg_events"])
        return (pd.DataFrame(rows)
                .groupby("customer_id", as_index=False)
                .sum(numeric_only=True))

    def customer_deltas(self) -> pd.DataFrame:
        """customer_id -> aggregate event deltas over the whole stream.

        Live overlay source: per customer, count negative events,
        positive/neutral events, and cancellations so the dashboard can
        shift live risk, flip churn state, and compute running revenue —
        without touching the warehouse snapshot.
        """
        with self._lock:
            take = list(self._events)
        if not take:
            return pd.DataFrame(columns=[
                "customer_id", "neg_events", "pos_events", "cancellations"])
        rows = []
        for e in take:
            is_neg = EVENT_TYPES[e.event_type][0]
            rows.append({
                "customer_id": e.customer_id,
                "neg_events": int(is_neg),
                "pos_events": int(e.event_type in ("payment", "plan_change")),
                "cancellations": int(e.event_type == "cancellation"),
            })
        return (pd.DataFrame(rows)
                .groupby("customer_id", as_index=False)
                .sum(numeric_only=True))


_SIM: Simulator | None = None


def get_simulator(customers: pd.DataFrame, seed: int | None = None) -> Simulator:
    """Module-level singleton so Streamlit reruns don't spawn duplicates."""
    global _SIM
    if _SIM is None:
        _SIM = Simulator(customers, seed=seed)
        _SIM.start()
    return _SIM
