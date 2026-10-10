"""Local Iconscout assets and SVG images safe for Streamlit's HTML sanitizer."""
import base64
import html
from pathlib import Path

ICON_DIR = Path(__file__).parent / "assets" / "unicons"


def svg_image(svg: str, *, css_class: str = "", label: str = "") -> str:
    encoded = base64.b64encode(svg.encode()).decode()
    return f'<img class="{html.escape(css_class, quote=True)}" alt="{html.escape(label, quote=True)}" src="data:image/svg+xml;base64,{encoded}"/>'


def icon(name: str, color: str = "#b4b4c5") -> str:
    svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    svg = svg.replace('<path ', f'<path fill="{color}" ')
    return svg_image(svg, css_class="ui-icon")
