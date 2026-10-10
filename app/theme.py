"""Enterprise BI theme — neon black, glass cards, Inter type.

Supersedes the older dark accents in motion.py for the shell chrome; the
kpi_tile / status_badges / chart primitives stay and just get recoloured
through the palette below. One soft glow lives behind the header only —
nowhere else, per the "restrained" brief.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone
from app.assets import icon

# ---- palette --------------------------------------------------------------
NAVY = "#030305"      # app background
PANEL = "#08080c"     # card surface
PANEL2 = "#111116"    # raised surface
EDGE = "rgba(0,217,255,.16)"   # cyan hairline
EDGE_HI = "rgba(0,217,255,.42)"
CYAN = "#00d9ff"
BLUE = "#0074ff"
INDIGO = "#6366f1"
TEXT = "#e8eefc"
MUTED = "#979bad"
GOOD = "#34d399"
BAD = "#f87171"
WARN = "#fbbf24"

AIRTEL = "#e40000"
JIO = "#1e4ed8"
VI = "#f5d000"

FONTS = (
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..800'
    '&family=JetBrains+Mono:wght@400..700&display=swap" rel="stylesheet">'
)

CSS = FONTS + f"""
<style>
:root {{
  --navy:{NAVY}; --panel:{PANEL}; --panel2:{PANEL2};
  --edge:{EDGE}; --edge-hi:{EDGE_HI};
  --cyan:{CYAN}; --blue:{BLUE}; --text:{TEXT}; --muted:{MUTED};
  --good:{GOOD}; --bad:{BAD}; --warn:{WARN};
}}
html,body,.stApp {{ font-family:'Inter',system-ui,sans-serif !important;
  color:var(--text); }}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{{ background:{NAVY}; }}
[data-testid="stHeader"]{{ background:transparent; }}

/* ---- one soft glow behind the header, nowhere else ---- */
[data-testid="stMainBlock"]::before {{ content:''; position:fixed; top:-220px;
  left:50%; transform:translateX(-50%); width:900px; height:420px;
  background:radial-gradient(50% 50% at 50% 0%, rgba(0,217,255,.14), transparent 70%);
  pointer-events:none; z-index:0; }}

/* ---- sidebar ---- */
[data-testid="stSidebar"]{{ background:#070709; border-right:1px solid var(--edge); }}
[data-testid="stSidebar"] *{{ color:var(--text) !important; }}
[data-testid="stSidebar"] .stRadio label{{ padding:8px 12px; border-radius:10px;
  font-weight:500; transition:background .22s,border-color .22s; border:1px solid transparent; }}
[data-testid="stSidebar"] .stRadio label:hover{{ background:rgba(0,217,255,.07);
  border-color:var(--edge); }}
[data-testid="stSidebar"] hr{{ border-color:var(--edge) !important; }}

/* ---- type ---- */
h1{{ font-family:'Inter',sans-serif !important; font-weight:700 !important;
  letter-spacing:-0.02em !important; color:#f4f7ff !important; font-size:28px !important;
  background:none !important; -webkit-text-fill-color:unset !important; }}
h2,h3,h4{{ font-family:'Inter',sans-serif !important; color:var(--text) !important;
  font-weight:600 !important; }}
p,.stMarkdown{{ color:var(--muted) !important; }}
strong{{ color:var(--text); }}
code{{ font-family:'JetBrains Mono',ui-monospace,monospace !important;
  color:{CYAN} !important; background:rgba(0,217,255,.08) !important;
  border:1px solid var(--edge) !important; border-radius:5px; padding:0 5px; }}

/* ---- glass cards ---- */
.glass,[data-testid="stDataFrame"],[data-testid="stExpander"],[data-testid="stMetric"],
[data-testid="stCodeBlock"] pre,[data-testid="stAlert"] {{
  border:1px solid var(--edge) !important; border-radius:14px !important;
  background:linear-gradient(160deg,{PANEL2} 0%,{PANEL} 100%) !important;
  backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px);
  box-shadow:0 0 0 1px rgba(10,17,32,.4), inset 0 1px 0 rgba(255,255,255,.03) !important;
  transition:border-color .25s,transform .25s !important; }}
[data-testid="stDataFrame"]:hover,[data-testid="stExpander"]:hover,
[data-testid="stMetric"]:hover {{ border-color:var(--edge-hi) !important;
  transform:translateY(-1px); }}
[data-testid="stExpander"]{{ overflow:hidden; }}
summary{{ color:var(--text) !important; }}
[data-testid="stCodeBlock"] code{{ color:#9fd8ff !important; background:transparent !important; border:none !important; }}

/* ---- metrics ---- */
[data-testid="stMetric"]{{ padding:14px 16px; }}
[data-testid="stMetricValue"]{{ color:#fff !important; font-variant-numeric:tabular-nums; font-weight:700; }}
[data-testid="stMetricLabel"]{{ color:var(--muted) !important; font-size:11px !important;
  text-transform:uppercase; letter-spacing:.06em; }}

/* ---- buttons ---- */
[data-testid="stBaseButton-primary"],[data-testid="stDownloadButton"] > button{{
  background:linear-gradient(180deg,{CYAN},{BLUE}) !important; color:#041020 !important;
  border:none !important; border-radius:10px !important; font-weight:600 !important;
  padding:9px 18px !important;
  box-shadow:0 4px 16px rgba(0,217,255,.22) !important;
  transition:transform .18s,box-shadow .18s !important; }}
[data-testid="stBaseButton-primary"]:hover,[data-testid="stDownloadButton"] > button:hover{{
  transform:translateY(-2px); box-shadow:0 8px 22px rgba(0,217,255,.34) !important; }}
[data-testid="stButton"] > button{{ background:transparent !important;
  border:1px solid var(--edge) !important; color:var(--text) !important;
  border-radius:10px !important; font-weight:500 !important; }}
[data-testid="stButton"] > button:hover{{ border-color:var(--edge-hi) !important;
  color:{CYAN} !important; }}

/* ---- inputs ---- */
input,textarea,select{{ caret-color:{CYAN} !important; color:var(--text) !important; }}
[data-baseweb="select"] > div,[data-testid="stMultiSelect"] > div,
[data-testid="stTextInput"] input {{ background:{PANEL2} !important;
  border-color:var(--edge) !important; border-radius:10px !important; }}
[data-baseweb="popover"],[data-baseweb="menu"]{{ background:{PANEL2} !important;
  border:1px solid var(--edge) !important; }}
[data-testid="stSlider"] [role="slider"]{{ background:{CYAN} !important; }}
[data-testid="stSlider"] div[data-testid="stSliderTrack"]{{ background:var(--edge) !important; }}

/* ---- misc ---- */
[data-testid="stCaptionContainer"]{{ color:var(--muted) !important; font-size:12.5px !important; }}
::-webkit-scrollbar{{ width:9px;height:9px; }}
::-webkit-scrollbar-track{{ background:{NAVY}; }}
::-webkit-scrollbar-thumb{{ background:#2d3039;border-radius:5px; }}
::-webkit-scrollbar-thumb:hover{{ background:#424754; }}

/* page entrance */
[data-testid="stMainBlock"] > div{{ animation:entRise .5s cubic-bezier(.22,1,.36,1) backwards; }}
[data-testid="stMainBlock"] > div:nth-child(2){{ animation-delay:.06s; }}
[data-testid="stMainBlock"] > div:nth-child(3){{ animation-delay:.12s; }}
[data-testid="stMainBlock"] > div:nth-child(4){{ animation-delay:.18s; }}
[data-testid="stMainBlock"] > div:nth-child(5){{ animation-delay:.24s; }}
@keyframes entRise{{ from{{ opacity:0;transform:translateY(14px); }} }}
@media (prefers-reduced-motion:reduce){{
  [data-testid="stMainBlock"] > div{{ animation:none !important; }}
}}
</style>
"""

CSS += """<style>
[data-testid="stMainBlockContainer"]{padding:1.1rem 1.2rem 2rem;max-width:1900px}
[data-testid="stHeader"]{height:0;background:transparent}
[data-testid="stSidebar"]{width:220px!important;min-width:220px!important;background:#070709}
[data-testid="stSidebarUserContent"]{padding:22px 12px}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]>div{padding-left:12px;padding-right:12px}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding:20px 0}
[data-testid="stVerticalBlock"]{gap:.65rem}
[data-testid="stSidebar"] [role="radiogroup"]{gap:8px}
[data-testid="stSidebar"] [role="radiogroup"] label{width:100%;padding:13px 12px;margin:0;font-size:13px}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#086880,#07252c);box-shadow:0 0 16px #168eff22}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none}
[data-testid="stSidebar"] [role="radiogroup"] label>div[data-baseweb="radio"]{display:none}
[data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:not([data-testid="stMarkdownContainer"]){display:none}
[data-testid="stSidebar"] [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"]{margin-left:0}
[data-testid="stSidebar"] [role="radiogroup"] label{white-space:nowrap}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:13px}
.brand{display:flex;align-items:center;gap:10px;margin:0 4px 24px;color:white;font-weight:700;font-size:16px}
.brand svg{width:40px;flex-shrink:0;color:#00d9ff!important;filter:drop-shadow(0 0 7px #00d9ff88)}
.brand small{display:block;color:#979dad;font-size:10px;margin-top:5px;font-weight:400;letter-spacing:1px}
.bi-header{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;padding:5px 0 18px;border-bottom:1px solid #252d34;margin-bottom:9px}
.bi-header h1{font-size:25px!important;margin:0!important;padding:0!important;letter-spacing:-.7px!important}
.bi-header .subline{font-size:12px;color:#bfc5d2;margin-top:4px}
.bi-header .tagline{font-size:10px;color:#8e96aa;margin-top:7px}
.operators{display:flex;gap:12px;align-items:center}
.operator{display:flex;align-items:center;justify-content:center;border-radius:9px;font-size:24px;font-weight:800;width:74px;height:45px;color:white;box-shadow:0 0 18px #ff265a22}
.operator.airtel{background:linear-gradient(#fa3652,#c90032);font-size:21px;width:99px;font-style:italic}
.operator.jio{background:linear-gradient(#077bff,#0742c7);border-radius:50%;width:48px;height:48px}
.operator.vi{background:linear-gradient(#ff425b,#ba0826)}
.operator-note{font-size:9px;color:#969eaf;margin-top:6px;text-align:center}
.header-status{display:flex;gap:10px}.status-box{border:1px solid #27383e;border-radius:9px;padding:10px 15px;background:#0b0b10;color:#bfc5d2;font-size:10px;min-width:135px;box-shadow:inset 0 0 15px #138cff08}
.status-box strong{display:block;color:#e5effe;font-size:12px;margin-top:5px}.status-box .connected{color:#35dbac}
.sidebar-note{margin-top:26px;padding:14px 9px;border:1px solid #27383e;border-radius:10px;color:#969eaf;font-size:11px;line-height:1.6}
[data-testid="stDownloadButton"] button p{color:white!important}
.chai-footer{border-top:1px solid #25252e;color:#8e96aa;text-align:center;padding-top:15px;margin-top:25px;font-size:11px}
@media(max-width:1100px){.bi-header{gap:12px}.bi-header h1{font-size:21px!important}.status-box{min-width:110px;padding:8px}.operators{gap:7px}}
@media(max-width:640px){[data-testid="stMainBlockContainer"]{padding:1rem .75rem}.bi-header h1{font-size:22px!important}.header-status{width:100%}.status-box{flex:1}}
</style>"""

TOWER = '<svg viewBox="0 0 40 52" fill="none" stroke="currentColor" stroke-width="2.3" aria-hidden="true"><circle cx="20" cy="15" r="3"/><path d="M17 19L9 48M23 19L31 48M12 37L27 43M28 37L13 43M15 28L25 33M25 28L15 33M11 7Q4 15 11 23M29 7Q36 15 29 23M6 2Q-4 15 6 28M34 2Q44 15 34 28"/></svg>'


def dashboard_header() -> str:
    return ('<div class="bi-header"><div class="workspace-mark">' + icon("wifi", "#00d9ff") + '</div><div><h1>Telecom Churn</h1>'
            '<div class="subline">Customer analytics & retention</div></div>'
            '<div class="header-status"><div class="status-box"><span class="workspace-label">'
            + icon("layer-group", "#00d9ff") + 'CONNECTED WORKSPACE</span><strong>4 providers · One view</strong></div></div></div>')


def operator_chip(name: str) -> str:
    """Recognizable operator mark — inline SVG letter badge + brand colour."""
    marks = {
        "Airtel": ("A", AIRTEL, "#fff"),
        "Jio": ("J", JIO, "#fff"),
        "Vi": ("Vi", VI, "#b3001b"),
    }
    letter, bg, fg = marks[name]
    return (
        f'<span style="display:inline-flex;align-items:center;gap:8px;'
        f'padding:4px 12px 4px 4px;border:1px solid var(--edge);border-radius:999px;'
        f'background:{PANEL2};font-family:Inter,sans-serif;font-size:12px;'
        f'font-weight:600;color:{TEXT}">'
        f'<span style="width:24px;height:24px;border-radius:50%;background:{bg};'
        f'color:{fg};display:inline-flex;align-items:center;justify-content:center;'
        f'font-size:11px;font-weight:800;font-family:Inter,sans-serif">{letter}</span>'
        f'{name}</span>'
    )


def header(refresh_ts: str, conn_ok: bool) -> str:
    """Top header bar: title, operator marks, tagline, status."""
    dot = GOOD if conn_ok else BAD
    status = "warehouse connected" if conn_ok else "warehouse offline"
    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
      flex-wrap:wrap;gap:14px;padding:6px 0 4px;margin-bottom:6px">
      <div>
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:22px;font-weight:800;color:#fff;font-family:Inter,sans-serif;letter-spacing:-0.02em">
            Telecom <span style="color:{CYAN}">Churn</span> Warehouse</span>
        </div>
        <div style="font-size:12.5px;color:{MUTED};margin-top:2px">
          Three Networks. One Platform. Complete Customer Insights.</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        {operator_chip("Airtel")}{operator_chip("Jio")}{operator_chip("Vi")}
        <span style="width:1px;height:22px;background:var(--edge);margin:0 4px"></span>
        <span style="display:inline-flex;align-items:center;gap:6px;font-size:11.5px;
          color:{MUTED};font-family:JetBrains Mono,monospace">
          <span style="width:8px;height:8px;border-radius:50%;background:{dot};
            box-shadow:0 0 8px {dot}"></span>{status} · {html.escape(refresh_ts)}
        </span>
      </div>
    </div>"""


def card(body: str, pad: int = 16, top_glint: str | None = None) -> str:
    """Glass card wrapper (used inside components.html)."""
    glint = (f'<div style="position:absolute;top:0;left:0;right:0;height:1px;'
             f'background:{top_glint}"></div>' if top_glint else "")
    return (
        f'<div style="position:relative;border:1px solid var(--edge);'
        f'border-radius:14px;background:linear-gradient(160deg,{PANEL2},{PANEL});'
        f'backdrop-filter:blur(6px);padding:{pad}px;overflow:hidden">'
        f'{glint}{body}</div>'
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
