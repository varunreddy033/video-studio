"""The neon motion style (rendering_method: neon): what goes into its project. Voice, render, sound and encode are
pipeline/three_video.py (the shared engine; this style draws with the DOM + a canvas, no 3D models).

  project   output/jobs/<id>/neon/: index.html (stage + FX canvas + grain + HUD + caption bar, the scenes and the
            spoken words as JSON), assets/js/world.js, assets/fonts (Anton, Archivo Black, Inter, Space Mono, DM Serif)
  sound     whoosh on every cut, impact when a headline / number slams, pop for each node / card
"""

import html
import json
import sys
from pathlib import Path

from .. import config as C
from .. import three_video

NAME, LABEL = "neon", "neon motion"
JS_SRC = Path(__file__).parent / "js"
FONTS = ("Anton-Regular.ttf", "ArchivoBlack-Regular.ttf", "InterVariable.ttf", "SpaceMono-Bold.ttf",
         "DMSerifDisplay-Italic.ttf")
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "is", "it", "this", "that", "i", "you", "we", "my",
        "your", "with", "for", "at", "so", "but", "be", "was", "are"}


def ready():
    return ""


def caption_groups(words):
    """The top-left caption bar: 3-7 words per line (a clause), the longest content word in a lime box."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 7 or (len(cur) >= 3 and w[0][-1:] in ".,!?;:"):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        clean = [w[0].strip(".,!?;:\"'").lower() for w in g]
        cands = [k for k, c in enumerate(clean) if c not in STOP] or [len(g) - 1]
        key = max(cands, key=lambda k: len(clean[k]))
        out.append({"t0": round(g[0][1], 3),
                    "t1": round(min(groups[i + 1][0][1], g[-1][2] + 0.25) if i + 1 < len(groups) else g[-1][2] + 0.6, 3),
                    "html": " ".join(f"<b>{html.escape(w[0])}</b>" if k == key else html.escape(w[0])
                                     for k, w in enumerate(g))})
    return out


def _index_html(data, W, H, fps, total, title):
    names = {"Anton": FONTS[0], "Archivo": FONTS[1], "Inter": FONTS[2], "Mono": FONTS[3], "SerifI": FONTS[4]}
    faces = "\n".join(f'@font-face {{ font-family: "{n}"; src: url("assets/fonts/{f}"); }}' for n, f in names.items())
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
{faces}
html, body {{ margin: 0; background: #050505; }}
#stage {{ position: absolute; inset: 0; width: {W}px; height: {H}px; overflow: hidden; background: #050505; perspective: {int(max(W, H) * 1.2)}px; }}
#fx, #grain {{ position: absolute; inset: 0; width: {W}px; height: {H}px; pointer-events: none; }}
#grain {{ opacity: .09; mix-blend-mode: screen; }}
.sc {{ position: absolute; inset: 0; display: none; }}
.cam {{ position: absolute; inset: 0; transform-style: preserve-3d; }}
.hud {{ position: absolute; font: 700 {max(10, W // 110)}px "Mono"; color: #F4F4F0; opacity: .45; letter-spacing: .12em; }}
#cap {{ position: absolute; left: {int(W * .045)}px; top: {int(H * .05)}px; max-width: {int(W * .7)}px;
  font: 700 {max(16, int(min(W, H) * .028))}px "Inter"; color: #F4F4F0; line-height: 1.35; }}
#cap b {{ background: #D4FF2A; color: #050505; padding: 0 .25em; font-weight: 800; }}
</style>
<script src="assets/js/gsap.min.js"></script>
<script>window.__NEON = {json.dumps(data)};</script>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{fps}">
  <div id="stage"></div>
  <canvas id="fx" width="{W}" height="{H}"></canvas>
  <canvas id="grain" width="{W // 4}" height="{H // 4}"></canvas>
  <div class="hud" id="hudTL" style="left:{int(W*.045)}px;bottom:{int(H*.04)}px">● REC</div>
  <div class="hud" id="hudTR" style="right:{int(W*.045)}px;top:{int(H*.05)}px">00:00:00</div>
  <div class="hud" id="hudBR" style="right:{int(W*.045)}px;bottom:{int(H*.04)}px">SCENE 01</div>
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
    shots = []
    for i, (sh, (st, d)) in enumerate(zip(parsed["shots"], spans)):
        ws = [[w[0], w[1]] for w in words if st - 0.05 <= w[1] < st + d]          # the words spoken in this scene
        shots.append({"start": round(st, 3), "end": round(st + d, 3), "type": sh["type"], "kind": sh["kind"],
                      "text": sh["text"], "extra": sh.get("extra", ""), "lines": sh.get("lines"),
                      "items": sh.get("items"), "words": ws})
    page_caps = not meta.get("captions")
    data = {"W": W, "H": H, "shots": shots, "caps": caption_groups(words) if page_caps else []}
    total = max(s["end"] for s in shots)
    kinds = [s["kind"] for s in shots]
    line = f"{len(shots)} scenes ({', '.join(f'{k} {kinds.count(k)}' for k in sorted(set(kinds)))}), " \
           f"captions {'in the picture' if page_caps else meta['presets']['captions']}"
    return data, _index_html(data, W, H, C.FPS, total, meta.get("title", "")), shots, {"scenes": len(shots)}, line


def cues(shots):
    out = [(s["start"] + 0.02, "whoosh") for s in shots[1:]]
    for s in shots:
        ws = s["words"]
        if s["kind"] in ("headline", "number", "logo") and ws:
            out.append((ws[min(len(ws) - 1, 1)][1], "impact"))
        if s["kind"] in ("nodes", "stack"):
            n = len(s["items"])
            out += [(s["start"] + 0.25 + k * max(0.25, (s["end"] - s["start"] - 0.6) / n), "pop") for k in range(n)]
    return out


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    return three_video.render(sys.modules[__name__], parsed, job_dir, mode, progress)
