"""The blocky 3D style (rendering_method: blocky3d, docs/BLOCKY3D_PLAN.md): what goes into its project. The voice,
render, sound and encode steps are pipeline/three_video.py (shared with explainer3d).

  project   output/jobs/<id>/blocky3d/: index.html (canvas + caption + sign layers, the shots as JSON),
            assets/js/world.js, assets/fonts, models/ (only the Kenney / studio files this video uses)
  sound     whooshes on cuts, pops on signs, story sounds per action; music from assets/blocky3d/music first
"""

import html
import json
from pathlib import Path

from .. import presets
from .. import three_video
from . import sets as SETS

NAME, LABEL = "blocky3d", "blocky 3D"
JS_SRC = Path(__file__).parent / "js"
FONTS = ("Barlow-Black.ttf", "PatrickHand-Regular.ttf", "CormorantSC-SemiBold.ttf", "SpaceMono-Bold.ttf")
LASHES = {"princess_costume", "pink_hair_friend"}                # studio characters that use the _lashes faces
STOP = {"in", "this", "if", "you", "has", "to", "on", "my", "i", "then", "they", "all", "so", "after", "me", "the",
        "way", "a", "an", "of", "and", "first", "it", "was", "is", "at", "he", "she", "we", "her", "his", "that"}
# story sounds: the shot's action -> a library sound kind, a little after the cut (motion_gfx FALLBACK maps missing kinds)
ACTION_SFX = {"fall": ("impact", 0.45), "freeze": ("crowd-gasp", 0.15), "cheer": ("crowd-cheer", 0.2),
              "jump": ("boing", 0.3), "scared": ("riser", 0.0)}


def caption_groups(words):
    """2-4 words per caption; the longest content word = the key word (caps + green), which starts line two."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[0][-1:] in ".,!?" or (len(cur) >= 2 and len(cur[-1][0]) > 7):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    caps = []
    for g, grp in enumerate(groups):
        clean = [w[0].strip(".,!?\"'").lower() for w in grp]
        cands = [k for k, c in enumerate(clean) if c not in STOP] or [len(grp) - 1]
        key = max(cands, key=lambda k: len(clean[k]))

        def line(ws):
            return " ".join(f"<b>{html.escape(w[0].strip('.,').upper())}</b>" if w is grp[key]
                            else html.escape(w[0].strip(".,")) for w in ws)
        # clear 0.08 s after the group's last word (never over the next shot), or when the next group starts
        t1 = min(groups[g + 1][0][1], grp[-1][2] + 0.08) if g + 1 < len(groups) else grp[-1][2] + 0.5
        caps.append({"t0": round(grp[0][1], 3), "t1": round(t1, 3),
                     "html": (f"<div>{line(grp[:key])}</div>" if key else "") + f"<div>{line(grp[key:])}</div>"})
    return caps


def _index_html(data, W, H, fps, total, title):
    faces = "\n".join(f'@font-face {{ font-family: "{f.split(".")[0]}"; src: url("assets/fonts/{f}"); }}' for f in FONTS)
    cs = int(H * (0.034 if H > W else 0.05))
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
{faces}
html, body {{ margin: 0; background: #000; }}
#world {{ position: absolute; inset: 0; width: {W}px; height: {H}px; }}
#cap {{ position: absolute; left: 50%; top: {int(H * (0.17 if H > W else 0.08))}px; width: {int(W * 0.86)}px; text-align: center;
  transform-origin: 50% 50%; font-family: "Barlow-Black"; font-size: {cs}px; line-height: 1.12; color: #fff;
  -webkit-text-stroke: {max(4, cs // 7)}px #111; paint-order: stroke fill; text-shadow: 0 {max(2, cs // 11)}px 0 rgba(0,0,0,.35); }}
#cap b {{ color: #3df06e; font-size: 1.12em; }}
.sign {{ position: absolute; left: 50%; top: 52%; width: {int(W * 0.72)}px; min-height: {int(W * 0.34)}px; box-sizing: border-box;
  display: flex; align-items: center; justify-content: center; text-align: center; padding: {int(W * 0.06)}px;
  font-size: {int(W * 0.058)}px; line-height: 1.25; box-shadow: 0 {int(W * 0.02)}px {int(W * 0.06)}px rgba(0,0,0,.45); opacity: 0; }}
.sign.off {{ display: none; }}
.sign.note {{ background: #fffdf3 repeating-linear-gradient(#fffdf3 0 {int(W * 0.07) - 3}px, #b9d3f0 {int(W * 0.07) - 3}px {int(W * 0.07)}px);
  color: #2a3f8f; font-family: "PatrickHand-Regular"; font-size: {int(W * 0.068)}px; }}
.sign.tablet {{ background: linear-gradient(#cdbf9f, #b5a37d); color: #4a3a22; font-family: "CormorantSC-SemiBold"; border: {int(W * 0.018)}px solid #8f7d58;
  border-radius: {int(W * 0.05)}px {int(W * 0.05)}px {int(W * 0.012)}px {int(W * 0.012)}px; }}
.sign.board {{ background: #2f5d3a; color: #f4f4ec; font-family: "PatrickHand-Regular"; border: {int(W * 0.022)}px solid #8a5a33; font-size: {int(W * 0.066)}px; }}
.sign.scoreboard {{ background: #0d0f14; color: #ff5a3c; font-family: "SpaceMono-Bold"; border: {int(W * 0.014)}px solid #3a3f4a; letter-spacing: .04em;
  text-shadow: 0 0 {int(W * 0.02)}px #ff5a3c; }}
.sign.phone {{ width: {int(W * 0.56)}px; min-height: {int(W * 0.9)}px; background: #111; border-radius: {int(W * 0.07)}px; border: {int(W * 0.02)}px solid #2b2b2b;
  align-items: flex-end; padding: {int(W * 0.05)}px {int(W * 0.04)}px {int(W * 0.12)}px; }}
.sign.phone span {{ background: #2f80ed; color: #fff; font-family: "Barlow-Black"; border-radius: {int(W * 0.04)}px; padding: {int(W * 0.03)}px {int(W * 0.04)}px;
  font-size: {int(W * 0.048)}px; text-align: left; }}
#dim {{ position: absolute; inset: 0; background: rgba(0,0,0,.28); }}
</style>
<script type="importmap">{{"imports": {{"three": "./assets/js/three.module.js"}}}}</script>
<script src="assets/js/gsap.min.js"></script>
<script>window.__BLOCKY = {json.dumps(data)};</script>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{fps}">
  <canvas id="world" width="{W}" height="{H}"></canvas>
  <div id="sign" class="sign off"><span id="signText"></span></div>
  <div id="cap"></div>
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
<script type="module" src="assets/js/world.js"></script>
</body></html>
"""


def ready():
    return "" if SETS.ready() else ("the blocky 3D model packs aren't downloaded. Run once in Terminal: "
                                    "bin/python tools/fetch_blocky3d_assets.py")


def build(meta, parsed, spans, words, W, H, project, warnings):
    cast = {}
    for name, c in meta["cast"].items():
        if c.get("model"):                         # a studio character (GLB); a crowd of them = seeded random colours
            cast[name] = {"model": c["model"], "count": c["count"], "random": c["count"] > 1, "skin": "#f2d0a7",
                          "lashes": "girl" in c["id"] or c["id"] in LASHES}
            continue
        p = presets.load("blocky_cast", c["preset"])
        cast[name] = {k: p.get(k) for k in ("skin", "hair", "hair_colour", "shirt", "shirt_colour", "shirt_colour2",
                                            "pants_colour", "random")} | {"count": c["count"]}
    shots = []
    for i, (sh, (st, d)) in enumerate(zip(parsed["shots"], spans)):
        shots.append({"start": round(st, 3), "end": round(st + d, 3), "type": sh["type"], "who": sh.get("who", []),
                      "action": sh.get("action", "idle"), "camera": sh.get("camera", "auto"),
                      "set": sh.get("set") or meta["set"], "face": sh.get("face", ""), "sign": sh.get("sign", ""),
                      "text": sh.get("text", ""), "seed": i * 0.37, "prop": sh.get("prop", "")})
    used_sets = sorted({s["set"] for s in shots})
    layouts = {name: SETS.layout(name) for name in used_sets}
    for name, lay in layouts.items():
        if lay["missing"]:
            warnings.append(f"set {name}: {len(lay['missing'])} model(s) missing from assets/blocky3d: "
                            f"{', '.join(lay['missing'][:4])}")
    page_caps = not meta.get("captions")
    studio_props = SETS.studio("props")
    props = {s["prop"]: studio_props[s["prop"]] for s in shots if s.get("prop")}
    faces = sorted({f.name[5:-4] for f in (SETS.BASE / "studio/textures/faces").glob("face_*.png")}) \
        if any(c.get("model") for c in cast.values()) else []
    data = {"W": W, "H": H, "grade": meta["grade"], "cast": cast, "shots": shots, "sets": layouts, "props": props,
            "studio_faces": faces,
            "caps": caption_groups(words) if page_caps else [], "speech": [[w[1], w[2]] for w in words]}
    files = [p["file"] for lay in layouts.values() for p in lay["props"]]
    files += [c["model"] for c in cast.values() if c.get("model")] + list(props.values())
    files += [f"studio/textures/faces/face_{f}.png" for f in faces]
    n = three_video.copy_files(SETS.BASE, files, project / "models")
    total = max(s["end"] for s in shots)
    line = (f"{len(shots)} shots, sets {', '.join(used_sets)}, {n} model files, grade {meta['grade']}, "
            f"captions {'in the picture' if page_caps else meta['presets']['captions']}")
    summary = {"shots": len(shots), "sets": used_sets, "models": n, "grade": meta["grade"]}
    return data, _index_html(data, W, H, three_video.C.FPS, total, meta.get("title", "")), shots, summary, line


def cues(shots):
    out = [(s["start"] + 0.03, "whoosh") for s in shots[1:]]
    out += [(s["start"] + 0.05, "pop") for s in shots if s["type"] == "sign"]
    out += [(s["start"] + ACTION_SFX[s["action"]][1], ACTION_SFX[s["action"]][0])
            for s in shots if s["type"] == "shot" and s["action"] in ACTION_SFX]
    return out


def render(parsed: dict, job_dir: Path, mode: str, progress) -> dict:
    import sys
    return three_video.render(sys.modules[__name__], parsed, job_dir, mode, progress)
