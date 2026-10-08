"""Motion-design chrome for the dashboard: animated KPI tiles, gradients,
and page-level entrance choreography. Pure CSS keyframes + a tiny JS count-up
with reduced-motion respect — no external animation libraries.
"""
from __future__ import annotations

import html
import itertools

_ids = itertools.count(1)

# Page-level CSS injected once via st.markdown (scoped under [data-testid]).
PAGE_CSS = """
<style>
/* ---------- app shell ---------- */
[data-testid="stAppViewContainer"] {
  background: #fafaf8;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #10131a 0%, #1a1d26 100%);
  border-right: 1px solid rgba(255,255,255,.07);
}
[data-testid="stSidebar"] * { color: #e8e6df !important; }
[data-testid="stSidebar"] .stRadio label { padding: 6px 10px; border-radius: 8px;
  transition: background .2s, transform .2s; }
[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,255,255,.06); transform: translateX(2px); }

/* ---------- page entrance ---------- */
[data-testid="stMainBlock"] > div {
  animation: pageRise .55s cubic-bezier(.22,1,.36,1) backwards; }
[data-testid="stMainBlock"] > div:nth-child(2) { animation-delay: .08s; }
[data-testid="stMainBlock"] > div:nth-child(3) { animation-delay: .16s; }
[data-testid="stMainBlock"] > div:nth-child(4) { animation-delay: .24s; }
[data-testid="stMainBlock"] > div:nth-child(5) { animation-delay: .30s; }

/* ---------- headings ---------- */
h1 {
  font-family: 'Space Grotesk', system-ui, sans-serif !important;
  letter-spacing: -0.02em;
  background: linear-gradient(92deg, #0b0b0b 30%, #2a78d6 55%, #eb6834 85%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
  background: linear-gradient(92deg, #ffffff 40%, #3987e5 75%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; }
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,.08) !important; }

/* ---------- data table ---------- */
[data-testid="stDataFrame"] div[data-testid*="dG"] {
  transition: transform .2s; }
[data-testid="stDataFrame"]:hover { box-shadow: 0 6px 22px rgba(11,11,11,.08); }

/* ---------- buttons ---------- */
[data-testid="stDownloadButton"] > button {
  transition: transform .18s cubic-bezier(.34,1.56,.64,1),
    box-shadow .18s !important; }
[data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(42,120,214,.25) !important; }

/* ---------- scrollbars ---------- */
[data-testid="stDataFrame"]::-webkit-scrollbar { width: 8px; }
[data-testid="stDataFrame"]::-webkit-scrollbar-thumb {
  background: #c3c2b7; border-radius: 4px; }

/* ---------- dark ---------- */
@media (prefers-color-scheme: dark) {
  [data-testid="stAppViewContainer"] { background: #0d0d0d; }
  h1 { background: linear-gradient(92deg, #ffffff 30%, #3987e5 55%, #d95926 85%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; }
}

@keyframes pageRise { from { opacity: 0; transform: translateY(18px); } }

/* ---------- reduced motion ---------- */
@media (prefers-reduced-motion: reduce) {
  [data-testid="stMainBlock"] > div, .kpi-root, .kpi-value, .kpi-spark path,
  rect.fill, text.val, .ticker-item { animation: none !important;
    transition: none !important; }
}
</style>
"""


def kpi_tile(
    label: str,
    value: str,
    *,
    delta: str = "",
    delta_good: bool = True,
    accent: str = "blue",
    spark: list[float] | None = None,
    height: int = 110,
) -> str:
    """Animated stat tile: gradient wash + counting value + optional sparkline.

    accent: blue | orange | red — drives the tile's accent hue (matches the
    chart palette slots; status red only for the watchlist count).
    """
    uid = f"kpi{next(_ids)}"
    accents = {
        "blue": ("#2a78d6", "#3987e5", "rgba(42,120,214,.10)", "rgba(56,135,229,.14)"),
        "orange": ("#eb6834", "#d95926", "rgba(235,104,52,.10)", "rgba(217,89,38,.14)"),
        "red": ("#d03b3b", "#e66767", "rgba(208,59,59,.10)", "rgba(230,103,103,.16)"),
    }
    a_l, a_d, wash_l, wash_d = accents[accent]

    d_html = ""
    if delta:
        good = ("#006300", "#0ca30c") if delta_good else ("#d03b3b", "#e66767")
        d_html = (
            f'<div class="kpi-delta" style="color:{good[0]};'
            f'--gdd:{good[1]}">{html.escape(delta)}</div>'
        )

    spark_html = ""
    if spark and len(spark) >= 2:
        w, h = 120, 30
        vmin, vmax = min(spark), max(spark)
        rng = (vmax - vmin) or 1.0
        pts = " ".join(
            f"{i * (w - 8) / (len(spark) - 1) + 4:.1f},"
            f"{h - 3 - (v - vmin) / rng * (h - 8):.1f}"
            for i, v in enumerate(spark)
        )
        spark_html = f"""
        <svg class="kpi-spark" width="{w}" height="{h}" aria-hidden="true">
          <path d="M{pts}" fill="none" stroke="{a_l}" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="{pts.split()[-1].split(',')[0]}" cy="{pts.split()[-1].split(',')[1]}"
                  r="3.5" fill="{a_l}" stroke="#fcfcfb" stroke-width="1.5"/>
        </svg>"""

    return f"""<!DOCTYPE html><html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; }}
.kpi-root {{
  font-family: 'Space Grotesk', system-ui, sans-serif;
  border-radius: 12px; padding: 14px 16px 12px;
  background: {wash_l};
  border: 1px solid rgba(11,11,11,.06);
  animation: rise .5s cubic-bezier(.22,1,.36,1) backwards;
  transition: transform .2s cubic-bezier(.34,1.56,.64,1),
    box-shadow .2s, background .2s;
  position: relative; overflow: hidden;
}}
.kpi-root:hover {{ transform: translateY(-3px);
  box-shadow: 0 10px 26px rgba(11,11,11,.10); }}
.kpi-root::after {{
  content:''; position:absolute; inset: 0 auto 0 0; width: 3px;
  background: {a_l};
}}
.kpi-label {{ font-size: 11.5px; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; color: #52514e; }}
.kpi-value {{
  font-size: 30px; font-weight: 700; color: #0b0b0b; line-height: 1.1;
  margin: 4px 0 2px; font-variant-numeric: tabular-nums;
}}
.kpi-delta {{ font-size: 12px; color: #006300; }}
.kpi-spark path {{ stroke-dasharray: 300; stroke-dashoffset: 300;
  animation: draw 1.1s cubic-bezier(.4,0,.2,1) .45s forwards; }}
.kpi-spark circle {{ animation: fadein .4s ease-out 1.4s backwards; }}
@keyframes rise {{ from {{ opacity:0; transform: translateY(14px); }} }}
@keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
@keyframes fadein {{ from {{ opacity: 0; }} }}
@media (prefers-color-scheme: dark) {{
  .kpi-root {{ background: {wash_d}; border-color: rgba(255,255,255,.08); }}
  .kpi-root:hover {{ box-shadow: 0 10px 26px rgba(0,0,0,.35); }}
  .kpi-root::after {{ background: {a_d}; }}
  .kpi-label {{ color: #c3c2b7; }}
  .kpi-value {{ color: #ffffff; }}
  .kpi-delta {{ color: var(--gdd, #0ca30c); }}
  .kpi-spark path {{ stroke: {a_d}; }}
  .kpi-spark circle {{ fill: {a_d}; stroke: #1a1a19; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .kpi-root, .kpi-value, .kpi-spark path, .kpi-spark circle {{
    animation: none !important; transition: none !important; }}
  .kpi-spark path {{ stroke-dashoffset: 0; }}
}}
</style></head><body>
<div class="kpi-root">
  <div class="kpi-label">{html.escape(label)}</div>
  <div class="kpi-value" id="{uid}">{html.escape(value)}</div>
  {d_html}
  {spark_html}
</div>
<script>
(function () {{
  var el = document.getElementById('{uid}');
  var raw = el.textContent;
  var m = raw.match(/^([^0-9.-]*)([0-9.,]+)(.*)$/);
  if (!m) return;
  var pre = m[1], num = m[2], suf = m[3];
  var target = parseFloat(num.replace(/,/g, ''));
  if (!isFinite(target)) return;
  var decimals = (num.split('.')[1] || '').length;
  var isPct = suf.indexOf('%') >= 0;
  var isMoney = pre.indexOf('$') >= 0;
  var dur = 900, t0 = null;
  var rm = window.matchMedia('(prefers-reduced-motion: reduce)');
  function fmt(v) {{
    var s = v.toLocaleString('en-US', {{
      minimumFractionDigits: decimals, maximumFractionDigits: decimals }});
    return (isMoney ? '$' : '') + s + (isPct ? '%' : '');
  }}
  function tick(t) {{
    if (t0 === null) t0 = t;
    var p = Math.min(1, (t - t0) / dur);
    var eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(target * eased);
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = raw;
  }}
  if (rm.matches) return;
  requestAnimationFrame(tick);
}})();
</script></body></html>"""
