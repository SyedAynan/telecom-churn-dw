"""Rolling demo signals and responsive Live workspace."""
from __future__ import annotations

import html
from datetime import datetime

import pandas as pd

from app.assets import icon, svg_image
from app.providers import PROVIDERS
from app.simulator import EVENT_TYPES

LABELS = {"payment": "Payment received", "failed_payment": "Payment failed",
          "ticket": "Support ticket", "usage_alert": "Usage alert",
          "plan_change": "Plan changed", "cancellation": "Cancellation request"}
ACTIONS = {"failed_payment": "Review payment retry", "ticket": "Review billing dispute",
           "usage_alert": "Review data allowance", "cancellation": "Prioritize retention contact"}
NEGATIVE = {name for name, config in EVENT_TYPES.items() if config[0]}


def review_queue(events: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    negative = events[events.event_type.isin(NEGATIVE)].sort_values("ts", ascending=False)
    counts = negative.groupby("customer_id").size().rename("neg_events")
    queue = negative.drop_duplicates("customer_id").merge(counts, on="customer_id")
    queue = queue.merge(base[["customer_id", "churn_probability"]], on="customer_id")
    # An inspection heuristic, not a freshly trained model probability.
    queue["priority_score"] = (queue.churn_probability + .04 * queue.neg_events).clip(upper=.99)
    queue["suggested_action"] = queue.event_type.map(ACTIONS)
    return queue.sort_values(["priority_score", "ts"], ascending=False).reset_index(drop=True)


def timeline(events: pd.DataFrame, now: float, minutes: int) -> str:
    bins = 30
    width = minutes * 60 / bins
    positions = ((events.ts - (now - minutes * 60)) / width).astype(int).clip(0, bins - 1)
    totals = positions.value_counts()
    negatives = positions[events.event_type.isin(NEGATIVE)].value_counts()
    peak = max(int(totals.max()) if len(totals) else 0, 1)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 190" font-family="Arial,sans-serif" font-size="11">'
    for i in range(3):
        y = 145 - i * 60
        svg += f'<path d="M30 {y}H650" stroke="#242429"/><text x="22" y="{y+4}" text-anchor="end" fill="#9292a3">{peak*i/2:g}</text>'
    for i in range(bins):
        total, neg = int(totals.get(i, 0)), int(negatives.get(i, 0))
        height, neg_height = total / peak * 120, neg / peak * 120
        x = 36 + i * 20.3
        svg += f'<rect x="{x:.1f}" y="{145-height:.1f}" width="12" height="{height:.1f}" rx="2" fill="#00d9ff"/><rect x="{x:.1f}" y="{145-neg_height:.1f}" width="12" height="{neg_height:.1f}" rx="2" fill="#ff537f"/>'
    for x, timestamp, anchor in [(30, now-minutes*60, "start"), (340, now-minutes*30, "middle"), (650, now, "end")]:
        svg += f'<text x="{x}" y="177" text-anchor="{anchor}" fill="#9292a3">{datetime.fromtimestamp(timestamp):%H:%M:%S}</text>'
    return svg_image(svg + '</svg>', css_class="live-timeline", label="Event counts by time, cyan neutral and pink negative")


def dashboard(events: pd.DataFrame, queue: pd.DataFrame, *, now: float, minutes: int,
              providers: list[str], feed_mode: str, paused: bool) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    negative = events[events.event_type.isin(NEGATIVE)]
    latest_age = max(0, int(now - events.ts.max())) if len(events) else None
    freshness = f"Latest event {latest_age}s ago" if latest_age is not None else "Awaiting events"
    state = "Snapshot paused" if paused else ("Feed quiet" if latest_age is None or latest_age > 15 else "Receiving events")
    kpis = [("Window events", f"{len(events):,}", f"Last {minutes} minutes", "signal", "#00d9ff"),
            ("Negative signals", f"{len(negative):,}", f"{len(negative)/len(events):.0%} of events" if len(events) else "No events yet", "user-minus", "#ff537f"),
            ("Customers affected", f"{len(queue):,}", "With a negative signal", "users-alt", "#ffb938"),
            ("Priority customers", f"{int((queue.priority_score >= .75).sum()):,}", "Demo priority score >= 75%", "shield-check", "#22d3bb")]
    tiles = ''.join(f'<article class="live-kpi" style="--accent:{color}"><div class="live-kpi-label">{icon(asset, color)}{label}</div><strong>{value}</strong><small>{note}</small></article>' for label, value, note, asset, color in kpis)
    cards = []
    for name, color in PROVIDERS.items():
        group = events[events.operator == name]
        count = int(group.event_type.isin(NEGATIVE).sum())
        active = name in providers
        cards.append(f'<article class="live-provider {"" if active else "muted"}" style="--provider:{color}"><div class="live-provider-top"><span class="live-wordmark brand-{name.lower()}">{name}</span><span>{"IN WINDOW" if active else "FILTERED OUT"}</span></div><div class="live-provider-values"><strong>{len(group):,}<small>events</small></strong><span>{count:,}<small>negative signals</small></span></div></article>')
    mix = ''
    for name, label in LABELS.items():
        count = int((events.event_type == name).sum())
        share = count / len(events) * 100 if len(events) else 0
        color = "#ff537f" if name in NEGATIVE else "#00d9ff"
        mix += f'<div class="live-mix-row"><span>{label}</span><div class="live-track"><i style="width:{share:.1f}%;background:{color}"></i></div><strong>{count:,}</strong></div>'
    feed = events if feed_mode == "All signals" else events[events.event_type.isin(NEGATIVE)]
    feed_rows = []
    for event in feed.head(40).itertuples(index=False):
        severe = event.event_type == "cancellation"
        negative_event = event.event_type in NEGATIVE
        color = "#ff537f" if negative_event else "#00d9ff"
        severity = "URGENT" if severe else "REVIEW" if negative_event else "INFO"
        feed_rows.append(f'<article class="live-event"><div class="live-event-meta"><time>{datetime.fromtimestamp(event.ts):%H:%M:%S}</time><span style="color:{PROVIDERS.get(event.operator, "#aaa")}">{esc(event.operator)}</span><b style="color:{color}">{severity}</b></div><div class="live-event-title"><strong>{esc(LABELS.get(event.event_type, event.event_type))}</strong><span>{esc(event.customer_id)}</span></div><p>{esc(event.detail)}</p></article>')
    empty = '<div class="live-empty">No signals in this window.</div>' if providers else '<div class="live-empty">No providers selected.</div>'
    table_rows = ''
    for row in queue.head(8).itertuples(index=False):
        table_rows += f'<tr><td><strong>{esc(row.customer_id)}</strong><small style="color:{PROVIDERS.get(row.operator, "#aaa")}">{esc(row.operator)}</small></td><td>{row.neg_events}</td><td><strong class="live-score">{row.priority_score:.0%}</strong><small>base {row.churn_probability:.0%}</small></td><td>{esc(row.suggested_action)}</td></tr>'
    table = ('<div class="live-table-scroll" tabindex="0" aria-label="Customer review queue"><table><thead><tr><th>Customer</th><th>Signals</th><th>Priority</th><th>Suggested action</th></tr></thead><tbody>' + table_rows + '</tbody></table></div>') if len(queue) else '<div class="live-empty">No customers need review in this window.</div>'
    return f'''<div class="live-shell">
      <div class="live-status"><span class="live-state {"paused" if paused else ""}"><i></i>{state}</span><span>{freshness} &nbsp; / &nbsp; Snapshot {datetime.fromtimestamp(now):%H:%M:%S}</span></div>
      <div class="live-kpis">{tiles}</div>
      <div class="live-section-heading"><h3>Provider activity</h3><span>Synthetic provider groups</span></div>
      <div class="live-providers">{''.join(cards)}</div>
      <div class="live-analysis"><section><div class="live-section-heading"><h3>Signal volume</h3><span>{minutes}-minute window</span></div>{timeline(events, now, minutes)}<div class="live-legend"><span><i style="background:#00d9ff"></i>Neutral</span><span><i style="background:#ff537f"></i>Negative</span></div></section><section><div class="live-section-heading"><h3>Event mix</h3><span>{len(events):,} events</span></div>{mix}</section></div>
      <div class="live-workspace"><section><div class="live-section-heading"><h3>Signal feed</h3><span>Latest {min(len(feed), 40)} of {len(feed):,}</span></div><div class="live-feed" tabindex="0" aria-label="Scrollable signal feed">{''.join(feed_rows) or empty}</div></section><section><div class="live-section-heading"><h3>Customer review queue</h3><span>Top {min(len(queue), 8)} of {len(queue):,}</span></div>{table}<p class="live-method">Demo priority = stored model probability + 4 percentage points per negative event, capped at 99%. This heuristic is not a new model prediction.</p></section></div>
    </div>'''
