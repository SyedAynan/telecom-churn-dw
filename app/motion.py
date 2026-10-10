"""ChaiUI chrome for the dashboard — the chaicode.com look.

Near-black warm background, neutral greys, white Manrope headlines, one
cream highlight phrase, warm hairline cards (orange-50/15 edge, black/10
fill, blur, no shadow), asymmetric-corner buttons, restrained colour.
Orange is nearly absent — it lives in the logo glint and hairlines only.
Status is text colour, never filled pills.
"""
from __future__ import annotations

import html
import itertools

_ids = itertools.count(1)

# ChaiUI tokens, mapped to a Streamlit-injected stylesheet.
#   bg      #0a0a0a   card edge   rgba(255,247,237,.15)  → hover .30
#   fill    rgba(0,0,0,.10) + blur  highlight   #00d9ff (orange-100)
#   text    #f5f5f4   muted        #a3a3a3      brand     #f5a97f-ish (logo only)
PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400..800&family=Montserrat:wght@400..800&family=Onest:wght@400..700&family=Geist+Mono:wght@400..600&display=swap');

:root {
  --chai-bg:#0a0a0a; --chai-card:rgba(0,0,0,.10); --chai-edge:rgba(255,247,237,.15);
  --chai-edge-hover:rgba(255,247,237,.30); --chai-text:#f5f5f4;
  --chai-muted:#a3a3a3; --chai-hi:#00d9ff; --chai-green:#34d399;
  --chai-red:#f87171; --chai-yellow:#fbbf24; --chai-purple:#a78bfa;
}

/* ---------- app shell ---------- */
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #0a0a0a; }
html, body, .stApp { font-family: 'Manrope', system-ui, sans-serif !important;
  color: var(--chai-text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: #0d0d0d;
  border-right: 1px solid var(--chai-edge);
}
[data-testid="stSidebar"] * { color: var(--chai-text) !important; }
[data-testid="stSidebar"] .stRadio label { padding: 7px 12px; border-radius: 10px;
  transition: background .25s, transform .25s; font-weight: 500; }
[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(255,247,237,.05); transform: translateX(2px); }
[data-testid="stSidebar"] hr { border-color: var(--chai-edge) !important; }
/* wordmark */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
  font-family: 'Onest', system-ui, sans-serif !important;
  letter-spacing: -0.02em; color: #ffffff !important; }

/* ---------- page entrance ---------- */
[data-testid="stMainBlock"] > div {
  animation: chaiRise .5s cubic-bezier(.22,1,.36,1) backwards; }
[data-testid="stMainBlock"] > div:nth-child(2) { animation-delay: .06s; }
[data-testid="stMainBlock"] > div:nth-child(3) { animation-delay: .12s; }
[data-testid="stMainBlock"] > div:nth-child(4) { animation-delay: .18s; }
[data-testid="stMainBlock"] > div:nth-child(5) { animation-delay: .24s; }

/* ---------- type ---------- */
h1 {
  font-family: 'Montserrat', 'Manrope', system-ui, sans-serif !important;
  font-weight: 600 !important; letter-spacing: -0.025em !important;
  color: #ffffff !important; font-size: 30px !important;
  background: none !important; -webkit-text-fill-color: unset !important;
}
h2, h3, h4 { font-family: 'Manrope', system-ui, sans-serif !important;
  font-weight: 500 !important; color: var(--chai-text) !important; }
p, .stMarkdown { color: var(--chai-muted) !important; }
strong { color: var(--chai-text); font-weight: 600; }
code { font-family: 'Geist Mono', ui-monospace, monospace !important;
  color: var(--chai-hi) !important; background: rgba(255,247,237,.06) !important;
  border: 1px solid var(--chai-edge) !important; border-radius: 5px;
  padding: 0 5px; font-size: .9em !important; }

/* ---------- hairline cards: dataframe / expander / metric / code ---------- */
[data-testid="stDataFrame"], [data-testid="stExpander"], [data-testid="stMetric"],
[data-testid="stCodeBlock"] pre, [data-testid="stAlert"] {
  border: 1px solid var(--chai-edge) !important;
  border-radius: 14px !important;
  background: var(--chai-card) !important;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  box-shadow: none !important;
  transition: border-color .3s !important; }
[data-testid="stDataFrame"]:hover, [data-testid="stExpander"]:hover,
[data-testid="stMetric"]:hover { border-color: var(--chai-edge-hover) !important; }
[data-testid="stExpander"] { overflow: hidden; }
summary { color: var(--chai-text) !important; }
[data-testid="stCodeBlock"] code { color: #e7d7b8 !important;
  background: transparent !important; border: none !important; }

/* ---------- metric tiles ---------- */
[data-testid="stMetric"] { padding: 14px 16px; }
[data-testid="stMetricValue"] { color: #ffffff !important;
  font-family: 'Montserrat', 'Manrope', sans-serif !important;
  font-variant-numeric: tabular-nums; font-weight: 600; }
[data-testid="stMetricLabel"] { color: var(--chai-muted) !important;
  font-size: 11px !important; letter-spacing: .04em; }

/* ---------- buttons: solid = white, asymmetric corners ---------- */
[data-testid="stBaseButton-primary"], [data-testid="stDownloadButton"] > button {
  background: #f5f5f4 !important; color: #0a0a0a !important;
  border: none !important; border-radius: 0 10px 0 10px !important;
  font-weight: 600 !important; padding: 8px 16px !important;
  font-family: 'Manrope', sans-serif !important;
  transition: transform .2s cubic-bezier(.34,1.4,.64,1), background .2s !important; }
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stDownloadButton"] > button:hover {
  background: #e4e4e2 !important; transform: translateY(-2px); }
[data-testid="stButton"] > button {
  background: transparent !important; border: 1px solid var(--chai-edge) !important;
  color: var(--chai-text) !important; border-radius: 10px 0 10px 0 !important;
  font-weight: 500 !important; transition: border-color .25s !important; }
[data-testid="stButton"] > button:hover { border-color: var(--chai-edge-hover) !important; }

/* ---------- inputs ---------- */
input, textarea, select { caret-color: var(--chai-hi) !important;
  color: var(--chai-text) !important; }
[data-baseweb="select"] > div, .stSelectbox > div > div,
[data-testid="stMultiSelect"] > div {
  background: #141414 !important; border-color: var(--chai-edge) !important;
  border-radius: 10px !important; }
[data-baseweb="popover"], [data-baseweb="menu"] {
  background: #141414 !important; border: 1px solid var(--chai-edge) !important; }
[data-testid="stSlider"] [role="slider"] { background: var(--chai-hi) !important; }
[data-testid="stSlider"] div[data-testid="stSliderTrack"] {
  background: var(--chai-edge) !important; }

/* ---------- captions read as quiet labels ---------- */
[data-testid="stCaptionContainer"] { color: var(--chai-muted) !important;
  font-size: 12.5px !important; }

/* ---------- scrollbars ---------- */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2b2b2b; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a3a; }

/* ---------- footer hairline (orange allowed once, at 10%) ---------- */
.chai-footer { position:relative; margin-top:48px; padding-top:18px;
  text-align:center; color:var(--chai-muted); font-size:12px;
  font-family:'Montserrat',sans-serif; }
.chai-footer::before { content:''; position:absolute; top:0; left:50%;
  transform:translateX(-50%); width:min(90%,900px); height:1px;
  background:#fbbf24; opacity:.10;
  mask-image:linear-gradient(90deg,transparent,#000 40%,#000 60%,transparent); }

@keyframes chaiRise { from { opacity: 0; transform: translateY(14px); } }

@media (prefers-reduced-motion: reduce) {
  [data-testid="stMainBlock"] > div, .kpi-root, .kpi-value,
  .kpi-spark path, .pill { animation: none !important;
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
    icon: str = "◈",
) -> str:
    """ChaiUI stat card — hairline, blurred, cream accent, count-up value.

    accent is kept as a name for call sites but maps to the restrained
    ChaiUI palette: text is near-white, deltas use green/red text only,
    and a single cream edge glint marks the card. No filled colours.
    """
    uid = f"kpi{next(_ids)}"
    color = {"blue": "#00d9ff", "red": "#ff237c", "violet": "#ad57ff", "green": "#00efb2", "orange": "#ffb53d"}.get(accent, "#00d9ff")
    # ChaiUI keeps one quiet accent — highlight cream — plus green/red text
    # for meaning. 'accent' only shifts the top-edge glint.
    glint = {
        "blue": "linear-gradient(90deg,rgba(255,231,194,.0),rgba(255,231,194,.5),rgba(255,231,194,0))",
        "violet": "linear-gradient(90deg,rgba(167,139,250,0),rgba(167,139,250,.5),rgba(167,139,250,0))",
        "orange": "linear-gradient(90deg,rgba(251,191,36,0),rgba(251,191,36,.45),rgba(251,191,36,0))",
        "red": "linear-gradient(90deg,rgba(248,113,113,0),rgba(248,113,113,.45),rgba(248,113,113,0))",
    }.get(accent, "linear-gradient(90deg,rgba(255,231,194,0),rgba(255,231,194,.5),rgba(255,231,194,0))")

    d_html = ""
    if delta:
        good = "#34d399" if delta_good else "#f87171"
        d_html = (
            f'<div class="kpi-delta" style="color:{good}">{html.escape(delta)}</div>'
        )

    spark_html = ""
    if spark and len(spark) >= 2:
        w, h = 120, 28
        vmin, vmax = min(spark), max(spark)
        rng = (vmax - vmin) or 1.0
        pts = " ".join(
            f"{i * (w - 8) / (len(spark) - 1) + 4:.1f},"
            f"{h - 3 - (v - vmin) / rng * (h - 8):.1f}"
            for i, v in enumerate(spark)
        )
        lx, ly = pts.split()[-1].split(",")
        spark_html = f"""
        <svg class="kpi-spark" width="{w}" height="{h}" aria-hidden="true">
          <path d="M{pts}" fill="none" stroke="#00d9ff" stroke-width="1.75"
                stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="{lx}" cy="{ly}" r="3" fill="#00d9ff" stroke="#0a0a0a" stroke-width="1.5"/>
        </svg>"""

    return f"""<!DOCTYPE html><html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:transparent; font-family:'Manrope',system-ui,sans-serif; }}
.kpi-root {{
  border-radius: 11px; padding: 16px 12px 12px 66px; min-height:108px;
  background: linear-gradient(125deg,#111116,#08080c);
  border: 1px solid #29383e;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  box-shadow: inset 0 0 16px #168eff08;
  animation: rise .45s cubic-bezier(.22,1,.36,1) backwards;
  transition: border-color .3s, transform .3s;
  position: relative; overflow: hidden;
}}
.kpi-root::before {{ content:''; position:absolute; top:0; left:0; right:0;
  height:1px; background: {glint}; }}
.kpi-root:hover {{ border-color: rgba(255,247,237,.30); transform: translateY(-2px); }}
.kpi-label {{ font-size: 11px; font-weight: 500; letter-spacing: .02em;
  color: #d5d8e5; }}
.kpi-icon {{position:absolute;left:12px;top:16px;width:43px;height:43px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;color:white;background:radial-gradient(circle at 35% 20%,{color},#08080c);border:1px solid {color};box-shadow:0 0 15px {color}55}}
.kpi-value {{ font-size: clamp(20px,2.1vw,28px); font-weight: 700; color: #ffffff;
  line-height: 1.15; margin: 4px 0 2px; font-variant-numeric: tabular-nums;
  font-family: 'Montserrat', 'Manrope', sans-serif; }}
.kpi-delta {{ font-size: 10px; font-weight: 500;
  font-family: 'Manrope', sans-serif; }}
.kpi-spark path {{ stroke-dasharray: 300; stroke-dashoffset: 300;
  animation: draw 1.1s cubic-bezier(.4,0,.2,1) .4s forwards; }}
.kpi-spark circle {{ animation: fadein .4s ease-out 1.3s backwards; }}
@keyframes rise {{ from {{ opacity:0; transform: translateY(12px); }} }}
@keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
@keyframes fadein {{ from {{ opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{
  .kpi-root, .kpi-value, .kpi-spark path, .kpi-spark circle {{
    animation: none !important; transition: none !important; }}
  .kpi-spark path {{ stroke-dashoffset: 0; }}
}}
</style></head><body>
<div class="kpi-root">
  <div class="kpi-icon" aria-hidden="true">{html.escape(icon)}</div>
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
  var dur = 850, t0 = null;
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


def status_badges(items: list[tuple[str, str]]) -> str:
    """Quiet mono labels in the ChaiUI voice — thin hairline chips, no fills.

    items: [(text, variant)] variant in ok|warn|err|neutral|cyan.
    Colour lives only in the text, never as a filled pill.
    """
    colors = {
        "ok": "#34d399",
        "warn": "#fbbf24",
        "err": "#f87171",
        "neutral": "#a3a3a3",
        "cyan": "#00d9ff",
    }
    pills = ""
    for text, variant in items:
        c = colors.get(variant, colors["neutral"])
        pills += (
            f'<span class="pill" style="color:{c}">{html.escape(text)}</span>'
        )
    return (
        '<!DOCTYPE html><html><head><style>'
        "body{margin:0;background:transparent}"
        ".pills{display:flex;gap:10px;flex-wrap:wrap;align-items:center;"
        "font-family:'Geist Mono',ui-monospace,monospace;font-size:11.5px;"
        "letter-spacing:.03em}"
        ".pill{padding:3px 11px;border-radius:999px;"
        "border:1px solid rgba(255,247,237,.15);font-weight:500;"
        "animation:rise .4s cubic-bezier(.22,1,.36,1) backwards}"
        ".pill:nth-child(2){animation-delay:.05s}.pill:nth-child(3){animation-delay:.10s}"
        ".pill:nth-child(4){animation-delay:.15s}.pill:nth-child(5){animation-delay:.20s}"
        "@keyframes rise{from{opacity:0;transform:translateY(6px)}}"
        "@media (prefers-reduced-motion:reduce){.pill{animation:none}}"
        "</style></head><body>"
        f'<div class="pills">{pills}</div>'
        "</body></html>"
    )
