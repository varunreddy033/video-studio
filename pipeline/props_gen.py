"""
props_gen.py  -  AI-made flat props and set plates for style: motion (docs/MOTION_PLAN.md, phase 5).

  [+ gen: a pair of white wired earphones]  ->  FLUX.2 klein (flat_vector art style, plain white background)
                                            ->  rembg u2net cut-out, trimmed  ->  assets/library/props/<slug>-<key>.png
  [scene: city_night]                       ->  a flat background plate (known set names, or | plate=<description>)
                                            ->  assets/library/plates/<slug>-<key>.png

Both caches are in git (assets/library), so every later video, and the other machine, reuses them: a prop or plate
is only ever generated once. Drafts and Check previews never generate (they use what's cached, else placeholders).
One image at a time, with the normal cool-down (visuals.shared_image).
"""

import json
import re
import time
from pathlib import Path

from PIL import Image

from . import config as C
from . import presets, visuals
from .util import h, log

PROPS_DIR = C.ASSETS / "library" / "props"
PLATES_DIR = C.ASSETS / "library" / "plates"
STYLE = "flat_vector"
VERSION = "v1"                      # bump to regenerate everything (changes every cache key)
PLATES = {                          # [scene: <name>] -> a plate, without writing a description
    "city_night": "a city skyline at night with lit windows and a dark blue sky",
    "city_day": "a modern city street with tall buildings under a clear sky",
    "ocean": "a calm ocean horizon with gentle waves and a wide sky",
    "stage": "an empty theatre stage with red curtains and one soft spotlight",
    "office": "a modern open-plan office interior with desks, plants and large windows",
    "street": "a quiet town street with small shops and trees",
    "trading_floor": "a stock trading floor with rows of desks and big wall screens showing abstract charts",
    "server_room": "a data center aisle with tall server racks and blue lights",
    "factory_floor": "a large factory floor with machines and conveyor belts",
    "bank_hall": "a grand bank hall with columns and a marble floor",
    "home": "a cosy living room with a sofa, a lamp and a window",
    "classroom": "a classroom with a blackboard, desks and big windows",
    "newsroom": "a news studio with a desk and large screens",
    "space": "outer space with planets and stars",
    "desert": "a wide desert with dunes under a clear sky",
    "port": "a cargo port with stacked shipping containers and cranes",
    "farm": "green farm fields with a red barn and hills",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "prop"


def _style():
    return presets.load("art_styles", STYLE)


def prop_prompt(text: str) -> str:
    st = _style()
    return f"{st['prefix']} of {text}, {st['prop_suffix']}, {st['suffix']}"


def plate_prompt(desc: str) -> str:
    st = _style()
    return f"{st['prefix']} of {desc}, {st['plate_suffix']}, {st['suffix']}"


def prop_path(text: str) -> Path:
    return PROPS_DIR / f"{_slug(text)}-{h(prop_prompt(text), VERSION)[:8]}.png"


def _plate_key(name: str, custom: str = ""):
    """`plate=home` (a known name) on any scene = that known plate, shared by every scene and video that uses it."""
    known = (custom or "").strip().lower().replace(" ", "_")
    return (known, "") if known in PLATES else (name, custom)


def plate_desc(name: str, custom: str = "") -> str:
    name, custom = _plate_key(name, custom)
    return custom or PLATES.get(name, "")


def plate_path(name: str, custom: str = "") -> Path:
    desc = plate_desc(name, custom)
    name, _ = _plate_key(name, custom)
    return PLATES_DIR / f"{_slug(name)}-{h(plate_prompt(desc), VERSION)[:8]}.png"


_rembg = None


def _cutout(src: Path, out: Path):
    """rembg (u2net, MIT/Apache-2.0) alpha, trimmed to the object plus a small margin."""
    global _rembg
    from rembg import new_session, remove
    if _rembg is None:
        _rembg = new_session("u2net")
    im = Image.open(src).convert("RGB")
    cut = remove(im, session=_rembg)
    a = cut.split()[-1]
    box = a.point(lambda v: 255 if v > 24 else 0).getbbox() or (0, 0, im.width, im.height)
    pad = int(0.04 * max(im.size))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
    out.parent.mkdir(parents=True, exist_ok=True)
    cut.crop(box).save(out)


def make_prop(text: str, log_dir: Path) -> Path:
    """The cut-out flat prop for '[+ gen: text]'; generated once, then always reused."""
    out = prop_path(text)
    if out.exists():
        return out
    t0 = time.time()
    raw = visuals.shared_image(prop_prompt(text), 1024, 1024, int(h(text)[:6], 16), log_dir)
    _cutout(raw, out)
    (out.with_suffix(".json")).write_text(json.dumps({"text": text, "prompt": prop_prompt(text), "style": STYLE,
                                                      "model": C.LOCAL_IMAGE_MODEL, "version": VERSION,
                                                      "made": time.strftime("%Y-%m-%d %H:%M")}, indent=1),
                                          encoding="utf-8")
    log(log_dir, f"  generated prop '{text}' -> {out.name} in {time.time() - t0:.0f}s (cached for later videos)")
    return out


def make_plate(name: str, custom: str, log_dir: Path):
    """The background plate for a scene, or None when the scene has no plate (code background)."""
    desc = plate_desc(name, custom)
    if not desc:
        return None
    out = plate_path(name, custom)
    if out.exists():
        return out
    t0 = time.time()
    raw = visuals.shared_image(plate_prompt(desc), 1280, 720, int(h(desc)[:6], 16), log_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.open(raw).convert("RGB").save(out, quality=92)
    (out.with_suffix(".json")).write_text(json.dumps({"scene": name, "description": desc, "prompt": plate_prompt(desc),
                                                      "style": STYLE, "model": C.LOCAL_IMAGE_MODEL, "version": VERSION,
                                                      "made": time.strftime("%Y-%m-%d %H:%M")}, indent=1),
                                          encoding="utf-8")
    log(log_dir, f"  generated plate '{name}' -> {out.name} in {time.time() - t0:.0f}s (cached for later videos)")
    return out


def wanted(parsed):
    """What a motion script asks for: ([gen texts], [(scene index, name, custom)])."""
    gens, plates = [], []
    for k, sh in enumerate(parsed["shots"]):
        for e in sh.get("events", []):
            if e.get("op") == "add" and e.get("kind") == "gen" and e["text"] not in gens:
                gens.append(e["text"])
        if sh["type"] == "scene":
            custom = (sh.get("opts") or {}).get("plate", "")
            if custom.lower() in ("no", "off", "none"):
                continue
            if plate_desc(sh.get("name", ""), custom):
                plates.append((k, sh.get("name", ""), custom))
    return gens, plates


def missing(parsed):
    """How many props/plates a final would have to generate (for Check's time estimate)."""
    gens, plates = wanted(parsed)
    return (sum(1 for g in gens if not prop_path(g).exists()),
            len({plate_path(n, c) for _, n, c in plates if not plate_path(n, c).exists()}))
