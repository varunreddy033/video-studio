"""The 3D explainer style (rendering_method: explainer3d): what goes into its project. Voice, render, sound and encode
are pipeline/three_video.py (shared with blocky3d).

  project   output/jobs/<id>/explainer3d/: index.html (3D canvas + 2D overlay canvas + caption layer, the scenes as
            JSON), assets/js/world.js, assets/fonts, models/ (only the explainer / blocky3d models this video uses)
  sound     whoosh on every cut, pop when a title / count / meter lands
"""

import html
import json
import sys
from pathlib import Path

from .. import config as C
from .. import three_video
from . import script as E

NAME, LABEL = "explainer3d", "3D explainer"
JS_SRC = Path(__file__).parent / "js"
FONTS = ("ArchivoBlack-Regular.ttf", "Barlow-Black.ttf")


def ready():
    return "" if E.MODELS_DIR.is_dir() else "assets/explainer3d/models is missing (it is in git: git checkout it)"


def caption_groups(words):
    """1-3 words per caption (the reference look), broken at punctuation; cleared just after the last word."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 3 or w[0][-1:] in ".,!?;:":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return [{"t0": round(g[0][1], 3),
             "t1": round(min(groups[i + 1][0][1], g[-1][2] + 0.08) if i + 1 < len(groups) else g[-1][2] + 0.5, 3),
             "text": " ".join(w[0] for w in g)} for i, g in enumerate(groups)]


def _index_html(data, W, H, fps, total, title):
    cs = int(H * (0.033 if H > W else 0.05))
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
@font-face {{ font-family: "Title"; src: url("assets/fonts/ArchivoBlack-Regular.ttf"); }}
@font-face {{ font-family: "Body"; src: url("assets/fonts/Barlow-Black.ttf"); }}
html, body {{ margin: 0; background: #000; }}
#world, #ov {{ position: absolute; inset: 0; width: {W}px; height: {H}px; }}
#cap {{ position: absolute; left: 50%; top: {int(H * 0.62)}px; width: {int(W * 0.9)}px; text-align: center;
  font-family: "Body"; font-size: {cs}px; line-height: 1.1; color: #fff; transform-origin: 50% 50%;
  text-shadow: 0 {max(2, cs // 12)}px {max(4, cs // 5)}px rgba(0,0,0,.55), 0 0 {max(2, cs // 10)}px rgba(0,0,0,.6); }}
</style>
<script type="importmap">{{"imports": {{"three": "./assets/js/three.module.js"}}}}</script>
<script src="assets/js/gsap.min.js"></script>
<script>window.__EXPLAINER = {json.dumps(data)};</script>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{fps}">
  <canvas id="world" width="{W}" height="{H}"></canvas>
  <canvas id="ov" width="{W}" height="{H}"></canvas>
  <div id="cap"></div>
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
<script type="module" src="assets/js/world.js"></script>
</body></html>
"""


def build(meta, parsed, spans, words, W, H, project, warnings):
    known = E.models()
    shots = []
    for i, (sh, (st, d)) in enumerate(zip(parsed["shots"], spans)):
        shots.append({"start": round(st, 3), "end": round(st + d, 3), "type": sh["type"], "subject": sh["subject"],
                      "camera": sh["camera"], "bg": sh["bg"], "title": sh.get("title"), "meter": sh.get("meter"),
                      "chart": sh.get("chart"), "count": sh.get("count")})
    ids = {s["subject"]["model"] for s in shots if s["subject"].get("model")}
    if any(s["subject"]["kind"] == "food" for s in shots):
        ids |= {"apple", "bread_loaf", "fish", "rice_bowl"}
    rel = {i: known[i] for i in sorted(ids)}
    n = three_video.copy_files(C.BASE_DIR, rel.values(), project / "models")
    page_caps = not meta.get("captions")
    data = {"W": W, "H": H, "shots": shots, "models": {i: "models/" + r for i, r in rel.items()},
            "caps": caption_groups(words) if page_caps else []}
    total = max(s["end"] for s in shots)
    line = f"{len(shots)} scenes, {len(rel)} models ({n} files), captions {'in the picture' if page_caps else meta['presets']['captions']}"
    summary = {"scenes": len(shots), "models": sorted(rel)}
    return data, _index_html(data, W, H, C.FPS, total, meta.get("title", "")), shots, summary, line


def cues(shots):
    out = [(s["start"] + 0.03, "whoosh") for s in shots[1:]]
    out += [(s["start"] + 0.12, "pop") for s in shots if s.get("title") or s.get("count")]
    out += [(s["start"] + 0.3, "ding") for s in shots if s.get("meter")]
    return out


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    return three_video.render(sys.modules[__name__], parsed, job_dir, mode, progress)
