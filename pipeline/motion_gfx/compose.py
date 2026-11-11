"""The HyperFrames project of one motion job (output/jobs/<id>/motion/):

  index.html                  root: one host per beat-scene, the caption chip host on top, the voice as <audio>
  compositions/scene_NNN.html one beat each (<template>: style, markup, script)
  compositions/captions.html  the caption chip: 2-4 word groups, top-left pill, the spoken word on a yellow marker
  assets/js/gsap.min.js       GSAP from node_modules (no CDN)
  assets/fonts/               the bundled fonts (no Google Fonts)

Transitions (beat-sync-editing): a hard cut inside a thought, a push between beats of one shot, zoom-through or
whip-pan on a new shot, a circle wipe on a new chapter. The incoming scene overlaps the outgoing one by
design.TRANSITION seconds; the cut point (where its narration starts) doesn't move."""

import html as _html
import shutil
from pathlib import Path

from .. import config as C
from . import design as D
from . import hf


def host(i):
    return f"s{i + 1:03d}"


def transition_for(beats, i):
    b = beats[i]
    if i == 0:
        return "cut"
    if b.get("chapter"):
        return "wipe"
    if b["index"] == 0:
        return ["zoom", "whip", "push"][b["shot"] % 3]
    return "cut" if b["index"] % 2 else "push"


def _transition_js(kind, ov, W, H):
    if ov <= 0 or kind == "cut":
        return ""
    d = f'duration: {ov:.2f}, ease: "power3.out"'
    if kind == "glitch":              # three quick offset jumps with a colour shift, then settle
        return (f'scene.fromTo("#__H__-stage", {{x: {int(W * 0.04)}, filter: "hue-rotate(90deg) saturate(2)"}}, '
                f'{{x: 0, filter: "hue-rotate(0deg) saturate(1)", duration: {ov:.2f}, ease: "steps(4)"}}, 0);')
    if kind == "flash":               # a white flash: the scene starts burnt out and comes down to normal
        return (f'scene.fromTo("#__H__-stage", {{filter: "brightness(3)"}}, {{filter: "brightness(1)", {d}}}, 0);')
    start, end = {
        "push": (f"{{x: {W}}}", f"{{x: 0, {d}}}"),
        "slide": (f"{{x: {-W}}}", f"{{x: 0, {d}}}"),
        "push_up": (f"{{y: {H}}}", f"{{y: 0, {d}}}"),
        "fade": ("{opacity: 0}", f"{{opacity: 1, {d}}}"),
        "zoom": ("{scale: 1.6, opacity: 0}", f"{{scale: 1, opacity: 1, {d}}}"),
        "zoom_out": ("{scale: 0.55, opacity: 0}", f"{{scale: 1, opacity: 1, {d}}}"),
        "whip": (f'{{x: {-int(W * 0.35)}, filter: "blur(24px)"}}', f'{{x: 0, filter: "blur(0px)", {d}}}'),
        "wipe": ('{clipPath: "circle(0% at 50% 55%)"}', f'{{clipPath: "circle(150% at 50% 55%)", {d}}}'),
        "blinds": ('{clipPath: "inset(0% 0% 100% 0%)"}', f'{{clipPath: "inset(0% 0% 0% 0%)", {d}}}'),
        "split": ('{clipPath: "polygon(50% 0%, 50% 0%, 50% 100%, 50% 100%)"}',
                  f'{{clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)", {d}}}'),
    }[kind]
    return f'scene.fromTo("#__H__-stage", {start}, {end}, 0);'


def prepare(project: Path, voice_wav: Path):
    for sub in ("compositions", "assets/js", "assets/fonts", "assets/audio", "snapshots", "logs"):
        (project / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(hf.GSAP_JS, project / "assets/js/gsap.min.js")
    for fam, f, w in D.FONTS.values():
        shutil.copy(C.FONTS_DIR / f, project / "assets/fonts" / f)
    shutil.copy(voice_wav, project / "assets/audio/voice.wav")


FRAMES = ["card", "tilt", "band", "spot"]          # the framed layouts (layout 3-5 of a type = layout 0-2 + its frame)
ENTRANCES = ["pop", "rise", "drop", "mask", "flip", "skew", "none"]


def frame_html(kind, hid, pal, W, H):
    """Code-drawn backdrop of a framed layout, behind the scene's own content."""
    if kind == "card":
        return (f'<div style="position:absolute;left:{int(W * .05)}px;right:{int(W * .05)}px;top:{int(H * .15)}px;'
                f'bottom:{int(H * .06)}px;background:{pal["soft"]};border:{max(4, W // 320)}px solid {pal["ink"]};'
                f'border-radius:{W // 60}px;box-shadow:{W // 150}px {W // 150}px 0 {pal["ink"]}"></div>')
    if kind == "tilt":
        return (f'<div style="position:absolute;left:-10%;width:120%;top:{int(H * .30)}px;height:{int(H * .42)}px;'
                f'background:{pal["soft"]};transform:rotate(-4deg)"></div>')
    if kind == "band":
        return (f'<div style="position:absolute;left:0;top:0;bottom:0;width:{int(W * .045)}px;background:{pal["pop"]}"></div>'
                f'<div style="position:absolute;left:{int(W * .055)}px;top:0;bottom:0;width:{max(3, W // 640)}px;'
                f'background:{pal["ink"]};opacity:.5"></div>'
                + "".join(f'<div style="position:absolute;right:{int(W * (.04 + .03 * k))}px;top:{int(H * .07)}px;'
                          f'width:{int(W * .018)}px;height:{int(W * .018)}px;border-right:{max(4, W // 400)}px solid '
                          f'{pal["ink"]};border-top:{max(4, W // 400)}px solid {pal["ink"]};transform:rotate(45deg);'
                          f'opacity:{.8 - .25 * k}"></div>' for k in range(3)))
    if kind == "spot":
        r = int(H * .46)
        return (f'<div style="position:absolute;left:{W // 2 - r}px;top:{int(H * .58) - r}px;width:{2 * r}px;'
                f'height:{2 * r}px;border-radius:50%;background:{pal["soft"]}"></div>')
    return ""


def _entrance_js(kind, hid, ov, W, H):
    sel, at = f"#{hid}-ent", f"{ov:.2f}"
    return {"pop": f'scene.fromTo("{sel}", {{scale: 0.88, opacity: 0.4}}, {{scale: 1, opacity: 1, duration: 0.45, ease: "back.out(2)"}}, {at});',
            "rise": f'scene.fromTo("{sel}", {{y: {int(H * .06)}}}, {{y: 0, duration: 0.45, ease: "expo.out"}}, {at});',
            "drop": f'scene.fromTo("{sel}", {{y: {-int(H * .06)}}}, {{y: 0, duration: 0.45, ease: "bounce.out"}}, {at});',
            "mask": f'scene.fromTo("{sel}", {{clipPath: "inset(0% 100% 0% 0%)"}}, {{clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power3.inOut"}}, {at});',
            "flip": f'scene.fromTo("{sel}", {{rotationX: 55, transformPerspective: 1200, transformOrigin: "50% 100%"}}, {{rotationX: 0, duration: 0.55, ease: "back.out(1.4)"}}, {at});',
            "skew": f'scene.fromTo("{sel}", {{skewX: 12, x: {-int(W * .03)}}}, {{skewX: 0, x: 0, duration: 0.45, ease: "expo.out"}}, {at});',
            }.get(kind, "")


def scene_file(i, beat, parts, pal, ov, W, H):
    hid = host(i)
    length = beat["dur"] + ov
    tr = _transition_js(beat["transition"], ov, W, H).replace("__H__", hid)
    frame = frame_html(beat.get("frame"), hid, pal, W, H)
    ent = _entrance_js(beat.get("entrance"), hid, ov, W, H)
    tilt = "transform:rotate(-1.5deg) scale(0.96);" if beat.get("frame") == "tilt" else ""
    return f"""<template>
<style>
#root {{ position: absolute; inset: 0; overflow: hidden; }}
#{hid}-stage {{ position: absolute; inset: 0; background: {pal['bg']}; overflow: hidden; }}
#{hid}-cam {{ position: absolute; inset: 0; }}
#{hid}-ent {{ position: absolute; inset: 0; {tilt} }}
{parts['css']}
</style>
<div id="root" data-composition-id="{hid}" data-width="{W}" data-height="{H}">
  <div id="{hid}-stage"><div id="{hid}-cam">{frame}<div id="{hid}-ent">
{parts['html']}
  </div></div></div>
</div>
<script>
const scene = gsap.timeline({{ paused: true }});
{tr}
{ent}
scene.fromTo("#{hid}-cam", {{scale: 1, x: 0}}, {{scale: {1.09 if beat.get("breather") else 1.035}, x: {-int(W * 0.02) if beat.get("breather") else 0}, transformOrigin: "50% 50%", duration: {length:.2f}, ease: "{"sine.inOut" if beat.get("breather") else "none"}"}}, 0);
const tl = gsap.timeline();
(function (tl) {{
{parts['js']}
}})(tl);
scene.add(tl, {ov:.2f});
window.__timelines["{hid}"] = scene;
</script>
</template>
"""


def caption_groups(words, max_words=4, max_gap=0.35):
    """[[ [word, t0, t1], ... ]] groups of 2-4 words (hyperframes captions.md: 2-3 high energy, 3-5 conversational),
    broken at a sentence end, a pause or the word limit."""
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w[1] - cur[-1][2] > max_gap or cur[-1][0][-1:] in ".?!:;,"):
            out.append(cur)
            cur = []
        cur.append(w)
    return out + ([cur] if cur else [])


def captions_file(words, total, W, H, fmt):
    """The caption chip composition (one host, data-track-kind=captions)."""
    cx, cy = D.SAFE[fmt]["chip"]
    size = int(H * (0.046 if fmt == "landscape" else 0.03))
    groups = caption_groups(words)
    html, js = [], []
    for g, grp in enumerate(groups):
        spans = "".join(f'<span id="c{g}w{k}" class="cw">{_html.escape(w[0])}</span>' for k, w in enumerate(grp))
        html.append(f'<div id="c{g}" class="cg">{spans}</div>')
        start = max(0.1, grp[0][1] - 0.05)
        end = min(total, (groups[g + 1][0][1] - 0.02) if g + 1 < len(groups) else grp[-1][2] + 0.4)
        end = max(end, start + 0.2)
        js.append(f'tl.fromTo("#c{g}", {{opacity: 0, scale: 0.8, x: -14}}, {{opacity: 1, scale: 1, x: 0, duration: 0.14, '
                  f'ease: "back.out(2)"}}, {start:.3f});')
        js.append(f'tl.set("#c{g}", {{opacity: 0, visibility: "hidden"}}, {end:.3f});')
        for k, w in enumerate(grp):
            js.append(f'tl.set("#c{g}w{k}", {{backgroundColor: "#FFD21F"}}, {max(start, w[1] - 0.02):.3f});')
            nxt = grp[k + 1][1] - 0.02 if k + 1 < len(grp) else end
            if nxt < end - 0.01:
                js.append(f'tl.set("#c{g}w{k}", {{backgroundColor: "rgba(255,210,31,0)"}}, {nxt:.3f});')
    return f"""<template>
<style>
#root {{ position: absolute; inset: 0; pointer-events: none; }}
.cg {{ position: absolute; left: {int(W * cx)}px; top: {int(H * cy)}px; opacity: 0; transform-origin: 0% 50%;
  background: #FFFFFF; border: 5px solid #111111; border-radius: {int(size * 0.5)}px; padding: {int(size * 0.18)}px {int(size * 0.32)}px;
  box-shadow: 0 {int(size * 0.14)}px 0 #111111; font-family: "Barlow Black"; font-size: {size}px; line-height: 1.15;
  color: #111111; white-space: nowrap; max-width: {int(W * 0.5)}px; }}
.cw {{ display: inline-block; padding: 0 0.12em; margin: 0 0.02em; border-radius: 0.14em; background: rgba(255,210,31,0); }}
</style>
<div id="root" data-composition-id="caps" data-width="{W}" data-height="{H}" data-layout-allow-overlap>
{chr(10).join(html)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["caps"] = tl;
</script>
</template>
"""


def index_file(beats, total, W, H, fps, title, with_captions):
    faces = "\n".join(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; src: url("assets/fonts/{f}"); }}'
                      for fam, f, w in D.FONTS.values())
    hosts = []
    for i, b in enumerate(beats):
        start = max(0.0, b["start"] - b["ov"])
        end = total if i == len(beats) - 1 else b["end"]
        hid = host(i)
        hosts.append(f'  <div id="{hid}" data-composition-id="{hid}" data-composition-src="compositions/scene_{i + 1:03d}.html" '
                     f'data-start="{start:.3f}" data-duration="{end - start:.3f}" data-track-index="1" '
                     f'data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index: {i + 1}"></div>')
    if with_captions:
        hosts.append(f'  <div id="caps" data-composition-id="caps" data-composition-src="compositions/captions.html" '
                     f'data-start="0" data-duration="{total:.3f}" data-track-index="2" data-track-kind="captions" '
                     f'data-width="{W}" data-height="{H}" style="z-index: 100000"></div>')
    hosts.append(f'  <audio id="voice" class="clip" src="assets/audio/voice.wav" data-start="0" data-duration="{total:.3f}" '
                 f'data-track-index="3" data-volume="1"></audio>')
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{_html.escape(title)}</title>
<style>
{faces}
html, body {{ margin: 0; background: #111111; }}
</style>
<script src="assets/js/gsap.min.js"></script>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}" data-fps="{fps}">
{chr(10).join(hosts)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
"""
