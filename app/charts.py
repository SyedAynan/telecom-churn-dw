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
body { background: transparent; }
.viz-root { position: relative; font-family: 'Space Grotesk', system-ui,
  -apple-system, 'Segoe UI', sans-serif; padding: 16px 14px 10px;
  animation: rise .5s cubic-bezier(.22,1,.36,1) backwards; }
.viz-root .title { font-size: 14px; font-weight: 700; color: #0b0b0b; }
.viz-root .sub { font-size: 12px; color: #898781; margin: 3px 0 12px; }
svg { display: block; }
text.cat { font-size: 12.5px; fill: #52514e; }
text.val { font-size: 12.5px; fill: #0b0b0b; font-weight: 600;
  font-variant-numeric: tabular-nums;
  animation: fadein .45s ease-out backwards;
  animation-delay: calc(var(--i, 0) * 90ms + .55s); }
rect.track { fill: #eceae4; opacity: .55; }
rect.fill { fill: var(--s); transform-box: fill-box;
  transform-origin: left center;
  animation: grow .7s cubic-bezier(.22,1,.36,1) backwards;
  animation-delay: calc(var(--i, 0) * 90ms);
  transition: transform .25s cubic-bezier(.34,1.56,.64,1), filter .2s; }
rect.fill.neg { transform-origin: right center; }
.bar-row { cursor: default; }
.bar-row:hover text.cat, .bar-row:focus-visible text.cat { fill: #0b0b0b; }
.bar-row:hover rect.fill, .bar-row:focus-visible rect.fill {
  transform: scaleY(1.07); filter: brightness(1.06); }
.bar-row:focus { outline: none; }
.line-zero { stroke: #e1e0d9; stroke-width: 1; }
.slot-1 { --s: #2a78d6; --sd: #3987e5; }
.slot-2 { --s: #eb6834; --sd: #d95926; }
.slot-3 { --s: #1baf7a; --sd: #199e70; }
rect.fill.dim { fill: #b9b8b1; }
.chart-coef rect.fill.pos { fill: #eb6834; }
.chart-coef rect.fill.neg { fill: #2a78d6; }
.tip { position: absolute; pointer-events: none; background: #fcfcfb;
  color: #0b0b0b; border: 1px solid rgba(11,11,11,.10); border-radius: 8px;
  padding: 6px 10px; font-size: 12px; display: none;
  box-shadow: 0 6px 18px rgba(0,0,0,.14); white-space: nowrap; z-index: 5; }
.tip b { font-weight: 700; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } }
@keyframes grow { from { transform: scaleX(0); } }
@keyframes fadein { from { opacity: 0; } }
@media (prefers-color-scheme: dark) {
  .viz-root .title { color: #ffffff; }
  text.cat { fill: #c3c2b7; }
  text.val { fill: #ffffff; }
  rect.track { fill: #26262a; opacity: .9; }
  rect.fill { fill: var(--sd); }
  rect.fill.dim { fill: #4a4a48; }
  .chart-coef rect.fill.pos { fill: #d95926; }
  .chart-coef rect.fill.neg { fill: #3987e5; }
  .line-zero { stroke: #2c2c2a; }
  .tip { background: #262625; color: #ffffff;
    border-color: rgba(255,255,255,.14); }
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
