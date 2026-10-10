"""Discover user-downloaded Iconscout animations and render a stable local player."""
from __future__ import annotations

import base64
from functools import lru_cache
import html
import json
import mimetypes
from pathlib import Path, PurePosixPath
import re
import zipfile

from etl.paths import PROJECT_ROOT

ASSET_DIR = Path(__file__).parent / "assets" / "animations"
PLAYER = ASSET_DIR / "player" / "lottie.min.js"
ASSETS = {"Jio": ("jio", "10697936"), "Airtel": ("airtel", "11825803"),
          "Vi": ("vi", "11625736"), "BSNL": ("bsnl", "10437298"),
          "China Telecom": ("china", "10697921")}
MAX_BYTES = 20 * 1024 * 1024


def _name(path: Path) -> str | None:
    tokens = re.split(r"[^a-z0-9]+", path.stem.lower())
    for provider, (word, identifier) in ASSETS.items():
        if word in tokens or identifier in path.stem:
            return provider
    return None


def _validate(data: dict) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("layers"), list):
        raise ValueError("Not a Lottie animation")
    for key in ("fr", "w", "h"):
        if not 0 < float(data[key]) < 10000:
            raise ValueError("Invalid animation dimensions or frame rate")
    if not float(data["op"]) > float(data["ip"]):
        raise ValueError("Invalid animation duration")
    # Only local, bundled resources; never start network requests from an asset.
    for asset in data.get("assets", []):
        if "p" in asset and not asset["p"].startswith("data:image/"):
            raise ValueError("Missing bundled image")
    if data.get("fonts", {}).get("list"):
        raise ValueError("Export text as shapes to avoid external font dependencies")


@lru_cache(maxsize=32)
def _read(path: Path, modified: int, size: int) -> dict:
    try:
        if size > MAX_BYTES:
            raise ValueError("Oversized animation")
        if path.suffix.lower() in (".mp4", ".webm"):
            content = path.read_bytes()
            if len(content) < 32:
                raise ValueError("Incomplete video")
            if content.startswith(b"\x1aE\xdf\xa3"):
                mime = "video/webm"
            elif content[4:8] == b"ftyp":
                mime = "video/mp4"
            else:
                raise ValueError("Unsupported video")
            return {"media": {"src": f"data:{mime};base64," + base64.b64encode(content).decode()}}
        if path.suffix.lower() in (".lottie", ".zip"):
            with zipfile.ZipFile(path) as archive:
                if sum(info.file_size for info in archive.infolist()) > MAX_BYTES:
                    raise ValueError("Oversized archive")
                names = archive.namelist()
                candidates = [n for n in names if n.endswith(".json") and PurePosixPath(n).name != "manifest.json"]
                if "manifest.json" in names:
                    manifest = json.loads(archive.read("manifest.json"))
                    entries = manifest.get("animations", [])
                    if entries:
                        identifier = entries[0]["id"]
                        preferred = [f"animations/{identifier}.json", f"a/{identifier}.json"]
                        candidates = [n for n in preferred if n in names] + candidates
                data = None
                for candidate in dict.fromkeys(candidates):
                    parsed = json.loads(archive.read(candidate))
                    if isinstance(parsed, dict) and "layers" in parsed:
                        data = parsed
                        break
                if data is None:
                    raise ValueError("No animation in archive")
                for asset in data.get("assets", []):
                    if "p" not in asset or asset["p"].startswith("data:image/"):
                        continue
                    relative = asset.get("u", "") + asset["p"]
                    matches = [n for n in names if n == relative or n == str(PurePosixPath(candidate).parent / relative)]
                    if not matches:
                        matches = [n for n in names if PurePosixPath(n).name == PurePosixPath(relative).name]
                    if len(matches) != 1:
                        raise ValueError("Missing image")
                    mime = mimetypes.guess_type(matches[0])[0] or ""
                    if mime not in ("image/png", "image/jpeg", "image/webp"):
                        raise ValueError("Unsupported image")
                    asset.update(p=f"data:{mime};base64," + base64.b64encode(archive.read(matches[0])).decode(), u="", e=1)
        else:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            for asset in data.get("assets", []):
                if "p" not in asset or asset["p"].startswith("data:image/"):
                    continue
                image_path = (path.parent / asset.get("u", "") / asset["p"]).resolve()
                if not image_path.is_relative_to(path.parent.resolve()) or image_path.stat().st_size > MAX_BYTES:
                    raise ValueError("Invalid image path or size")
                mime = mimetypes.guess_type(image_path.name)[0] or ""
                if mime not in ("image/png", "image/jpeg", "image/webp"):
                    raise ValueError("Unsupported image")
                asset.update(p=f"data:{mime};base64," + base64.b64encode(image_path.read_bytes()).decode(), u="", e=1)
        _validate(data)
        return data
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile):
        # Exceptions are not cached: retry when a companion image finishes copying.
        raise ValueError("Incomplete or unsupported animation") from None


def discover(root: Path = PROJECT_ROOT) -> dict[str, dict]:
    """Scan the drop locations only, not the virtualenv, repository, or database."""
    found = {}
    for directory in (root, root / "assets" / "animations", root / "app" / "assets" / "animations"):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.suffix.lower() not in (".json", ".lottie", ".zip", ".mp4", ".webm"):
                continue
            provider = _name(path)
            if provider is None:
                continue
            try:
                stat = path.stat()
                data = _read(path, stat.st_mtime_ns, stat.st_size)
            except (OSError, ValueError):
                continue
            if provider not in found or "media" not in data:
                found[provider] = data
    return {name: found[name] for name in ASSETS if name in found}


def gallery(animations: dict[str, dict]) -> str:
    """Stable iframe outside the one-second data fragment; no external scripts."""
    cards = ''.join(f'<article><div id="animation-{i}" class="animation" role="img" aria-label="{html.escape(name)} animation"></div><span>{html.escape(name)}{" · illustration" if name == "China Telecom" else ""}</span></article>' for i, name in enumerate(animations))
    payload = json.dumps(list(animations.values())).replace("<", "\\u003c")
    runtime = PLAYER.read_text(encoding="utf-8") if any("media" not in data for data in animations.values()) else ""
    return '''<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;background:#060608;color:#e6e8f1;font:12px system-ui,sans-serif}
header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}header span{color:#959bac;font-size:10px}
button{background:#12141d;border:1px solid #00d9ff40;border-radius:7px;color:#ccecf4;padding:7px 12px;cursor:pointer}button:focus-visible{outline:2px solid #00d9ff}
.gallery{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px;scrollbar-color:#37404b #101116}article{flex:1;min-width:145px;border:1px solid #ffffff18;background:#101116;border-radius:12px;overflow:hidden}
.animation{height:110px;background:#fff}article>span{display:block;padding:10px 12px;color:#bac5d7}svg,video{width:100%;height:100%;object-fit:contain}
@media(max-width:650px){article{min-width:150px}}
</style></head><body><header><div>Signal animations <span> · Iconscout</span></div><button id="motion" type="button" aria-pressed="false">Pause animations</button></header><div class="gallery" tabindex="0" aria-label="Scrollable signal animations">''' + cards + '''</div><script>''' + runtime + '''</script><script>
const data=''' + payload + ''';
const reduced=matchMedia('(prefers-reduced-motion: reduce)');let paused=reduced.matches;
const players=data.map((d,i)=>{const container=document.getElementById('animation-'+i);if(d.media){const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.preload='metadata';v.src=d.media.src;container.append(v);return {play:()=>{v.play().catch(()=>{});},pause:()=>v.pause(),addEventListener:(e,fn)=>v.addEventListener('loadeddata',fn)};}return lottie.loadAnimation({container,renderer:'svg',loop:true,autoplay:false,animationData:d});});
const visible=new Set(); const button=document.getElementById('motion');
function sync(){players.forEach((p,i)=>{if(!paused&&!document.hidden&&visible.has(i))p.play();else p.pause();});button.textContent=paused?'Play animations':'Pause animations';button.setAttribute('aria-pressed',String(paused));}
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{const i=Number(e.target.id.split('-')[1]);if(e.isIntersecting)visible.add(i);else visible.delete(i);});sync();});
players.forEach((p,i)=>{observer.observe(document.getElementById('animation-'+i));p.addEventListener('DOMLoaded',sync);});
button.onclick=()=>{paused=!paused;sync();};document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',e=>{paused=e.matches;sync();});sync();
</script></body></html>'''
