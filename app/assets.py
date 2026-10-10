"""Local Iconscout assets and SVG images safe for Streamlit's HTML sanitizer."""
import base64
import html
from pathlib import Path
from functools import lru_cache

ICON_DIR = Path(__file__).parent / "assets" / "unicons"
PROVIDER_DIR = Path(__file__).parent / "assets" / "providers"


def svg_image(svg: str, *, css_class: str = "", label: str = "") -> str:
    encoded = base64.b64encode(svg.encode()).decode()
    return f'<img class="{html.escape(css_class, quote=True)}" alt="{html.escape(label, quote=True)}" src="data:image/svg+xml;base64,{encoded}"/>'


@lru_cache(maxsize=64)
def icon(name: str, color: str = "#b4b4c5") -> str:
    svg = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    svg = svg.replace('<path ', f'<path fill="{color}" ')
    return svg_image(svg, css_class="ui-icon")


@lru_cache(maxsize=4)
def provider_logo(name: str) -> str:
    """Official artwork embedded locally, with its original colours intact."""
    filename = {"Jio": "jio.png", "Vi": "vi.svg", "Airtel": "airtel.svg", "BSNL": "bsnl.png"}[name]
    path = PROVIDER_DIR / filename
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f'<img class="provider-logo logo-{name.lower()}" alt="{html.escape(name)} logo" src="data:{mime};base64,{encoded}"/>'


def provider_banner(name: str, state: str) -> str:
    return (f'<div class="provider-artwork artwork-{name.lower()}">'
            f'<div class="provider-logo-plate">{provider_logo(name)}</div>'
            '<span class="provider-orbit" aria-hidden="true"></span></div>'
            f'<div class="provider-caption"><span>{html.escape(name)}</span>'
            f'<small>{html.escape(state)}</small></div>')
