"""Responsive animated HTML/SVG charts for the Streamlit dashboard.

Layout is JS-driven: each chart measures its container and re-renders on
resize, so marks never clip and text never scales out of spec. Entrance
animations (staggered bar growth) and hover micro-interactions are chrome
only — the dataviz contract is preserved: validated palette slots, thin
marks (22px) with 4px rounded data-ends, hairline solid grids, per-mark
tooltips with keyboard parity, selective direct labels, text in ink
tokens, and dark mode via prefers-color-scheme (color lives in CSS
classes, so no JS color swapping).
"""
from __future__ import annotations

import html
import itertools
import json
from string import Template
from typing import Sequence

_ids = itertools.count(1)

_FONTS = (
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:'
    'wght@500;600;700&display=swap" rel="stylesheet">'
)

_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: transparent; font-family: 'Manrope', system-ui, sans-serif; }
.viz-root { position: relative; padding: 16px 14px 10px;
  background: linear-gradient(125deg,#111116,#08080c); border: 1px solid #29383e;
  border-radius: 14px; backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: rise .5s cubic-bezier(.22,1,.36,1) backwards;
  transition: border-color .3s; }
.viz-root:hover { border-color: #3781b5; }
.viz-root .title { font-size: 13.5px; font-weight: 600; color: #f5f5f4;
  letter-spacing: -0.01em; font-family: 'Montserrat','Manrope',sans-serif; }
.viz-root .sub { font-size: 11.5px; color: #a3a3a3; margin: 3px 0 12px;
  font-family: 'Geist Mono', ui-monospace, monospace; }
svg { display: block; }
text.cat { font-size: 12px; fill: #d4d4d8; }
text.val { font-size: 12px; fill: #f5f5f4; font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-family: 'Geist Mono', ui-monospace, monospace;
  animation: fadein .45s ease-out backwards;
  animation-delay: calc(var(--i, 0) * 90ms + .55s); }
rect.track { fill: #1b1b25; opacity: .9; }
rect.fill { fill: var(--s); transform-box: fill-box;
  transform-origin: left center;
  animation: grow .7s cubic-bezier(.22,1,.36,1) backwards;
  animation-delay: calc(var(--i, 0) * 90ms);
  transition: transform .25s cubic-bezier(.34,1.56,.64,1), opacity .2s; }
rect.fill.neg { transform-origin: right center; }
.bar-row { cursor: default; }
.bar-row:hover text.cat, .bar-row:focus-visible text.cat { fill: #ffffff; }
.bar-row:hover rect.fill, .bar-row:focus-visible rect.fill {
  transform: scaleY(1.06); opacity: .85; }
.bar-row:focus { outline: none; }
.line-zero { stroke: #2b2b2b; stroke-width: 1; }
/* time-series (line) chart */
line.grid { stroke: #1e1e1e; stroke-width: 1; }
path.line { fill: none; stroke: var(--s); stroke-width: 2;
  stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 1200; stroke-dashoffset: 1200;
  animation: draw 1.1s cubic-bezier(.4,0,.2,1) .15s forwards; }
path.area { fill: var(--s); opacity: .09;
  animation: fadein .8s ease-out .3s backwards; }
circle.dot { fill: var(--s); stroke: #0a0a0a; stroke-width: 1.5;
  animation: fadein .4s ease-out 1.2s backwards; }
text.tick { font-size: 11px; fill: #737373; font-variant-numeric: tabular-nums;
  font-family: 'Geist Mono', ui-monospace, monospace; }
text.val-end { font-size: 12px; fill: #f5f5f4; font-weight: 600;
  font-variant-numeric: tabular-nums;
  animation: fadein .5s ease-out 1.1s backwards; }
/* ChaiUI restraint: one cream accent + meaning in muted tints, no fills */
.slot-1 { --s: #00d9ff; }
.slot-2 { --s: #ad57ff; }
.slot-3 { --s: #00efb2; }
rect.fill.dim { fill: #3a3a3a; }
.chart-coef rect.fill.pos { fill: #f87171; }
.chart-coef rect.fill.neg { fill: #34d399; }
.tip { position: absolute; pointer-events: none; background: #111116;
  color: #f5f5f4; border: 1px solid rgba(255,247,237,.2); border-radius: 10px;
  padding: 6px 10px; font-size: 12px; display: none;
  box-shadow: 0 8px 22px rgba(0,0,0,.5); white-space: nowrap; z-index: 5; }
.tip b { font-weight: 700; color: #00d9ff; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } }
@keyframes grow { from { transform: scaleX(0); } }
@keyframes fadein { from { opacity: 0; } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) {
  .viz-root, rect.fill, text.val, path.line, path.area, circle.dot,
  text.val-end { animation: none !important; }
  path.line { stroke-dashoffset: 0; }
}
"""

_JS_HBAR = """
(function () {
  var root = document.currentScript.closest('.viz-root');
  var data = JSON.parse(document.getElementById(root.getAttribute('data-src')).textContent);
  var NS = 'http://www.w3.org/2000/svg';
  var svg = root.querySelector('svg');
  var tip = root.querySelector('.tip');

  function E(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    return e;
  }

  function build() {
    var W = Math.max(340, root.clientWidth - 28);
    var gut = Math.min(190, Math.max(118, W * 0.22));
    var vw = 80;
    var pw = Math.max(80, W - gut - vw - 8);
    var rowH = 34, top = 10, n = data.cats.length;
    var H = n * rowH + top + 4;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', H);
    while (svg.firstChild) { svg.removeChild(svg.firstChild); }
    var vmax = Math.max.apply(null, data.vals.concat([1e-9]));
    for (var i = 0; i < n; i++) {
      var g = E('g', { 'class': 'bar-row', 'tabindex': 0 });
      g.setAttribute('data-cat', data.cats[i]);
      g.setAttribute('data-val', data.fvals[i]);
      g.style.setProperty('--i', i);
      var y = top + i * rowH;
      var by = y + rowH / 2 - 11;
      var t = E('text', { 'class': 'cat', 'text-anchor': 'end',
        x: gut - 10, y: y + rowH / 2 + 4 });
      t.textContent = data.cats[i];
      g.appendChild(t);
      g.appendChild(E('rect', { 'class': 'track', x: gut, y: by,
        width: pw, height: 22, rx: 4 }));
      var bw = Math.max(2, data.vals[i] / vmax * pw);
      var cls = 'fill' + (data.hl && data.vals[i] < vmax ? ' dim' : '');
      g.appendChild(E('rect', { 'class': cls, x: gut, y: by,
        width: bw.toFixed(1), height: 22, rx: 4 }));
      var v = E('text', { 'class': 'val',
        x: (gut + bw + 8).toFixed(1), y: y + rowH / 2 + 4 });
      v.textContent = data.fvals[i];
      g.appendChild(v);
      svg.appendChild(g);
    }
  }

  build();
  var rt = null;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(build, 160);
  });

  function show(row) {
    tip.textContent = '';
    var b1 = document.createElement('b');
    b1.textContent = row.getAttribute('data-cat');
    var b2 = document.createElement('b');
    b2.textContent = row.getAttribute('data-val');
    tip.appendChild(b1);
    tip.appendChild(document.createTextNode(' — '));
    tip.appendChild(b2);
    tip.style.display = 'block';
    var rg = root.getBoundingClientRect(), gg = row.getBoundingClientRect();
    tip.style.left = Math.max(4, Math.min(rg.width - 150,
      gg.left - rg.left + 6)) + 'px';
    tip.style.top = Math.max(2, gg.top - rg.top - 32) + 'px';
  }
  root.addEventListener('pointerover', function (e) {
    var r = e.target.closest('.bar-row');
    if (r) { show(r); }
  });
  root.addEventListener('pointerout', function (e) {
    if (e.target.closest('.bar-row')) { tip.style.display = 'none'; }
  });
  root.addEventListener('focusin', function (e) {
    var r = e.target.closest('.bar-row');
    if (r) { show(r); }
  });
  root.addEventListener('focusout', function () { tip.style.display = 'none'; });
})();
"""

_JS_COEF = """
(function () {
  var root = document.currentScript.closest('.viz-root');
  var data = JSON.parse(document.getElementById(root.getAttribute('data-src')).textContent);
  var NS = 'http://www.w3.org/2000/svg';
  var svg = root.querySelector('svg');
  var tip = root.querySelector('.tip');

  function E(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    return e;
  }

  function build() {
    var W = Math.max(380, root.clientWidth - 28);
    var gut = Math.min(230, Math.max(132, W * 0.30));
    var vw = 64;
    var pw = Math.max(120, W - gut - vw - 8);
    var mid = gut + pw / 2;
    var rowH = 34, top = 10, n = data.cats.length;
    var H = n * rowH + top + 4;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', H);
    while (svg.firstChild) { svg.removeChild(svg.firstChild); }
    var vmax = Math.max.apply(null, data.coefs.map(Math.abs).concat([1e-9]));
    for (var i = 0; i < n; i++) {
      var c = data.coefs[i];
      var g = E('g', { 'class': 'bar-row', 'tabindex': 0 });
      g.setAttribute('data-cat', data.cats[i]);
      g.setAttribute('data-val', data.fvals[i]);
      g.style.setProperty('--i', i);
      var y = top + i * rowH;
      var by = y + rowH / 2 - 11;
      var t = E('text', { 'class': 'cat', 'text-anchor': 'end',
        x: gut - 10, y: y + rowH / 2 + 4 });
      t.textContent = data.cats[i];
      g.appendChild(t);
      g.appendChild(E('line', { 'class': 'line-zero', x1: mid, y1: y + 3,
        x2: mid, y2: y + rowH - 3 }));
      var w = Math.max(2, Math.abs(c) / vmax * (pw / 2 - 8));
      var x = c >= 0 ? mid : mid - w;
      var cls = c >= 0 ? 'fill pos' : 'fill neg';
      g.appendChild(E('rect', { 'class': cls, x: x.toFixed(1), y: by,
        width: w.toFixed(1), height: 22, rx: 4 }));
      var vx = c >= 0 ? mid + w + 8 : mid - w - 8;
      var anchor = c >= 0 ? 'start' : 'end';
      var v = E('text', { 'class': 'val', 'text-anchor': anchor,
        x: vx.toFixed(1), y: y + rowH / 2 + 4 });
      v.textContent = data.fvals[i];
      g.appendChild(v);
      svg.appendChild(g);
    }
  }

  build();
  var rt = null;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(build, 160);
  });

  function show(row) {
    tip.textContent = '';
    var b1 = document.createElement('b');
    b1.textContent = row.getAttribute('data-cat');
    var b2 = document.createElement('b');
    b2.textContent = row.getAttribute('data-val');
    tip.appendChild(b1);
    tip.appendChild(document.createTextNode(' — '));
    tip.appendChild(b2);
    tip.style.display = 'block';
    var rg = root.getBoundingClientRect(), gg = row.getBoundingClientRect();
    tip.style.left = Math.max(4, Math.min(rg.width - 150,
      gg.left - rg.left + 6)) + 'px';
    tip.style.top = Math.max(2, gg.top - rg.top - 32) + 'px';
  }
  root.addEventListener('pointerover', function (e) {
    var r = e.target.closest('.bar-row');
    if (r) { show(r); }
  });
  root.addEventListener('pointerout', function (e) {
    if (e.target.closest('.bar-row')) { tip.style.display = 'none'; }
  });
  root.addEventListener('focusin', function (e) {
    var r = e.target.closest('.bar-row');
    if (r) { show(r); }
  });
  root.addEventListener('focusout', function () { tip.style.display = 'none'; });
})();
"""

_JS_LINE = """
(function () {
  var root = document.currentScript.closest('.viz-root');
  var data = JSON.parse(document.getElementById(root.getAttribute('data-src')).textContent);
  var NS = 'http://www.w3.org/2000/svg';
  var svg = root.querySelector('svg');

  function E(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    return e;
  }

  function build() {
    var W = Math.max(320, root.clientWidth - 28);
    var H = data.height;
    var padL = 52, padR = 16, padT = 14, padB = 26;
    var iw = W - padL - padR, ih = H - padT - padB;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', H);
    while (svg.firstChild) { svg.removeChild(svg.firstChild); }

    var n = data.vals.length;
    var lo = Math.max(Math.min.apply(null, data.vals.concat([data.ymin])), data.ymin);
    var hi = Math.min(Math.max.apply(null, data.vals.concat([data.ymax])), data.ymax);
    if (hi === lo) { hi = lo + 1; }
    function X(i) { return padL + (n <= 1 ? iw / 2 : i * iw / (n - 1)); }
    function Y(v) { return padT + ih - (v - lo) / (hi - lo) * ih; }

    // horizontal grid + y ticks
    var ticks = 4;
    for (var t = 0; t <= ticks; t++) {
      var v = lo + (hi - lo) * t / ticks;
      var yy = Y(v);
      svg.appendChild(E('line', { 'class': 'grid', x1: padL, y1: yy,
        x2: W - padR, y2: yy }));
      var lab = E('text', { 'class': 'tick', x: padL - 8, y: yy + 4,
        'text-anchor': 'end' });
      lab.textContent = data.yfmt(v);
      svg.appendChild(lab);
    }

    // area + line
    var d = '', dArea = '';
    for (var i = 0; i < n; i++) {
      var x = X(i).toFixed(1), y = Y(data.vals[i]).toFixed(1);
      d += (i ? 'L' : 'M') + x + ',' + y;
      dArea += (i ? 'L' : 'M') + x + ',' + y;
    }
    dArea += 'L' + X(n - 1).toFixed(1) + ',' + (padT + ih) +
             'L' + X(0).toFixed(1) + ',' + (padT + ih) + 'Z';
    svg.appendChild(E('path', { 'class': 'area', d: dArea }));
    svg.appendChild(E('path', { 'class': 'line', d: d }));

    // last-point marker + end label
    if (n > 0) {
      svg.appendChild(E('circle', { 'class': 'dot', cx: X(n - 1).toFixed(1),
        cy: Y(data.vals[n - 1]).toFixed(1), r: 4 }));
      var last = E('text', { 'class': 'val-end',
        x: Math.max(padL + 4, X(n - 1).toFixed(1) - 6),
        y: Math.max(padT + 12, Y(data.vals[n - 1]) - 10), 'text-anchor': 'end' });
      last.textContent = data.fvals[n - 1];
      svg.appendChild(last);
    }

    // x labels: first, middle, last
    if (n > 1) {
      var idx = [0, Math.floor((n - 1) / 2), n - 1];
      for (var k = 0; k < idx.length; k++) {
        var xl = E('text', { 'class': 'tick', x: X(idx[k]).toFixed(1),
          y: H - 8, 'text-anchor': k === 0 ? 'start' : (k === 2 ? 'end' : 'middle') });
        xl.textContent = data.xlabels[idx[k]];
        svg.appendChild(xl);
      }
    }
  }

  build();
  var rt = null;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(build, 160);
  });
})();
"""

_TMPL = Template(
    """<!DOCTYPE html><html><head>
$fonts
<style>$css</style></head>
<body>
<div class="viz-root $rclass $slotcls" data-src="$src" data-root>
  <div class="title">$title</div>
  $subhtml
  <svg role="img" aria-label="$aria"></svg>
  <div class="tip"></div>
</div>
<script type="application/json" id="$src">$json</script>
<script>$js</script>
</body></html>"""
)


def _render(uid, data, title, subtitle, *, rclass, slotcls, js, aria):
    j = json.dumps(data).replace("</", "<\\/")
    sub = f'<div class="sub">{html.escape(subtitle)}</div>' if subtitle else ""
    return _TMPL.substitute(
        fonts=_FONTS, css=_CSS, rclass=rclass, slotcls=slotcls, src=uid,
        title=html.escape(title), subhtml=sub, aria=html.escape(aria),
        json=j, js=js,
    )


def chart_height(n_rows: int, has_subtitle: bool = False) -> int:
    """Pixel height for a components.html slot holding an n-row chart."""
    return n_rows * 34 + 84 + (36 if has_subtitle else 0)


def hbar_chart(
    title: str,
    categories: Sequence[str],
    values: Sequence[float],
    *,
    value_fmt: str = "{:.1%}",
    color_slot: int = 0,
    highlight_max: bool = True,
    subtitle: str = "",
) -> str:
    """Horizontal bar chart — one series, magnitude comparison.

    Bars <=24px with 4px rounded data-ends, staggered grow-in animation,
    value labels at bar tips (ink color), per-bar hover tooltip + lift,
    hairline track. highlight_max keeps the maximum bar in the series hue
    and de-emphasizes the rest toward gray (emphasis form); False = uniform
    slot coloring.
    """
    uid = f"vd{next(_ids)}"
    data = {
        "cats": [str(c) for c in categories],
        "vals": [float(v) for v in values],
        "fvals": [value_fmt.format(float(v)) for v in values],
        "hl": bool(highlight_max),
    }
    return _render(
        uid, data, title, subtitle,
        rclass="chart-hbar", slotcls=f"slot-{color_slot + 1}",
        js=_JS_HBAR, aria=f"{title} — horizontal bar chart",
    )


def coefficient_chart(
    title: str,
    features: Sequence[str],
    coefs: Sequence[float],
    *,
    subtitle: str = "",
) -> str:
    """Diverging horizontal bar chart of model coefficients (polarity job).

    Churn-up bars in orange, protective in blue — the validated warm/cool
    pair with the zero line as neutral midpoint. Bars grow outward from
    the zero line on entrance.
    """
    uid = f"vd{next(_ids)}"
    data = {
        "cats": [str(f) for f in features],
        "coefs": [float(c) for c in coefs],
        "fvals": [f"{float(c):+.2f}" for c in coefs],
    }
    return _render(
        uid, data, title, subtitle,
        rclass="chart-coef", slotcls="",
        js=_JS_COEF, aria=f"{title} — diverging bar chart",
    )


def donut_chart(
    title: str,
    labels: Sequence[str],
    values: Sequence[float],
    *,
    colors: Sequence[str] | None = None,
    value_fmt: str = "{:.1%}",
    subtitle: str = "",
) -> str:
    """ChaiUI-style doughnut — hairline segments, no filled bars.

    Segments are drawn as rings with per-slice colour from the palette; the
    centre shows total + share. Colour is meaning (contract/operator), not
    decoration. Sizes stay proportional; the legend is rendered inside the
    same card so hover+click stay in one surface.
    """
    uid = f"vd{next(_ids)}"
    vals = [float(v) for v in values]
    total = sum(vals) or 1.0
    data = {
        "cats": [str(c) for c in labels],
        "vals": vals,
        "fvals": [value_fmt.format(v) for v in vals],
        "total": total,
        "height": 200,
        "colors": list(colors) if colors else [],
    }
    js = _JS_DONUT
    return _render(
        uid, data, title, subtitle,
        rclass="chart-donut", slotcls="",
        js=js, aria=f"{title} — doughnut chart",
    )


def combo_chart(
    title: str,
    labels: Sequence[str],
    series: Sequence[dict],
    *,
    volume_label: str = "Customers",
    rate_label: str = "Churn rate",
    subtitle: str = "",
) -> str:
    """Dual-axis combo: volume bars + rate line per operator.

    series: [{"name":"Airtel","color":"#e40000","volume":[..],"rate":[..]}]
    Volume stacks as bars (left axis), rate overlays as lines (right axis).
    Legend is inline in the card. All values come from the live mart.
    """
    uid = f"vd{next(_ids)}"
    data = {
        "labels": [str(x) for x in labels],
        "series": [{
            "name": s["name"], "color": s["color"],
            "volume": [float(v) for v in s["volume"]],
            "rate": [float(r) for r in s["rate"]],
        } for s in series],
        "volume_label": volume_label,
        "rate_label": rate_label,
        "height": 240,
    }
    return _render(
        uid, data, title, subtitle,
        rclass="chart-combo", slotcls="",
        js=_JS_COMBO, aria=f"{title} — combo chart",
    )


def line_chart(
    title: str,
    labels: Sequence[str],
    values: Sequence[float],
    *,
    value_fmt: str = "{:.1%}",
    yfmt: str = "{:.1%}",
    ymin: float | None = None,
    ymax: float | None = None,
    color_slot: int = 0,
    subtitle: str = "",
) -> str:
    """Responsive time-series line chart with a subtle area fill."""
    uid = f"vd{next(_ids)}"
    vals = [float(v) for v in values]
    lo = min(vals) if vals else 0.0
    hi = max(vals) if vals else 1.0
    if ymin is None:
        ymin = lo
    if ymax is None:
        ymax = hi
    if ymax <= ymin:
        ymax = ymin + 1.0
    data = {
        "xlabels": [str(x) for x in labels],
        "vals": vals,
        "fvals": [value_fmt.format(v) for v in vals],
        "ymin": float(ymin),
        "ymax": float(ymax),
        "height": 190,
    }
    # JSON cannot carry a callable; the line chart needs a compact formatter
    # for SVG tick labels, so format common numeric values in the browser.
    data["yfmt"] = "pct" if yfmt == "{:.1%}" else "num"
    return _render(
        uid, data, title, subtitle,
        rclass="chart-line", slotcls=f"slot-{color_slot + 1}",
        js=_JS_LINE.replace(
            "data.yfmt(v)",
            "(data.yfmt === 'pct' ? (v * 100).toFixed(0) + '%' : v.toFixed(1))",
        ),
        aria=f"{title} — line chart",
    )
