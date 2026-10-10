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


@lru_cache(maxsize=8)
def _logo_image(filename: str, css_class: str, label: str) -> str:
    path = PROVIDER_DIR / filename
    encoded = base64.b64encode(path.read_bytes()).decode()
    return (f'<img class="{html.escape(css_class, quote=True)}" alt="{html.escape(label, quote=True)}" '
            f'src="data:image/png;base64,{encoded}"/>')


def app_icon(css_class: str = "ui-icon") -> str:
    """China Telecom signal mark — used as the application icon and brand mark."""
    return _logo_image("telecom-churn.png", css_class, "Telecom Churn")


@lru_cache(maxsize=4)
def provider_logo(name: str) -> str:
    """Iconscout signal-animation previews embedded locally, colours intact."""
    filename = {"Jio": "jio.png", "Vi": "vi.png", "Airtel": "airtel.png", "BSNL": "bsnl.png"}[name]
    return _logo_image(filename, f"provider-logo logo-{name.lower()}", f"{name} logo")


def provider_banner(name: str, state: str) -> str:
    return (f'<div class="provider-artwork artwork-{name.lower()}">'
            f'<div class="provider-logo-plate">{provider_logo(name)}</div>'
            '<span class="provider-orbit" aria-hidden="true"></span></div>'
            f'<div class="provider-caption"><span>{html.escape(name)}</span>'
            f'<small>{html.escape(state)}</small></div>')


def page_heading(title: str, asset: str, eyebrow: str) -> str:
    return (f'<div class="asset-page-heading"><span class="asset-heading-icon">{icon(asset, "#00d9ff")}</span>'
            f'<div><div class="live-eyebrow">{html.escape(eyebrow)}</div><h2>{html.escape(title)}</h2></div></div>')


def empty_state(title: str, detail: str, asset: str = "search") -> str:
    return (f'<div class="live-empty"><span class="empty-asset">{icon(asset, "#00d9ff")}</span>'
            f'<strong>{html.escape(title)}</strong><p>{html.escape(detail)}</p></div>')
