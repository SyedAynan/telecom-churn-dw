"""Compact, warehouse-backed visual panels for the reference-style overview."""
from __future__ import annotations

import html
import re

import pandas as pd
from app.providers import PROVIDERS
from app.assets import icon, svg_image, provider_banner

COLORS = ["#ff237c", "#00d9ff", "#ffb53d", "#ad57ff", "#00efb2"]
STYLE = """
*{box-sizing:border-box}html,body{height:100%;margin:0;background:transparent;color:#e8f1ff;font:12px 'Segoe UI',Arial,sans-serif}
.panel{padding:14px 16px;background:linear-gradient(125deg,#111116,#08080c);border:1px solid #29383e;
border-radius:11px;box-shadow:inset 0 0 18px #00d9ff08,0 0 8px #00d9ff05;height:100%;overflow:hidden}
.panel:hover{border-color:#00d9ff70;box-shadow:inset 0 0 18px #00d9ff08,0 0 9px #00d9ff12}
h3{font-size:14px;font-weight:600;margin:0 0 5px}p{color:#989caf;font-size:11px;margin:0 0 10px}
svg{width:100%;height:170px;display:block}text{font-family:'Segoe UI',Arial,sans-serif;fill:#babdcc;font-size:11px}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0;color:#b9bdcf;font-size:11px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.insight{display:flex;gap:10px;margin:17px 0;line-height:1.55;color:#c9ccda}.insight b{color:#fff}
.mark{color:#2ddcb5;font-size:18px}.table{width:100%;border-collapse:collapse;font-size:11px}
th{text-align:left;color:#a3a8bd;font-weight:500;background:#14141c}td,th{padding:9px 8px;border-bottom:1px solid #25252e}
td{color:#d9e8fb}td:last-child,th:last-child{text-align:right}
.segments{display:flex;gap:9px;margin-top:18px}.segment{flex:1;padding:17px 7px;text-align:center;border:1px solid #27383e;border-radius:9px;background:#101017}
.segment strong{display:block;font-size:24px;color:white;margin:17px 0 10px}.segment small{color:#88a7c8}
@media(prefers-reduced-motion:no-preference){.panel{animation:in .4s ease-out}@keyframes in{from{opacity:0;transform:translateY(5px)}}}
"""


def panel(title: str, body: str, subtitle: str = "", asset: str | None = None) -> str:
    def embed(match):
        svg = match.group()
        classes = re.search(r'class="([^"]+)"', svg)
        # SVG presented as an image survives st.html sanitization. Give its
        # text explicit colours, since the document stylesheet cannot reach it.
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        svg = svg.replace('<text ', '<text fill="#9c9caf" font-family="Arial,sans-serif" font-size="11" ')
        svg = svg.replace('fill:white', 'fill:#eeeef3')
        return svg_image(svg, css_class=classes[1] if classes else "chart-image", label=title)
    body = re.sub(r'<svg\b[\s\S]*?</svg>', embed, body)
    mark = icon(asset, "#00d9ff") if asset else ""
    return (f'<section class="panel"><header class="panel-heading"><h3>{mark}{html.escape(title)}</h3>'
            f'<p>{html.escape(subtitle)}</p></header>{body}</section>')


def tenure_chart(base: pd.DataFrame, simulated: bool = False) -> str:
    buckets = pd.cut(base.tenure_months, [-1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72])
    grouped = base.groupby(buckets, observed=False).churned.agg(["count", "sum", "mean"])
    peak = max(float(grouped["count"].max()), 1)
    body = '<div class="chart-scroll" tabindex="0" aria-label="Scrollable tenure chart"><svg class="tenure-svg" viewBox="0 0 640 210" role="img" aria-label="Customer counts and churn rate by tenure, not calendar time">'
    for i in range(5):
        y = 168 - i * 35
        body += f'<path d="M40 {y}H600" stroke="#25252e"/><text x="32" y="{y+4}" text-anchor="end">{peak*i/4:.0f}</text><text x="608" y="{y+4}">{i*25}%</text>'
    points = []
    for i, (_, row) in enumerate(grouped.iterrows()):
        x = 49 + i * 46
        retained = (row["count"] - row["sum"]) / peak * 140
        lost = row["sum"] / peak * 140
        label = f'{i*6+1}–{(i+1)*6}' if i else '0–6'
        body += f'<g><title>{label} months: {int(row["count"]):,} customers, {row["mean"]:.1%} churn</title><rect x="{x}" y="{168-lost}" width="26" height="{lost}" fill="#ff237c"/><rect x="{x}" y="{168-lost-retained}" width="26" height="{retained}" fill="#00d9ff" rx="2"/></g>'
        body += f'<text x="{x+13}" y="187" text-anchor="middle" style="font-size:9px">{label}</text>'
        points.append((x+13, 168-float(row["mean"] if pd.notna(row["mean"]) else 0)*140))
    body += '<polyline points="' + ' '.join(f'{x},{y}' for x,y in points) + '" stroke="#c789ff" stroke-width="2" fill="none"/>'
    body += ''.join(f'<circle cx="{x}" cy="{y}" r="3" fill="#e1b9ff"/>' for x,y in points)
    body += '</svg></div><div class="legend"><span><i class="dot" style="background:#00d9ff"></i>Retained</span><span><i class="dot" style="background:#ff237c"></i>Churned</span><span><i class="dot" style="background:#c789ff"></i>Churn rate · right axis</span></div>'
    return panel("Customer tenure & churn", body, "Customer tenure in months · " + ("Simulated outcomes" if simulated else "February 2020 snapshot"))


def contract_donut(base: pd.DataFrame) -> str:
    groups = base[base.churned].groupby("contract_label").size().sort_values(ascending=False)
    total = max(int(groups.sum()), 1)
    body = '<svg class="donut-svg" viewBox="0 0 300 210" role="img" aria-label="Share of churned customers by contract">'
    offset = 0.0
    for i, (label, value) in enumerate(groups.items()):
        portion = float(value) / total * 100
        body += f'<circle cx="150" cy="104" r="72" fill="none" stroke="{COLORS[i]}" stroke-width="29" pathLength="100" stroke-dasharray="{portion} {100-portion}" stroke-dashoffset="{-offset}" transform="rotate(-90 150 104)"><title>{html.escape(label)}: {int(value):,} churned customers ({portion:.1f}%)</title></circle>'
        offset += portion
    body += f'<text x="150" y="101" text-anchor="middle" style="fill:white;font-size:26px;font-weight:700">{base.churned.mean():.1%}</text><text x="150" y="121" text-anchor="middle">Overall churn rate</text></svg>'
    body += '<div class="legend">' + ''.join(f'<span><i class="dot" style="background:{COLORS[i]}"></i>{html.escape(label)} {value/total:.1%}</span>' for i,(label,value) in enumerate(groups.items())) + '</div>'
    return panel("Churn by contract", body, "Share of churned customers")


def bars(title: str, labels: list, values: list, *, money: bool = False, counts: bool = False) -> str:
    maximum = max(max(values, default=0), 0.001)
    body = '<div class="bar-list">'
    for i, (label, value) in enumerate(zip(labels, values)):
        formatted = f'{value:,.0f}' if counts else f'${value:,.0f}' if money else f'{value:.1%}'
        body += (f'<div class="bar-item"><div class="bar-label"><span>{html.escape(str(label))}</span>'
                 f'<strong>{formatted}</strong></div><div class="bar-track" aria-hidden="true">'
                 f'<div style="width:{100*value/maximum:.2f}%;background:{COLORS[i%len(COLORS)]}"></div></div></div>')
    return panel(title, body + '</div>', "Customers by dominant risk factor" if counts else "Monthly charges · USD" if money else "Observed churn rate by segment")


def insights(base: pd.DataFrame, summary: pd.DataFrame, simulated: bool = False) -> str:
    facts = []
    for segment in ("contract", "tenure_bucket", "payment_method"):
        rows = summary[summary.segment_type == segment]
        highest = rows.loc[rows.churn_rate.idxmax()]
        label = html.escape(str(highest.segment_label)) + (" months" if segment == "tenure_bucket" else "")
        facts.append(f'<b>{label}</b> customers have <b>{highest.churn_rate:.1%}</b> churn.')
    score_label = "demo risk score" if simulated else "model churn probability"
    facts.append(f'<b>{int((base.risk_band == "high").sum()):,} customers</b> score at least 75% {score_label}.')
    assets = ["file-check-alt", "chart-line", "credit-card", "users-alt"]
    body = ''.join(f'<div class="insight"><span class="insight-asset">{icon(asset, "#b39aff")}</span><span>{fact}</span></div>' for fact, asset in zip(facts, assets))
    return panel("Key insights", body, "From the simulated scenario" if simulated else "From your warehouse", asset="lightbulb-alt")


def recommendations() -> str:
    items = ["Review high-risk customers in the Watchlist before planning outreach.", "Explore longer-term contracts for month-to-month customers.", "Prioritize onboarding support during the first year.", "Review billing friction for electronic-check customers."]
    assets = ["users-alt", "file-check-alt", "headphones-alt", "credit-card"]
    return panel("Retention opportunities", ''.join(f'<div class="insight"><span class="insight-asset">{icon(asset, "#22d3bb")}</span><span>{item}</span></div>' for item, asset in zip(items, assets)), "Suggested actions · validate with your retention team", asset="shield-check")


def customer_table(base: pd.DataFrame, simulated: bool = False) -> str:
    rows = base[base.churned].sort_values("churn_probability", ascending=False).head(5)
    body = '<div class="table-scroll" tabindex="0" aria-label="Scrollable customer sample"><table class="table"><thead><tr><th>Customer ID</th><th>Contract</th><th>Tenure</th><th>Monthly bill</th><th>Model risk</th></tr></thead><tbody>'
    for row in rows.itertuples():
        body += f'<tr><td>{html.escape(row.customer_id)}</td><td>{html.escape(row.contract_label)}</td><td>{row.tenure_months} mo</td><td>${row.monthly_charges:.2f}</td><td style="color:#ff668f">{row.churn_probability:.1%}</td></tr>'
    return panel("Churned customers · sample", body + '</tbody></table></div>', "Simulated outcomes and scores" if simulated else "Historical outcomes · ranked by model probability")


def provider_cards(base: pd.DataFrame, selected: str) -> str:
    cards = []
    for name, color in PROVIDERS.items():
        group = base[base.provider == name]
        rate = f"{group.churned.mean():.1%}" if len(group) else "—"
        cards.append(f'<article class="provider-card {"selected" if selected == name else ""}" style="--provider:{color}">'
                     f'{provider_banner(name, "SELECTED" if selected == name else "DEMO GROUP")}'
                     f'<div class="provider-numbers"><strong>{len(group):,}<small>customers</small></strong>'
                     f'<strong>{rate}<small>churn rate</small></strong></div></article>')
    return ('<div class="provider-banner"><div class="banner-label"><div class="section-icon-label">'
            + icon("signal", "#00d9ff") + 'NETWORK PORTFOLIO</div><span>Four providers. One view.</span></div><div class="provider-grid">'
            + ''.join(cards) + '</div></div>')


def dashboard(base: pd.DataFrame, summary: pd.DataFrame, revenue: pd.DataFrame, *, all_customers: pd.DataFrame | None = None, provider: str = "All providers") -> str:
    """A single flowing grid so cards respond to available content width."""
    simulated = "simulation_second" in base.columns
    source_label = "Simulated live demo" if simulated else "February 2020 snapshot"
    value = revenue.loc[revenue.segment_type == "risk_band", "addressable_revenue"].sum()
    metrics = [
        ("Total customers", f"{len(base):,}", "Customers in the snapshot", "#00d9ff", "users"),
        ("Churned customers", f"{int(base.churned.sum()):,}", "Simulated customer exits" if simulated else "Observed customer exits", "#ff237c", "exit"),
        ("Overall churn rate", f"{base.churned.mean():.1%}", "Share of all customers", "#ad57ff", "percent"),
        ("Monthly charges", f"${base.monthly_charges.sum():,.0f}", "Across all customers · USD", "#00efb2", "wallet"),
        ("Addressable retention value", f"${value:,.0f}", "Modelled lifetime value at risk", "#ffb53d", "shield"),
    ]
    icons = {"users": "users-alt", "exit": "user-minus", "percent": "percentage", "wallet": "wallet", "shield": "shield-check"}
    kpis = ''.join(
        f'<article class="stat-card" style="--accent:{color}"><div class="stat-top">'
        f'<span class="stat-icon">{icon(icons[icon_name], color)}</span>'
        f'<span class="stat-label">{label}</span></div><div class="stat-value">{amount}</div>'
        f'<div class="stat-note">{note}</div></article>'
        for label, amount, note, color, icon_name in metrics
    )
    segment_panels = []
    for segment, title in [("contract", "Contract performance"), ("payment_method", "Payment behaviour"), ("tenure_bucket", "Customer tenure segments")]:
        rows = summary[summary.segment_type == segment].sort_values("segment_label")
        labels = [str(label).replace(" (automatic)", "") + (" months" if segment == "tenure_bucket" else "") for label in rows.segment_label]
        segment_panels.append(bars(title, labels, rows.churn_rate.tolist()))
    economics = base.groupby("contract_label").monthly_charges.sum()
    segment_panels.append(bars("Revenue by contract", economics.index.tolist(), economics.tolist(), money=True))
    title = "Customer overview" if provider == "All providers" else f"{html.escape(provider)} overview"
    networks = provider_cards(all_customers, provider) if all_customers is not None else ""
    return ('<div class="overview-shell"><div class="overview-head"><div><div class="eyebrow">CUSTOMER INTELLIGENCE</div>'
            f'<h2>{title}</h2><p>{"Accelerated demo · outcomes, bills and risk scores vary every second." if simulated else "Churn, revenue, and retention opportunities."}</p></div>'
            f'<span class="snapshot-pill"><i></i> {source_label}</span></div>'
            f'{networks}'
            f'<div class="stats-grid">{kpis}</div><div class="section-label">PERFORMANCE OVERVIEW<span>01 — Portfolio health</span></div>'
            f'<div class="primary-grid">{tenure_chart(base, simulated)}{contract_donut(base)}</div>'
            '<div class="section-label">WHAT DRIVES CHURN<span>02 — Segments & opportunities</span></div>'
            f'<div class="analysis-grid"><div class="segment-grid">{"".join(segment_panels)}</div>'
            f'<aside class="insights-stack">{insights(base, summary, simulated)}{recommendations()}</aside></div>'
            f'<div class="customer-section">{customer_table(base, simulated)}</div></div>')
