"""Freshness across videos for motion graphics (docs/ASSET_PACKS_PLAN.md sections 3.6 and 4).

data/asset_history.json (private, not in git) gets one entry per finished FINAL video: the look it used (icon family,
palette set, font pairing, icon style) and the icons, templates, palettes, fonts, music and sound effects in it.

  choose_look(meta, title)   one look per video. A video that is already in the history keeps its look (same script =
                             same video). A new one takes, per part, the option the last 5 videos used least (ties by a
                             hash of the title). Header lines win: icons:, palette:, fonts:, icon_style:, look: classic.
  recent(title)              what the 5 videos BEFORE this one used (its own entry and later ones never count, so a
                             re-render picks the same icons as the first render).
  record(title, job, data)   writes / replaces this video's entry (keeps its place in the order).
"""

import hashlib
import json
import time

from .. import config as C
from .. import icon_library as L
from . import design as D

PATH = C.BASE_DIR / "data" / "asset_history.json"
RECENT = 5
CLASSIC = {"icons": "fluent_flat", "palette": "pop", "fonts": "poster", "icon_style": "sticker"}


def key_of(title: str) -> str:
    return hashlib.sha1((title or "").strip().lower().encode("utf-8")).hexdigest()[:16]


def load() -> list:
    try:
        return json.loads(PATH.read_text(encoding="utf-8")).get("videos", [])
    except (OSError, ValueError):
        return []


def _before(title: str) -> list:
    videos, key = load(), key_of(title)
    for i, v in enumerate(videos):
        if v.get("key") == key:
            return videos[:i]
    return videos


def entry(title: str):
    key = key_of(title)
    return next((v for v in load() if v.get("key") == key), None)


def recent(title: str) -> dict:
    """{"icons": {id: n}, "templates": {...}, "music": {...}, "sfx": {...}, "looks": [...]} of the last 5 videos."""
    out = {"icons": {}, "templates": {}, "music": {}, "sfx": {}, "looks": []}
    for v in _before(title)[-RECENT:]:
        out["looks"].append(v.get("look") or {})
        for k in ("icons", "templates", "music", "sfx"):
            for x in v.get(k) or []:
                out[k][x] = out[k].get(x, 0) + 1
    return out


def options() -> dict:
    return {"icons": L.usable_families() or ["fluent_flat"], "palette": list(D.PALETTE_SETS),
            "fonts": list(D.FONT_PAIRS), "icon_style": ["sticker", "plain"]}


def choose_look(meta: dict, title: str) -> dict:
    pins = {"icons": (meta.get("icons") or "").strip().lower(), "palette": (meta.get("palette") or "").strip().lower(),
            "fonts": (meta.get("fonts") or "").strip().lower(),
            "icon_style": (meta.get("icon_style") or "").strip().lower()}
    mode = (meta.get("look") or "auto").strip().lower()
    opts = options()
    if mode == "classic":
        base = dict(CLASSIC)
    else:
        old = entry(title)
        base = dict((old or {}).get("look") or {})
        looks = recent(title)["looks"]
        h = int(hashlib.sha1(title.encode("utf-8")).hexdigest()[:8], 16)
        for part in ("icons", "palette", "fonts"):
            if base.get(part) in opts[part]:
                continue
            used = [lk.get(part) for lk in looks]
            n = len(opts[part])
            order = [opts[part][(h + k) % n] for k in range(n)]
            base[part] = min(order, key=lambda o: (used.count(o), order.index(o)))
        base.setdefault("icon_style", "sticker")
    for part, v in pins.items():
        if v:
            base[part] = v
    for part in ("icons", "palette", "fonts", "icon_style"):
        if base.get(part) not in opts[part]:
            base[part] = CLASSIC[part] if CLASSIC[part] in opts[part] else opts[part][0]
    return base


def record(title: str, job: str, data: dict) -> None:
    videos, key = load(), key_of(title)
    row = dict(data, key=key, title=title, job=job, date=time.strftime("%Y-%m-%d %H:%M"))
    for i, v in enumerate(videos):
        if v.get("key") == key:
            videos[i] = row
            break
    else:
        videos.append(row)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"videos": videos}, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PATH)
