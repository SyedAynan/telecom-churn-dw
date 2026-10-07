"""HTML/SVG chart components for the Streamlit dashboard.

Hand-built per the dataviz method: thin bars (<=24px), 4px rounded data-ends
(square at baseline), 2px surface gaps between adjacent marks, hairline solid
grids, per-mark hover tooltips, selective direct labels, text in ink tokens
(never series colors), one validated palette for light+dark via
prefers-color-scheme.
"""
from __future__ import annotations

import html
from typing import Sequence

# validated 3-slot categorical (light | dark) — adjacency-safe for bars
SERIES = [("#2a78d6", "#3987e5"), ("#eb6834", "#d95926"), ("#1baf7a", "#199e70")]
INK = {"primary": ("#0b0b0b", "#ffffff"), "secondary": ("#52514e", "#c3c2b7"),
       "muted": ("#898781", "#898781")}
GRID = ("#e1e0d9", "#2c2c2a")
SURFACE = ("#fcfcfb", "#1a1a19")
STATUS = {"critical": ("#d03b3b", "#e66767"), "warning": ("#eda100", "#c98500"),
          "good": ("#0ca30c", "#0ca30c")}


def _mode_css() -> str:
    light, dark = SURFACE
    return f"""
    .viz-root {{ color-scheme: light dark; background: {light}; color: {INK['primary'][0]};
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
    @media (prefers-color-scheme: dark) {{ .viz-root {{ background: {dark};
        color: {INK['primary'][1]}; }} }}
    """


def hbar_chart(
    title: str,
    categories: Sequence[str],
    values: Sequence[float],
    *,
    value_fmt: str = "{:.1%}",
    width: int = 760,
    row_h: int = 34,
    color_slot: int = 0,
    highlight_max: bool = True,
    subtitle: str = "",
) -> str:
    """Horizontal bar chart — one series, magnitude comparison.

    Bars <=24px, 4px rounded data-end, value labels at bar tips (ink color),
    per-bar hover tooltip + lift, hairline grid. highlight_max keeps the
    maximum bar in the series hue and de-emphasizes the rest toward gray
    (emphasis form) — pass False for uniform slot-1 coloring.
    """
    n = len(categories)
    chart_h = n * row_h + 30
    vmax = max(values) if max(values) > 0 else 1.0
    plot_w = width - 150 - 70  # label gutter left, value labels right

    light, dark = SERIES[color_slot]
    hl_light, hl_dark = SERIES[color_slot]
    dim_light, dim_dark = "#b9b8b1", "#4a4a48"

    rows = []
    for i, (cat, val) in enumerate(zip(categories, values)):
        y = 8 + i * row_h
        bar_w = max(2.0, val / vmax * plot_w)
        emphasized = (not highlight_max) or (val == vmax)
        fill = hl_light if emphasized else dim_light
        fill_d = hl_dark if emphasized else dim_dark
        label = html.escape(str(cat))
        vtxt = value_fmt.format(val)
        rows.append(f"""
        <g class="bar-row" tabindex="0" data-cat="{label}" data-val="{vtxt}"
           style="cursor:default">
          <text x="146" y="{y + row_h / 2 + 4}" text-anchor="end"
                class="cat" fill="{INK['secondary'][0]}">{label}</text>
          <rect class="track" x="150" y="{y + row_h / 2 - 11}" width="{plot_w}"
                height="22" rx="4" fill="{GRID[0]}" opacity="0.35"/>
          <rect class="fill" x="150" y="{y + row_h / 2 - 11}" width="{bar_w:.1f}"
                height="22" rx="4" data-fill-l="{fill}" data-fill-d="{fill_d}"
                fill="{fill}"/>
          <text class="val" x="{150 + bar_w + 8:.1f}" y="{y + row_h / 2 + 4}"
                fill="{INK['primary'][0]}" font-weight="600">{vtxt}</text>
        </g>""")

    sub = f'<div class="sub">{html.escape(subtitle)}</div>' if subtitle else ""
    return f"""<!DOCTYPE html>
<html><head><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; }}
  .viz-root {{ padding:16px 12px 8px; }}
  .title {{ font-size:14px; font-weight:600; color:{INK['primary'][0]}; margin-bottom:2px; }}
  .sub {{ font-size:12px; color:{INK['muted'][0]}; margin-bottom:10px; }}
  .cat {{ font-size:12.5px; }}
  .val {{ font-size:12.5px; }}
  .bar-row:focus, .bar-row:hover .fill {{ filter: brightness(1.08); }}
  .bar-row:hover .cat, .bar-row:focus .cat {{ fill:{INK['primary'][0]}; }}
  .tip {{ position:absolute; pointer-events:none; background:{SURFACE[1]};
    color:{INK['primary'][1]}; border:1px solid rgba(255,255,255,.14);
    border-radius:6px; padding:6px 10px; font-size:12px; display:none;
    box-shadow:0 4px 14px rgba(0,0,0,.25); white-space:nowrap; z-index:5; }}
  .tip .t-strong {{ font-weight:600; }}
  svg {{ display:block; }}
  @media (prefers-color-scheme: dark) {{
    .viz-root {{ color:{INK['primary'][1]}; }}
    .title {{ color:{INK['primary'][1]}; }}
    .sub {{ color:{INK['muted'][1]}; }}
    .cat {{ fill:{INK['secondary'][1]}; }}
    .val {{ fill:{INK['primary'][1]}; }}
    .bar-row:hover .cat, .bar-row:focus .cat {{ fill:{INK['primary'][1]}; }}
    .bar-row .fill {{ fill: attr(data-fill-d); }}
    .tip {{ background:#26262
    5; }}
  }}
  /* fill swap via JS (attr() not supported in < media queries on Chrome) */
</style></head>
<body><div class="viz-root" style="position:relative">
  <div class="title">{html.escape(title)}</div>{sub}
  <svg width="{width}" height="{chart_h}" role="img"
       aria-label="{html.escape(title)} bar chart">
    <g class="bars">{''.join(rows)}</g>
  </svg>
  <div class="tip"></div>
</div>
<script>
(function() {{
  const root = document.currentScript.closest('.viz-root');
  if (!root) return;
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const fills = root.querySelectorAll('rect.fill');
  function apply(mode) {{
    root.querySelectorAll('rect.track').forEach(r => {{
      r.setAttribute('fill', mode ? '{GRID[1]}' : '{GRID[0]}');
      r.setAttribute('opacity', '0.5');
    }});
    fills.forEach(r => {{
      r.setAttribute('fill', mode ? r.dataset.fillD : r.dataset.fillL);
    }});
    root.querySelectorAll('text.cat').forEach(t => t.setAttribute('fill', mode ? '{INK['secondary'][1]}' : '{INK['secondary'][0]}'));
    root.querySelectorAll('text.val').forEach(t => t.setAttribute('fill', mode ? '{INK['primary'][1]}' : '{INK['primary'][0]}'));
    const tip = root.querySelector('.tip');
    tip.style.background = mode ? '#262625' : '{SURFACE[0]}';
    tip.style.color = mode ? '{INK['primary'][1]}' : '{INK['primary'][0]}';
    tip.style.borderColor = mode ? 'rgba(255,255,255,.14)' : 'rgba(11,11,11,.10)';
  }}
  apply(mq.matches);
  mq.addEventListener ? mq.addEventListener('change', e => apply(e.matches)) : mq.addListener(e => apply(e.matches));
  const tip = root.querySelector('.tip');
  root.querySelectorAll('.bar-row').forEach(g => {{
    const show = () => {{
      tip.innerHTML = '<span class="t-strong">' + g.dataset.cat + '</span> — '
        + '<span class="t-strong">' + g.dataset.val + '</span>';
      tip.style.display = 'block';
      const rg = root.getBoundingClientRect(), gg = g.getBoundingClientRect();
      tip.style.left = Math.max(4, Math.min(rg.width - 120, gg.left - rg.left + 8)) + 'px';
      tip.style.top = (gg.top - rg.top - 34) + 'px';
    }};
    g.addEventListener('pointerenter', show);
    g.addEventListener('focus', show);
    g.addEventListener('pointerleave', () => tip.style.display = 'none');
    g.addEventListener('blur', () => tip.style.display = 'none');
  }});
}})();
</script></body></html>"""


def coefficient_chart(
    title: str,
    features: Sequence[str],
    coefs: Sequence[float],
    *,
    width: int = 760,
    row_h: int = 34,
    subtitle: str = "",
) -> str:
    """Diverging horizontal bar chart of model coefficients (polarity job).

    Positive (churn-up) bars in orange, negative (protective) in blue — the
    validated warm/cool pair with gray midpoint at zero. Diverging form, not
    a value ramp on nominal categories.
    """
    n = len(features)
    chart_h = n * row_h + 30
    vmax = max(abs(c) for c in coefs)
    plot_w = width - 230 - 60  # long feature labels left, values right
    mid = 110 + plot_w / 2

    rows = []
    for i, (feat, coef) in enumerate(zip(features, coefs)):
        y = 8 + i * row_h
        w = abs(coef) / vmax * (plot_w / 2 - 6)
        x = mid if coef >= 0 else mid - w
        fill_l = "#eb6834" if coef >= 0 else "#2a78d6"
        fill_d = "#d95926" if coef >= 0 else "#3987e5"
        vtxt = f"{coef:+.2f}"
        rows.append(f"""
        <g class="bar-row" tabindex="0" data-cat="{html.escape(feat)}" data-val="{vtxt}">
          <text x="{mid - plot_w / 2 - 8}" y="{y + row_h / 2 + 4}" text-anchor="end"
                class="cat" fill="{INK['secondary'][0]}">{html.escape(feat)}</text>
          <line x1="{mid}" y1="{y + 4}" x2="{mid}" y2="{y + row_h - 4}"
                stroke="{GRID[0]}" stroke-width="1"/>
          <rect class="fill" x="{x:.1f}" y="{y + row_h / 2 - 11}" width="{w:.1f}"
                height="22" rx="4" data-fill-l="{fill_l}" data-fill-d="{fill_d}"
                fill="{fill_l}"/>
          <text class="val" x="{(mid + w + 8) if coef >= 0 else (mid - w - 8):.1f}"
                y="{y + row_h / 2 + 4}"
                text-anchor="{'start' if coef >= 0 else 'end'}"
                fill="{INK['primary'][0]}" font-weight="600">{vtxt}</text>
        </g>""")

    sub = f'<div class="sub">{html.escape(subtitle)}</div>' if subtitle else ""
    return f"""<!DOCTYPE html>
<html><head><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; }}
  .viz-root {{ padding:16px 12px 8px; }}
  .title {{ font-size:14px; font-weight:600; color:{INK['primary'][0]}; }}
  .sub {{ font-size:12px; color:{INK['muted'][0]}; margin-bottom:10px; }}
  .cat, .val {{ font-size:12.5px; }}
  .bar-row:hover .fill {{ filter: brightness(1.08); }}
  .tip {{ position:absolute; pointer-events:none; background:{SURFACE[0]};
    color:{INK['primary'][0]}; border:1px solid rgba(11,11,11,.10); border-radius:6px;
    padding:6px 10px; font-size:12px; display:none; box-shadow:0 4px 14px rgba(0,0,0,.15);
    white-space:nowrap; z-index:5; }}
  svg {{ display:block; }}
</style></head>
<body><div class="viz-root" style="position:relative">
  <div class="title">{html.escape(title)}</div>{sub}
  <svg width="{width}" height="{chart_h}" role="img"
       aria-label="{html.escape(title)} diverging bar chart">
    {''.join(rows)}
  </svg>
  <div class="tip"></div>
</div>
<script>
(function() {{
  const root = document.currentScript.closest('.viz-root');
  if (!root) return;
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  function apply(mode) {{
    root.querySelectorAll('rect.fill').forEach(r => {{
      r.setAttribute('fill', mode ? r.dataset.fillD : r.dataset.fillL);
    }});
    root.querySelectorAll('line').forEach(l => {{
      l.setAttribute('stroke', mode ? '{GRID[1]}' : '{GRID[0]}');
    }});
    root.querySelectorAll('text.cat').forEach(t => t.setAttribute('fill', mode ? '{INK['secondary'][1]}' : '{INK['secondary'][0]}'));
    root.querySelectorAll('text.val').forEach(t => t.setAttribute('fill', mode ? '{INK['primary'][1]}' : '{INK['primary'][0]}'));
    const tip = root.querySelector('.tip');
    tip.style.background = mode ? '#262625' : '{SURFACE[0]}';
    tip.style.color = mode ? '{INK['primary'][1]}' : '{INK['primary'][0]}';
    tip.style.borderColor = mode ? 'rgba(255,255,255,.14)' : 'rgba(11,11,11,.10)';
  }}
  apply(mq.matches);
  mq.addEventListener ? mq.addEventListener('change', e => apply(e.matches)) : mq.addListener(e => apply(e.matches));
  const tip = root.querySelector('.tip');
  root.querySelectorAll('.bar-row').forEach(g => {{
    const show = () => {{
      tip.innerHTML = '<span class="t-strong">' + g.dataset.cat + '</span> — <span class="t-strong">' + g.dataset.val + '</span>';
      tip.style.display = 'block';
      const rg = root.getBoundingClientRect(), gg = g.getBoundingClientRect();
      tip.style.left = Math.max(4, Math.min(rg.width - 130, gg.left - rg.left + 8)) + 'px';
      tip.style.top = (gg.top - rg.top - 34) + 'px';
    }};
    g.addEventListener('pointerenter', show);
    g.addEventListener('focus', show);
    g.addEventListener('pointerleave', () => tip.style.display = 'none');
    g.addEventListener('blur', () => tip.style.display = 'none');
  }});
}})();
</script></body></html>"""


def risk_meter(p: float) -> str:
    """Single probability as a meter — same-ramp track, fill = severity.

    For the watchlist rows: blue fill when low, orange when medium, red
    (status-critical family) when high. Track is a lighter step of the same
    ramp so state reads across the whole bar, not just the filled part.
    """
    if p >= 0.75:
        fill_l, fill_d, track_l, track_d = "#d03b3b", "#e66767", "#f5c6c6", "#5a2626"
    elif p >= 0.45:
        fill_l, fill_d, track_l, track_d = "#eb6834", "#d95926", "#f8d4c4", "#5c2d1a"
    else:
        fill_l, fill_d, track_l, track_d = "#2a78d6", "#3987e5", "#cde2fb", "#17325c"
    pct = min(100, p * 100)
    return f"""<div class="meter" style="display:flex;align-items:center;gap:8px">
      <div style="flex:1;background:{track_l};height:8px;border-radius:4px;overflow:hidden;position:relative">
        <div style="width:{pct:.1f}%;background:{fill_l};height:100%;border-radius:4px"></div>
      </div>
      <span style="font-size:12px;color:{INK['secondary'][0]};font-variant-numeric:tabular-nums">{p:.1%}</span>
    </div>"""


def style_kpi(label: str, value: str, delta: str = "", delta_good: bool = True) -> str:
    """Stat tile: label / value / optional delta. Values in ink, never series colors."""
    d = ""
    if delta:
        color = ("#006300", "#0ca30c") if delta_good else ("#d03b3b", "#e66767")
        d = f'<div style="font-size:12px;color:{color[0]};margin-top:2px">{delta}</div>'
    return f"""<div style="padding:2px 0">
      <div style="font-size:12px;color:{INK['muted'][0]}">{html.escape(label)}</div>
      <div style="font-size:28px;font-weight:600;color:{INK['primary'][0]};
                  line-height:1.15;margin-top:2px">{html.escape(value)}</div>{d}
    </div>"""
